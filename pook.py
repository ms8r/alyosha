from urllib import urlencode
from urlparse import urlparse
import logging
import re
import web
from web import form
import rfc3987
from alyosha import alyosha as al
from alyosha import reference as REF
# TODO: add threading for web requests

# Minimum word count for search result to be eligible
MIN_WC = 400
# Minimum match score for search result to be eligible
MIN_MATCH = 0.4
# Number of results per catergory (left-center-right)
NUM_MATCHES = 2
# Cut-off for source site's quality weight to be included in search (heavy
# sinks to bottom, [0, 100]
MAX_QUALITY_WEIGHT = 50
# Max. wait (in seconds) in between calls to Google:
GOOGLE_DELAY = 1

logging.basicConfig(level=logging.DEBUG)

render = web.template.render('templates/', base='layout')

urls = (
    '/', 'index',
    '/request', 'request',
    '/results', 'results',
    '/sources', 'sources',
    '/error', 'error'
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

# for now a global to maintain WebArticle object across pages
wa = None


class index(object):

    def GET(self):
        return render.index(urlForm)

    def POST(self):

        global wa

        if not urlForm.validates():
            return render.index(urlForm)
        form_data = web.input()

        check_spec = True if 'checkspec' in form_data else False

        if rfc3987.match(form_data.URL, rule='URI_reference'):
            parsed = urlparse(form_data['URL'], scheme='http')
            ref_url = parsed.scheme + '://' + '/'.join([parsed.netloc,
                    parsed.path]).lstrip('/')
        else:
            ref_url = None

        if ref_url and check_spec:
            params = {'url': ref_url}
            raise web.seeother('/request?' + urlencode(params), '/')
        else:
            params = {
                    'msg': "Sorry, not implememted yet...",
                    'back_link': '/'
            }
            raise web.seeother('/error?' + urlencode(params))


class error(object):

    def GET(self):
        i = web.input(msg='', back_link='/')
        return render.error(i.msg, i.back_link)


class request(object):

    cust_search_prompt = 'Roll your own:'

    def GET(self):

        global wa

        i = web.input(url='', back_link='/')
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
        i = web.input(search_str=None, sources=0, match_score=0, min_wc=0,
                back_days=None)
        logging.debug("results parameter: search_str='%s', sources=%s, "
                      "match_score=%s, min_wc=%s, back_days=%s",
                      i.search_str, i.sources, i.match_score, i.min_wc,
                      i.back_days)
        results = {}
        for cat in REF.src_cats:
            sources = REF.cat_sources(cat, sites_only=True, sort_by='weight',
                    mask=decode_src_sel(int(i.sources)))
            # Note: each `results` entry will be a tuple (m, d) with m being a
            # list of matches and d being a list of discards
            results[cat] = al.best_matches(wa, sources, i.search_str,
                    back_days=int(i.back_days), min_wc=int(i.min_wc),
                    min_match=int(i.match_score) / 100.,
                    num_matches=NUM_MATCHES, exact=False, delay=GOOGLE_DELAY,
                    allintext=False)
            logging.debug("%s: %d ranked results", cat, len(results[cat][0]))

        return render.results(wa, i.search_str, REF.src_cats.keys(), results,
                '/request')


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


def encode_src_sel(form_data):
    """
    Encodes selected sources as binary flags an returns as a decimal number.
    """
    selection = 0
    for i, s in enumerate(REF.source_sites):
        if s.id in form_data:
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
