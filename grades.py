#!/usr/bin/env python2

import BeautifulSoup
import getpass
import mechanize
import prettytable
import re

# Optional configuration. If not set, obtained interactively.
username = None # 'a99bcdef'
password = None # '!@#$%^&*'

def parse_grade(grade):
	"""Suppress all non-integer values."""
	try:
		int(grade)
		return grade
	except ValueError:
		return ''

def fetch_grades(username, password, term):
	"""Login to Quest, and get the grades for the given term."""
	br = mechanize.Browser()

	br.open('https://quest.pecs.uwaterloo.ca/psp/SS/ACADEMIC/SA/')
	br.select_form('login')
	br.form['userid'] = username
	br.form['pwd'] = password
	br.submit()

	br.open('https://quest.pecs.uwaterloo.ca/psc/SS/ACADEMIC/SA/c/SA_LEARNER_SERVICES.SSR_SSENRL_GRADE.GBL?Page=SSR_SSENRL_GRADE')
	br.select_form('win0')
	br.form.set_all_readonly(False)
	br.form['SSR_DUMMY_RECV1$sels$0'] = [term]
	br.form['ICAction'] = 'DERIVED_SSS_SCT_SSR_PB_GO'
	br.submit()

	resp = br.response().read()

	br.close()

	return resp

def parse_response(resp):
	soup = BeautifulSoup.BeautifulSoup(resp)

	courses = [x.text for x in soup.findAll(attrs={'id': re.compile('CLS_LINK.+')})]
	grades = [x.text for x in soup.findAll(attrs={'class': 'PABOLDTEXT'})]

	return courses, grades

def make_table(courses, grades):
	pt = prettytable.PrettyTable(["Course", "Grade"])

	for course, grade in zip(courses, grades):
		pt.add_row([course, parse_grade(grade)])

	return pt

# Get any missing credentials.
if not username:
	username = raw_input('Quest username: ')

if not password:
	password = getpass.getpass('Password for %s: ' % (username))

# Go!
resp = fetch_grades(username, password, '2')
courses, grades = parse_response(resp)
make_table(courses, grades).printt(header=False, border=False)
