import web
from web import form
import logging
from alyosha import alyosha as al
from alyosha import reference as REF
# TODO: add threading for web requests

# Configure the logger
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
        form.Textbox('URL', form.notnull, decription='Reference URL'),
        class_='urlform')

searchPhrasesForm = form.Form(
        form.Checkbox('Search phrases'),
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


class request(object):

    def GET(self):
        return render.request(formDict)

    def POST(self):
        for form in formDict.values():
            if not form.validates():
                return render.request(formDict)

        # extract form data
        form_data = web.input()
        ref_url = form_data['URL']
        months_in_past = int(form_data['Months in past'])
        searchPhrases = 'Search phrases' in form_data
        forcePhrases = 'Force phrases' in form_data
        logging.debug("ref_url=%s" % ref_url)
        logging.debug("month in past=%d" % months_in_past)
        logging.debug("Search phrases=%s" % searchPhrases)
        logging.debug("Force phrases=%s" % forcePhrases)

        try:
            wa = al.WebArticle(ref_url, REF.stop_words,
                    REF.late_kills)
            logging.debug("article '%s' (%d words) at url='%s': query='%s'",
                    wa.title, wa.wcount, wa.url,
                    wa.search_string(use_phrases=searchPhrases,
                        force_phrases=forcePhrases))
        except al.ArticleFormatError:
            return render.error("Non-html resource at %s" % ref_url,
                                '/request')
        except al.ArticleExtractionError:
            return render.error("Cannot extract article from %s" % ref_url,
                                '/request')
        except al.InvalidUrlError:
            return render.error("Invalid URL: %s" % ref_url, '/request')
        except al.PageRetrievalError:
            return render.error("Could not retrieve URL: %s" % ref_url,
                                '/request')

        results = {}
        for cat, rng in src_cats.iteritems():
            sources = dict((src, v[0]) for (src, v) in
                    REF.source_sites.iteritems() if rng[0] <= v[1] < rng[1])
            results[cat] = al.rank_matches(wa, sources,
                    use_phrases=searchPhrases, force_phrases=forcePhrases,
                    back_days=months_in_past * 30, allintext=True)
            logging.debug("%s: %d ranked results", cat, len(results[cat]))

        return render.results(wa, results, '/request')


class results(object):

    def GET(self):
        return render.results(None, None,
                REF.source_sites.keys(), '/request')


# For serving using any wsgi server
wsgiapp = web.application(urls, globals()).wsgifunc()


if __name__ == '__main__':

    app = web.application(urls, globals())
    app.run()
