from alyosha import alyosha as al
from alyosha import reference as REF
import time
from random import random
from random import shuffle
import logging
from itertools import product
import sys

logging.basicConfig(level=logging.INFO)

done = set([
    ('washingtonpost.com', '"religious tolerance"'),
    ('slate.com', '"fiscal discipline"'),
    ('econlib.org', '"fiscal discipline"'),
    ('slate.com', '"whistleblower edward snowden"'),
    ('wsj.com', '"single mother"'),
    ('brookings.edu', '"the feds"'),
    ('slate.com', '"affordable care"'),
    ('theguardian.com', '"rising inequality"'),
    ('theatlantic.com', 'discrimination'),
    ('fivethirtyeight.com', '"scientific evidence"'),
    ('spiegel.de', '"affordable care act"'),
    ('foxnews.com', '"feminist movement"'),
    ('huffingtonpost.com', '"national security"'),
    ('thenation.com', '"religious beliefs"'),
    ('fivethirtyeight.com', '"christian values"'),
    ('townhall.com', '"affordable care"'),
    ('nytimes.com', '"religious right"'),
    ('thenation.com', '"fiscal discipline"'),
    ('nytimes.com', '"fiscal discipline"'),
    ('weeklystandard.com', '"government intervention"'),
    ('theatlantic.com', 'obamacare'),
    ('economist.com', '"religious beliefs"'),
    ('dailykos.com', 'political'),
    ('fivethirtyeight.com', 'political'),
    ('foxnews.com', '"single parent"'),
    ('economist.com', '"federal government"'),
    ('theatlantic.com', '"free market"'),
    ('wsj.com', '"feminist movement"'),
    ('brookings.edu', 'obamacare'),
    ('theatlantic.com', '"same sex marriage"'),
    ('huffingtonpost.com', '"austerity measures"'),
    ('lawfareblog.com', '"religious convictions"'),
    ('econlib.org', '"american values"'),
    ('spiegel.de', '"whistleblower edward snowden"'),
    ('townhall.com', '"free market"'),
    ('brookings.edu', '"rising inequality"'),
    ('motherjones.com', '"affordable care act"'),
    ('huffingtonpost.com', '"scientific evidence"'),
    ('spiegel.de', '"government intervention"'),
    ('brookings.edu', '"whistleblower edward snowden"'),
    ('nationalreview.com', '"the feds"'),
    ('foxnews.com', '"environmental activist"'),
    ('economist.com', '"religious tolerance"'),
    ('nytimes.com', '"super rich"'),
    ('motherjones.com', '"efficient market"'),
    ('wsj.com', '"free market"'),
    ('nytimes.com', '"same sex marriage"'),
    ('fivethirtyeight.com', '"religious convictions"'),
    ('nytimes.com', '"government intervention"'),
    ('factcheck.org', '"religious tolerance"'),
    ('slate.com', '"scale back government"'),
    ('theatlantic.com', '"scientific evidence"'),
    ('huffingtonpost.com', '"rising inequality"'),
    ('weeklystandard.com', '"christian values"'),
    ('msnbc.com', '"same sex marriage"'),
    ('motherjones.com', '"environmental activist"'),
    ('hoover.org', '"austerity measures"'),
    ('motherjones.com', '"single parent"'),
    ('motherjones.com', '"religious beliefs"'),
    ('spiegel.de', '"gay rights"'),
    ('hoover.org', '"government intervention"'),
    ('thenation.com', 'political'),
    ('brookings.edu', '"gay rights"'),
    ('foxnews.com', '"gay marriage"'),
    ('msnbc.com', '"feminist movement"'),
    ('slate.com', '"religious right"'),
    ('motherjones.com', '"american values"'),
    ('townhall.com', '"minimum wage"'),
    ('economist.com', '"government intervention"'),
    ('theguardian.com', 'obamacare'),
    ('washingtonpost.com', '"government intervention"'),
    ('brookings.edu', '"religious liberty"'),
    ('hoover.org', '"super rich"'),
    ('hoover.org', 'obamacare'),
    ('weeklystandard.com', '"single mother"'),
    ('thenation.com', '"gay movement"'),
    ('slate.com', '"environmental activist"'),
    ('dailykos.com', '"religious beliefs"'),
    ('townhall.com', '"gay movement"'),
    ('foxnews.com', '"religious right"'),
    ('economist.com', '"gay marriage"'),
    ('foxnews.com', '"austerity measures"'),
    ('thenation.com', '"single parent"'),
    ('brookings.edu', '"national security"'),
    ('msnbc.com', '"scientific evidence"'),
    ('motherjones.com', '"federal government"'),
    ('fivethirtyeight.com', 'discrimination'),
    ('nytimes.com', '"scientific evidence"'),
    ('washingtonpost.com', '"endangered species"'),
    ('hoover.org', '"religious right"'),
    ('economist.com', '"affordable care act"'),
    ('weeklystandard.com', '"american values"'),
    ('theatlantic.com', '"austerity measures"'),
    ('townhall.com', '"fiscal discipline"'),
    ('slate.com', '"super rich"'),
    ('theatlantic.com', '"religious right"'),
    ('thenation.com', '"scale back government"'),
    ('csmonitor.com', '"affordable care act"'),
    ('brookings.edu', '"federal government"'),
    ('lawfareblog.com', '"national security"'),
    ('msnbc.com', '"super rich"'),
    ('theguardian.com', '"scientific evidence"'),
    ('factcheck.org', '"religious liberty"'),
    ('factcheck.org', '"whistleblower edward snowden"'),
    ('msnbc.com', '"affordable care"'),
    ('econlib.org', 'political'),
    ('washingtonpost.com', '"religious right"'),
    ('economist.com', '"the feds"'),
    ('wsj.com', '"religious convictions"'),
    ('lawfareblog.com', '"endangered species"'),
    ('fivethirtyeight.com', '"rising inequality"'),
    ('washingtonpost.com', '"national security"'),
    ('theatlantic.com', '"scale back government"'),
    ('lawfareblog.com', '"whistleblower edward snowden"'),
    ('spiegel.de', '"religious beliefs"'),
    ('weeklystandard.com', '"single parent"'),
    ('weeklystandard.com', '"feminist movement"'),
    ('brookings.edu', '"super rich"'),
    ('nationalreview.com', '"minimum wage"'),])

