import os
from urllib import urlencode
import urlparse
import logging
import json
from collections import OrderedDict
import web
from web import form
import rfc3987
import redis
import rq
from alyosha import alyosha as al
from alyosha import reference as REF


# Minimum word count for search result to be eligible
MIN_WC = 400
# Minimum match score for search result to be eligible
MIN_MATCH = 0.4
# Number of results per catergory (left-center-right)
NUM_MATCHES = 2
# Cut-off for source site's quality weight to be included in search (heavy
# sinks to bottom, [0, 100]
MAX_QUALITY_WEIGHT = 50
# number of stem_top list elements to consider for match score:
MATCH_SCORE_LEN = 20
# Max. wait (in seconds) in between calls to Google:
GOOGLE_DELAY = 1

logging.basicConfig(level=logging.DEBUG)

# Connect to Redis and define expiry in seconds:
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
# urlparse.uses_netloc.append('redis')
# url = urlparse.urlparse(redis_url)
# redis_conn = redis.StrictRedis(host=url.hostname, port=url.port)
redis_conn = redis.from_url(redis_url)
REDIS_EXPIRE = 1200

render = web.template.render('templates/', base='layout')

urls = (
    '/', 'index',
    '/request', 'request',
    '/results', 'results',
    '/scorematches', 'score_matches',
    '/error', 'error',
    '/thify-what', 'thify_what',
    '/thify-why', 'thify_why',
    '/thify-how', 'thify_how'
)

urlForm = form.Form(
        form.Textbox(
            'URL',
            form.notnull,
            description='',
            id='url-entry'))

# construct the source checkboxes:
srcSitesForms = []
for cat in REF.src_cats:
    cs = REF.cat_sources(cat)
    cbForms = [form.Checkbox(c.id, checked=(c.weight <= MAX_QUALITY_WEIGHT),
            value=c.site, description=c.label) for c in cs]
    srcSitesForms.append(form.Form(*cbForms))

matchCriteriaForm = form.Form(
        form.Textbox(
            'matchScore',
            form.notnull,
            form.regexp('\d+', 'Must be an integer number'),
            size='5',
            maxlength='3',
            description='Desired content match:',
            post='%',
            value=int(MIN_MATCH * 100),
            id='match-score'),
        form.Textbox(
            'minWC',
            form.notnull,
            form.regexp('\d+', 'Must be an integer number'),
            size='5',
            maxlength='4',
            description='Minimum word count:',
            value=MIN_WC,
            id='min-word-count'),
        form.Dropdown(
            'backMonths',
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            value=0,
            description="No older than:",
            post='months (0 for no age restrictions)',
            id='back-months'))

formDict = {
        'src_by_cat': srcSitesForms,
        'match_criteria': matchCriteriaForm,
}


class index(object):

    def GET(self):
        return render.index(urlForm)

    def POST(self):

        if not urlForm.validates():
            return render.index(urlForm)
        form_data = web.input()

        check_spec = True if 'checkspec' in form_data else False

        if rfc3987.match(form_data.URL, rule='URI_reference'):
            parsed = urlparse.urlparse(form_data['URL'], scheme='http')
            ref_url = parsed.scheme + '://' + '/'.join([parsed.netloc,
                    parsed.path.lstrip('/')]).lstrip('/')
        else:
            ref_url = None

        if ref_url:
            params = {'url': ref_url,
                      'checkspec': int(check_spec)}
            raise web.seeother('/request?' + urlencode(params), '/')
        else:
            params = {
                    'msg': "Sorry, not implememted yet...",
                    'back_link': '/'
            }
            raise web.seeother('/error?' + urlencode(params))


class request(object):

    cust_search_prompt = 'Roll your own:'

    def GET(self):

        i = web.input(url='', back_link='/', checkspec='0')
        try:
            wa = al.WebArticle(i.url, REF.stop_words, REF.late_kills)
            logging.debug("article '%s' (%d words) at url='%s'",
                    wa.title, wa.wcount, wa.url)
        except (al.NotAnArticleError, al.ArticleFormatError,
                al.ArticleExtractionError, al.InvalidUrlError,
                al.PageRetrievalError) as e:
            params = {
                    'msg': "%s: %s" % (type(e), e.message),
                    'back_link': '/'
            }
            raise web.seeother('/error?' + urlencode(params))
        # need to de-dupe search_strings in case no phrases are found
        search_str_opts = [
                {'use_phrases': False, 'force_phrases': False},
                {'use_phrases': True, 'force_phrases': False},
                {'use_phrases': True, 'force_phrases': True}
        ]
        search_str_choices = list(dedupe([wa.search_string(num_terms=6, **sso)
                                          for sso in search_str_opts]))

        # store essentials on Redis:
        wa_key = al.RedisWA.redis_store(redis_conn, wa.url, wa.title,
                wa.wcount, wa.stem_tops[:MATCH_SCORE_LEN], search_str_choices)
        redis_conn.expire(wa_key, REDIS_EXPIRE)

        if not int(i.checkspec):
            # use 'unforced phrases' for search string if available
            ssi = 1 if len(search_str_choices) > 1 else 0
            src_sel = [s.id for s in REF.source_sites
                       if s.weight <= MAX_QUALITY_WEIGHT]
            params = {
                    'wa_key': wa_key,
                    'search_str': search_str_choices[ssi],
                    'sources': encode_src_sel(src_sel),
                    'match_score': int(MIN_MATCH * 100),
                    'min_wc': MIN_WC,
                    'back_days': 0,
            }
            logging.debug("request parameter: %s" % params)
            raise web.seeother('/results?' + urlencode(params))


        # set "no phrases" search string as default:
        radio_buttons = [form.Radio('SearchStr', [search_str_choices[0]],
                description='', value=search_str_choices[0],
                class_='search-string-choice')]
        # add remaining search string options (if any)
        radio_buttons += [form.Radio('SearchStr', [ssc], description='',
                class_='search-string-choice') for ssc in
                search_str_choices[1:]]
        radio_buttons.append(form.Radio('SearchStr',
                [request.cust_search_prompt], description='',
                id='cust-search-rb'))
        # add custom search string choice and text box
        radio_buttons.append(form.Textbox('CustSearch', description='',
                size='40', id='cust-search-entry'))
        formDict['search_strings'] = form.Form(*radio_buttons)

        # put redis key string into hidden form field for retrieval by POST:
        formDict['wa_key'] = form.Form(form.Textbox(
                'waKey',
                form.notnull,
                description='',
                id='wa-key',
                value=wa_key,
                style="display: none;"))

        return render.request(formDict, REF.src_cats.keys(), wa.title, wa.url)

    def POST(self):

        for entry in formDict.values():
            if type(entry) is list:
                for f in entry:
                    if not f.validates():
                        return render.request(formDict)
            else:
                if not entry.validates():
                    return render.request(formDict)
        form_data = web.input()

        search_str = form_data.SearchStr
        if search_str == request.cust_search_prompt:
            search_str = form_data.CustSearch

        params = {
                'wa_key': form_data.waKey,
                'search_str': search_str,
                'sources': encode_src_sel(form_data),
                'match_score': int(form_data.matchScore),
                'min_wc': int(form_data.minWC),
                'back_days': int(form_data.backMonths) * 30,
        }
        logging.debug("request parameter: %s" % params)
        raise web.seeother('/results?' + urlencode(params))


