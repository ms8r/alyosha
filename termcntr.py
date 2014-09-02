from alyosha import alyosha as al
from alyosha import reference as REF
import time
from random import random
from random import shuffle
import logging
from itertools import product
import sys

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
        'obamacare']

short_sleep = 30
long_sleep = 1852
max_fail_count = 3

sources = [s.site for s in sorted(REF.source_sites,
           key=lambda k: k.specVal, reverse=True)]

if __name__ == '__main__':

    with open('termcntr.done', 'r') as fin:
        done = set([tuple(line.rstrip().split('\t')[:2]) for line in fin])

    todo = list(product(sources, [base_term] + test_terms))
    todo = set([t for t in todo if t not in done])
    first = True
    fail_count = 0
    gs = al.GoogleSerp()
    while todo:
        if not first:
            time.sleep(long_sleep)
        else:
            first = False
        items = list(todo)
        shuffle(items)
        if fail_count > max_fail_count:
            fail_count -= 1
        for src, t in items:
            if fail_count > max_fail_count:
                break
            time.sleep((short_sleep + random() * short_sleep) / 2.)
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
