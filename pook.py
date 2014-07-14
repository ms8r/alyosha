from urllib import urlencode
from urlparse import urlparse
import logging
import web
from web import form
from alyosha import alyosha as al
from alyosha import reference as REF
# TODO: add threading for web requests

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
        use_phrases = 'Use phrases' in form_data
        force_phrases = 'Force phrases' in form_data
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
        i = web.input(url=None, use_phrases=False, force_phrases=False,
                back_days=None)
        try:
            wa = al.WebArticle(i.url, REF.stop_words, REF.late_kills)
            logging.debug("article '%s' (%d words) at url='%s': query='%s'",
                    wa.title, wa.wcount, wa.url,
                    wa.search_string(use_phrases=i.use_phrases,
                        force_phrases=i.force_phrases))
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
            sources = dict((src, v[0]) for (src, v) in
                    REF.source_sites.iteritems() if rng[0] <= v[1] < rng[1])
            results[cat] = al.rank_matches(wa, sources,
                    use_phrases=i.use_phrases, force_phrases=i.force_phrases,
                    back_days=int(i.back_days), allintext=False)
            logging.debug("%s: %d ranked results", cat, len(results[cat]))

        return render.results(wa, results, '/request')


# For serving using any wsgi server
wsgiapp = web.application(urls, globals()).wsgifunc()


if __name__ == '__main__':

    app = web.application(urls, globals())
    app.run()