class results(object):

    def GET(self):

        i = web.input(wa_key=None, search_str=None, sources=0, match_score=0,
                min_wc=0, back_days=None)
        logging.debug("results parameter: wa_key=%s, search_str='%s', "
                "sources=%s, match_score=%s, min_wc=%s, back_days=%s",
                i.wa_key, i.search_str, i.sources, i.match_score, i.min_wc,
                i.back_days)
        # get WebArticle data from Redis:
        try:
            rwa = al.RedisWA(redis_conn, i.wa_key)
        except al.RedisGetError as e:
            logging.debug("%s: %s", type(e), e.message)
            raise

        # we need to construct a dict of source categories mapped to the
        # correponding (masked) source lists to be passed by render to the
        # page, so we can include it there as a JS variable.
        cat_sources = OrderedDict()
        for cat in REF.src_cats:
            cat_sources[cat] = REF.cat_sources(cat, sites_only=True,
                    sort_by='weight', mask=decode_src_sel(int(i.sources)))

        return render.results(
                rwa, i.search_str, cat_sources, i.match_score, i.min_wc,
                i.back_days, '/request')


class score_matches(object):

    q = rq.Queue(connection=redis_conn)

    def GET(self):
        i = web.input(wa_key=None, search_str=None, src=None, job_id=None)
        logging.debug("score_matches called with '%s'", i)
        web.header('Content-Type', 'application/json')
        if i.get('job_id'):
            # they want us to check for results...
            job = score_matches.q.fetch_job(i.job_id)
            status = job.get_status()
            result = (job.result[0] if status == rq.job.Status.FINISHED
                      and job.result else '')
            s = json.dumps({'src': i.src, 'job_id': i.job_id, 'status': status,
                'result': result})
            logging.debug("JSON string: %s", s)
            return s

        else:
            # get worker busy; first retrieve original article from Redis:
            rwa = al.RedisWA(r=redis_conn, key=i.wa_key)
            job = score_matches.q.enqueue(al.score_matches, rwa, [i.src],
                    i.search_str, num_matches=3,
                    delay=GOOGLE_DELAY, encoding='utf-8')
            s = json.dumps({'src': i.src, 'job_id': job.id})
            logging.debug("JSON string: %s", s)
            return s


class error(object):

    def GET(self):
        i = web.input(msg='', back_link='/')
        return render.error(i.msg, i.back_link)


class thify_what(object):

    def GET(self):
        return render.thify_what(msg='')



class thify_why(object):

    def GET(self):
        return render.thify_why(msg='')



class thify_how(object):

    def GET(self):
        return render.thify_how(msg='')



def dedupe(items):
    """
    Utility generator that eliminates duplicates from a sequence while
    maintaining order (source: Python Cookbook)
    """
    seen = set()
    for item in items:
        if item not in seen:
            yield item
            seen.add(item)


def encode_src_sel(src_sel):
    """
    Encodes selected sources as binary flags an returns as a decimal number.
    `src_sel` can be ani kind of object that supports `in` for membership
    checking (e.g. form_data dict).
    """
    selection = 0
    for i, s in enumerate(REF.source_sites):
        if s.id in src_sel:
            selection += 2 ** i
    return selection


def decode_src_sel(selection):
    """
    Returns boolean array indicating which sources in REF.source_sites have
    been included in the selection. `selection` is an integer.
    """
    decoded = list(reversed(str(bin(selection))[2:]))
    decoded = [(True if int(d) else False) for d in decoded]
    decoded += [False] * (len(REF.source_sites) - len(decoded))
    return decoded


# For serving using any wsgi server
wsgiapp = web.application(urls, globals()).wsgifunc()


if __name__ == '__main__':

    app = web.application(urls, globals())
    app.run()
