# scrape-quest

Python interface to the [University of Waterloo Quest System](http://quest.uwaterloo.ca/).

## Synopsis

``` python
from quest import scraper

qs = scraper.QuestScraper()

try:
    qs.login(username, password)
except scraper.LoginError as e:
    print e.message
    sys.exit(1)

courses, grades = qs.fetch_grades(term)
```

## Usage

The current way to use this package is through `git-submodule`:

1. `git submodule add git://github.com/0/scrape-quest.git quest`
2. `git submodule init`
3. `from quest import scraper`

Though, ideally, this should make its way to PyPI at some point. 

## Supported functions

The module currently supports:

* logging in
* fetching grades for a term
