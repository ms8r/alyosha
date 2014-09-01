from alyosha import alyosha as al
from alyosha import reference as REF
import time
from random import random
import re
import logging
import json

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
        '"tree hugger"',
        '"endangered species"',
        '"austerity measures"',
        '"fiscal discipline"',
        '"feminist movement"',
        '"christian values"',
        '"the feds"',
        '"federal government"',
        '"environmental activist"',
        'discrimination',
        'religious right',
        'obamacare' ]

max_sleep = 30

sources = [s.site for s in sorted(REF.source_sites,
           key=lambda k: k.specVal, reverse=True)]

gs = al.GoogleSerp()
for src in sources:
    time.sleep(random() * max_sleep)
    try:
        num_res = gs.search(base_term, exact=True, site=src)
        logging.info("%s:%s:%d", src, base_term, num_res)
    except al.EmptySearchResult:
        num_res = 0
        logging.info("%s:%s:%d", src, base_term, num_res)
    except (al.ResultParsingError, al.PageRetrievalError) as e:
        logging.warning("%s:%s: %s", src, base_term, e)
    for t in test_terms:
        time.sleep(random() * max_sleep)
        try:
            num_res = gs.search(t, exact=True, site=src)
            logging.info("%s:%s:%d", src, t, num_res)
        except al.EmptySearchResult:
            num_res = 0
            logging.info("%s:%s:%d", src, t, num_res)
        except (al.ResultParsingError, al.PageRetrievalError) as e:
            logging.warning("%s:%s: %s", src, base_term, e)

