import BeautifulSoup
import mechanize
import re

class QuestScraper(object):
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
		self.br.open(self.base_url + '?cmd=login')
		self.br.select_form('login')
		self.br.form['userid'] = username
		self.br.form['pwd'] = password
		self.br.submit()

	def fetch_grades(self, term):
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

		return courses, grades