base_term = 'political'
test_terms = [
        '"super rich"',
        '"rising inequality"',
        '"scale back government"',
        '"affordable care"',
        '"gay movement"',
        '"gay rights"',
        '"scientific evidence"',
        '"same sex marriage"',
        '"gay marriage"',
        '"whistleblower edward snowden"',
        '"religious liberty"',
        '"religious tolerance"',
        '"religious beliefs"',
        '"religious convictions"',
        '"efficient market"',
        '"free market"',
        '"government intervention"',
        '"american values"',
        '"single mother"',
        '"single parent"',
        '"national security"',
        '"minimum wage"',
        '"endangered species"',
        '"austerity measures"',
        '"fiscal discipline"',
        '"feminist movement"',
        '"christian values"',
        '"the feds"',
        '"federal government"',
        '"environmental activist"',
        'discrimination',
        '"religious right"',
        '"affordable care act"',
        'obamacare' ]

short_sleep = 30
long_sleep = 300
max_fail_count = 3

sources = [s.site for s in sorted(REF.source_sites,
           key=lambda k: k.specVal, reverse=True)]

gs = al.GoogleSerp()

items = list(product(sources, [base_term] + test_terms))
items = [i for i in items if i not in done]
todo = set(items)
shuffle(items)
first = True
while todo:
    if not first:
        time.sleep(long_sleep)
    else:
        first = False
    fail_count = 0
    for src, t in items:
        if fail_count > max_fail_count:
            break
        time.sleep(random() * short_sleep)
        logging.info("*** items left: %d", len(todo))
        try:
            num_res = gs.search(t, exact=True, site=src)
        except al.EmptySearchResult:
            logging.info("%s:%s:%d", src, t, 0)
        except (al.ResultParsingError, al.PageRetrievalError) as e:
            fail_count += 1
            logging.warning("%s:%s: %s: %s", src, t, type(e), e.message)
        else:
            logging.info("%s:%s:%d", src, t, num_res)
            todo.remove((src, t))
            if fail_count:
                fail_count -= 1
