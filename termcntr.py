from alyosha import alyosha as al
from alyosha import reference as REF
import time
from random import random
from random import shuffle
import logging
from itertools import product

logging.basicConfig(level=logging.INFO)

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
max_fail_count = 5

sources = [s.site for s in sorted(REF.source_sites,
           key=lambda k: k.specVal, reverse=True)]

sources = sources[:3]
test_terms = test_terms[:2]

gs = al.GoogleSerp()

items = list(product(sources, [base_term] + test_terms))
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
            logging.warning("%s:%s: %s: ", src, t, type(e), e.message)
        else:
            logging.info("%s:%s:%d", src, t, num_res)
            todo.remove((src, t))
            if fail_count:
                fail_count -= 1
