from urllib import urlencode
from urlparse import urlparse
import logging
import web
from web import form
from alyosha import alyosha as al
from alyosha import reference as REF
# TODO: add threading for web requests

# Minimum word count for search result to be eligible
MIN_WC = 400
# Minimum match score for search result to be eligible
MIN_MATCH = 0.3
# Number of results per catergory (left-center-right)
NUM_MATCHES = 1
# Cut-off for source site's quality weight to be included in search (heavy
# sinks to bottom, [0, 100]
MAX_QUALITY_WEIGHT = 45
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
        form.Textbox('URL', form.notnull, description='Reference URL'),
        class_='urlform')

searchPhrasesForm = form.Form(
        form.Checkbox('Use phrases'),
        form.Checkbox('Force phrases'))

dateRangeForm = form.Form(
        form.Dropdown('Months in past', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], value=0))

formDict = {
        'url': urlForm,
        'phrases': searchPhrasesForm,
        'date_range': dateRangeForm,
}

# source grouping: intervals below are open on the left
src_cats = {
        'right': (-1.0, -0.5),
        'center': (-0.5, 0.5),
        'left': (0.5, 1.0)
}


class index(object):

    def GET(self):
        return render.index('/request')


class error(object):

    def GET(self):
        i = web.input(msg='', back_link='/index')
        return render.error(i.msg, i.back_link)


class request(object):

    def GET(self):
        return render.request(formDict)

    def POST(self):
        for form in formDict.values():
            if not form.validates():
                return render.request(formDict)
        form_data = web.input()
        parsed = urlparse(form_data['URL'])
        scheme = parsed[0] if parsed[0] else 'http'
        # ignore any parameters url:
        ref_url = scheme + '://' + parsed[1] + parsed[2]
        back_days = int(form_data['Months in past']) * 30
        use_phrases = 1 if 'Use phrases' in form_data else 0
        force_phrases = 1 if 'Force phrases' in form_data else 0
        params = {
                'url': ref_url,
                'use_phrases': use_phrases,
                'force_phrases': force_phrases,
                'back_days': back_days
        }
        logging.debug("request parameter: %s" % params)
        raise web.seeother('/results?' + urlencode(params))


class results(object):

    def GET(self):
        i = web.input(url=None, use_phrases=0, force_phrases=0,
                back_days=None)
        logging.debug("results parameter: url=%s, use_phrases=%s, "
                      "force_phrases=%s, back_days=%s" %
                      (i.url, bool(int(i.use_phrases)),
                      bool(int(i.force_phrases)), i.back_days))
        try:
            wa = al.WebArticle(i.url, REF.stop_words, REF.late_kills)
            search_str = wa.search_string(use_phrases=int(i.use_phrases),
                    force_phrases=int(i.force_phrases))
            logging.debug("article '%s' (%d words) at url='%s': query='%s'",
                    wa.title, wa.wcount, wa.url, search_str)
        except al.ArticleFormatError:
            params = {
                    'msg': "Non-html resource at %s" % i.url,
                    'back_link': '/request'
            }
            raise web.seeother('/error?' + urlencode(params))
        except al.ArticleExtractionError:
            params = {
                    'msg': "Cannot extract article from %s" % i.url,
                    'back_link': '/request'
            }
            raise web.seeother('/error?' + urlencode(params))
        except al.InvalidUrlError:
            params = {
                    'msg': "Invalid URL: %s" % i.url,
                    'back_link': '/request'
            }
            raise web.seeother('/error?' + urlencode(params))
        except al.PageRetrievalError:
            params = {
                    'msg': "Could not retrieve URL: %s" % i.url,
                    'back_link': '/request'
            }
            raise web.seeother('/error?' + urlencode(params))

        results = {}
        for cat, rng in src_cats.iteritems():
            sources = [(t[2], t[0]) for t in REF.source_sites.values()
                       if (rng[0] <= t[1] < rng[1]) and t[2] <=
                       MAX_QUALITY_WEIGHT]
            sources = [t[1] for t in sorted(sources)]
            results[cat] = al.best_matches(wa, sources, search_str,
                    back_days=int(i.back_days), min_wc=MIN_WC,
                    min_match=MIN_MATCH, num_matches=NUM_MATCHES,
                    exact=False, delay=GOOGLE_DELAY, allintext=False)
            logging.debug("%s: %d ranked results", cat, len(results[cat]))

        return render.results(wa, search_str, results, '/request')


# For serving using any wsgi server
wsgiapp = web.application(urls, globals()).wsgifunc()


if __name__ == '__main__':

    app = web.application(urls, globals())
    app.run()
