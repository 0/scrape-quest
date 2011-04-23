import BeautifulSoup
import mechanize
import re


class InterfaceError(Exception):
	"""
	An exceptional turn of events when talking to Quest.
	"""


class LoginError(Exception):
	"""
	Failure to log in.
	"""


class QuestScraper(object):
	"""
	A scraper for Quest.

	All methods raise InterfaceError if they encounter something unexpected.
	"""

	base_url = 'https://quest.pecs.uwaterloo.ca/psc/SS/ACADEMIC/SA/'

	def __init__(self):
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
				raise InterfaceError('Could not determine error when logging in.')
		elif self.is_logged_in():
			return True
		else:
			raise InterfaceError('Unexpected result upon logging in.')

	def fetch_grades(self, term):
		"""
		Fetch the grades for a given term.

		term -- Specified as the radio button ID string of the desired term.
		"""

		self.br.open(self.base_url + 'c/SA_LEARNER_SERVICES.SSR_SSENRL_GRADE.GBL?Page=SSR_SSENRL_GRADE')
		self.br.select_form('win0')
		self.br.form.set_all_readonly(False)
		self.br.form['SSR_DUMMY_RECV1$sels$0'] = [term]
		self.br.form['ICAction'] = 'DERIVED_SSS_SCT_SSR_PB_GO'
		self.br.submit()

		resp = self.br.response().read()
		soup = BeautifulSoup.BeautifulSoup(resp)

		courses = [x.text for x in soup.findAll(attrs={'id': re.compile('CLS_LINK')})]
		grades = [x.text for x in soup.findAll(attrs={'class': 'PABOLDTEXT'})]

		if len(courses) != len(grades):
			raise InterfaceError('Mismatch between number of courses (%d) and'
					'number of grades (%d)' % (len(courses), len(grades)))

		return courses, grades
