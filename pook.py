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

searchScopeForm = form.Form(
        form.Radio('Scope', [('narrow', 'include phrases and single words '
        'in query'), ('broader', 'use only phrases'), ('wide', 'use only '
        'words')], value='narrow'), class_='searchscopeform')

searchPhrasesForm = form.Form(
        form.Checkbox('Search phrases'))

minCountForm = form.Form(
        form.Dropdown('MinCount', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], value=0))

sourceSelForm = form.Form(
        form.Checkbox('Left field'),
        form.Checkbox('Center'),
        form.Checkbox('Right field'))

# source grouping: intervals below are open on the left

formDict = {
        'url': urlForm,
}

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

        form_data = web.input()
        logging.debug("ref_url=%s" % form_data['URL'])

        try:
            wa = al.WebArticle(form_data['URL'], REF.stop_words,
                    REF.late_kills)
            logging.debug("article '%s' (%d words) at url='%s': query='%s'",
                    wa.title, wa.wcount, wa.url, wa.search_string())
        except al.ArticleFormatError:
            return render.error("Non-html resource at %s" % form_data['URL'])
        except al.ArticleExtractionError:
            return render.error("Cannot extract article from %s" %
                    form_data['URL'])
        except al.InvalidUrlError:
            return render.error("Invalid URL: %s" % form_data['URL'])
        except al.PageRetrievalError:
            return render.error("Could not retrieve URL: %s" %
                    form_data['URL'])

        results = {}
        for cat, rng in src_cats.iteritems():
            sources = dict((src, v[0]) for (src, v) in
                    REF.source_sites.iteritems() if rng[0] <= v[1] < rng[1])
            results[cat] = al.rank_matches(wa, sources)
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
