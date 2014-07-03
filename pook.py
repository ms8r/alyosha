import urllib
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
sourceLeaningGroups = {
        'Left field': (0.5, 1.0),
        'Center': (-0.5, 0.5),
        'Right field': (-1.0, -0.5)
}

formDict = {
        'url': urlForm,
        'searchPhrases': searchPhrasesForm,
        'sourceSel': sourceSelForm
}


class index(object):

    def GET(self):
        return render.index('/request')


class request(object):

    max_phrases = 2
    max_words = 5

    def GET(self):
        return render.request(formDict)

    def POST(self):
        for form in formDict.values():
            if not form.validates():
                return render.request(formDict)
        else:
            form_data = web.input()
            ref_url = form_data['URL']
            logging.debug("ref_url=%s" % urllib.unquote(ref_url))
            phrases, full_words, pruned_words = al.build_search_string(
                    ref_url, stop_words=REF.stop_words,
                    late_kills=REF.late_kills)
            logging.debug("search phrases=%s" %
                    phrases[:min(10, len(phrases))])
            logging.debug("search words full=%s" %
                    full_words[:min(10, len(full_words))])
            logging.debug("search words pruned=%s" %
                    pruned_words[:min(10, len(pruned_words))])

            # build search string:
            if phrases and 'Search phrases' in form_data.keys():
                n = min(request.max_phrases, len(phrases))
                query = ' '.join(phrases[:n])
                m = min(request.max_words - n, len(pruned_words))
                sep = ' ' if query and m else ''
                query += sep + ' '.join(pruned_words[:m])
            else:
                m = min(request.max_words, len(full_words))
                query = ' '.join(full_words[:m])
            logging.debug("query: %s" % query)

            # build sources list:
            s_ranges = [v for (k, v) in sourceLeaningGroups.iteritems()
                        if k in form_data.keys()]
            logging.debug("source ranges: %s" % s_ranges)
            # compile all sources to included in dict:
            source_sites = {}
            for (k, v) in REF.source_sites.iteritems():
                for r in s_ranges:
                    if r[0] <= v[1] < r[1]:
                        source_sites[k] = v[0]
                        break
            logging.debug("source sites: %s" % source_sites.keys())
            if not source_sites:
                return render.error("No sources selected", '/request')
            result = al.full_results(source_sites, query)
            return render.results(result, query, source_sites.keys(),
                                  '/request')

class results(object):

    def GET(self):
        return render.results(None, "some dummy query",
                REF.source_sites.keys(), '/request')


# For serving using any wsgi server
wsgiapp = web.application(urls, globals()).wsgifunc()


if __name__ == '__main__':

    app = web.application(urls, globals())
    app.run()
