import BeautifulSoup
import logging
import mechanize
import re


logger = logging.getLogger(__name__)


class InterfaceError(Exception):
	"""
	An exceptional turn of events when talking to Quest.
	"""


class LoginError(Exception):
	"""
	Failure to log in.
	"""


class AuthenticationError(Exception):
	"""
	An attempt to do something without being logged in.
	"""


class QuestScraper(object):
	"""
	A scraper for Quest.

	All methods raise InterfaceError if they encounter something unexpected.
	"""

	base_url = 'https://quest.pecs.uwaterloo.ca/psc/SS/ACADEMIC/SA/'

	def __init__(self, auto_authenticate=False):
		# Do we automatically attempt to log in if we're logged out?
		self.auto_authenticate = auto_authenticate
		# Credentials are set by a call to login.
		self.username = None
		self.password = None

		self.br = mechanize.Browser()

	def is_logged_in(self):
		"""
		Determine whether currently in a valid session.
		"""

		# Grab the universal header.
		self.br.open(self.base_url + 's/WEBLIB_PT_NAV.ISCRIPT1.FieldFormula.'
				'IScript_UniHeader_Frame')

		resp = self.br.response().read()
		soup = BeautifulSoup.BeautifulSoup(resp)

		# If the header loads and has a link to log out, we're probably logged
		# in.
		return bool(soup.find(attrs={'class': 'headerLinkActive'},
				text=re.compile('Sign out')))

	def login(self, username, password):
		"""
		Attempt to create a new session for the given username.

		Raises LoginError if Quest refuses the credentials.
		"""

		if self.auto_authenticate:
			self.username = username
			self.password = password

		logger.debug('Logging in as "%s".', username)

		self.br.open(self.base_url + '?cmd=login')
		self.br.select_form('login')
		self.br.form['userid'] = username
		self.br.form['pwd'] = password
		self.br.submit()

		resp = self.br.response().read()
		soup = BeautifulSoup.BeautifulSoup(resp)

		if 'errorCode' in self.br.geturl():
			error_tags = soup.findAll(attrs={'class': 'PSERRORTEXT'})
			if len(error_tags) == 1:
				raise LoginError('Quest: %s' % (error_tags[0].text))
			else:
				raise InterfaceError('Could not determine error when logging'
						'in.')
		elif self.is_logged_in():
			logger.debug('Successfully logged in.')

			return True
		else:
			raise InterfaceError('Unexpected result upon logging in.')

	def _authenticated(f):
		"""
		Decorator for methods which must have a valid session to work.
		"""

		def decorated(self, *args):
			if self.is_logged_in():
				logger.debug('Already logged in.')
			elif self.auto_authenticate and self.username and self.password:
				logger.info('Automatically logging in as "%s".', self.username)

				self.login(self.username, self.password)
			else:
				raise AuthenticationError('Not logged in.')

			return f(self, *args)

		return decorated

	def _parse_grade(self, grade):
		"""
		Suppress all non-grade values.
		
		Some valid grade values include: '', '12', 'CR'.
		"""

		if 'nbsp' in grade: # Empty cells have &nbsp; in them.
			return ''
		else:
			return grade

	@_authenticated
	def fetch_grade_terms(self):
		"""
		Fetch the list of terms for which grades can be requested.
		"""

		logger.debug('Fetching list of terms.')

		self.br.open(self.base_url + 'c/SA_LEARNER_SERVICES.SSR_SSENRL_GRADE.'
				'GBL?Page=SSR_SSENRL_GRADE')

		resp = self.br.response().read()
		soup = BeautifulSoup.BeautifulSoup(resp)

		term_ids = [x.get('value') for x in
				soup.findAll(attrs={'name': 'SSR_DUMMY_RECV1$sels$0'})]
		terms = [x.text for x in
				soup.findAll(attrs={'class': 'PSEDITBOX_DISPONLY'})[0::3]]

		if len(term_ids) != len(terms):
			raise InterfaceError('Mismatch between number of term_ids (%d) '
					'and number of terms (%d)' % (len(term_ids), len(terms)))

		return term_ids, terms

	@_authenticated
	def fetch_grades(self, term):
		"""
		Fetch the grades for a given term.

		term -- Specified as the radio button ID string of the desired term.
				(cf. fetch_grade_terms)
		"""

		logger.debug('Fetching grades for term "%s".', term)

		self.br.open(self.base_url + 'c/SA_LEARNER_SERVICES.SSR_SSENRL_GRADE.'
				'GBL?Page=SSR_SSENRL_GRADE')
		self.br.select_form('win0')
		self.br.form.set_all_readonly(False)
		self.br.form['SSR_DUMMY_RECV1$sels$0'] = [term]
		self.br.form['ICAction'] = 'DERIVED_SSS_SCT_SSR_PB_GO'
		self.br.submit()

		resp = self.br.response().read()
		soup = BeautifulSoup.BeautifulSoup(resp)

		courses = [x.text for x in soup.findAll('a', attrs={
				'id': re.compile('CLS_LINK')})]
		grades = [x.text for x in soup.findAll(attrs={'class': 'PABOLDTEXT'})]

		if len(courses) != len(grades):
			raise InterfaceError('Mismatch between number of courses (%d) and '
					'number of grades (%d)' % (len(courses), len(grades)))

		return courses, [self._parse_grade(x) for x in grades]
