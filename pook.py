import web
from web import form
# import threading
from alyosha import alyosha as al
from alyosha import reference as REF

render = web.template.render('templates/')

urls = (
    '/', 'index'
)

urlForm = form.Form(form.Textbox('URL', form.notnull,
                        decription='Please enter the URL of an article/post '
                        'for which you would like to see alternative view '
                        'points'),
                    form.Radio('Scope', [('narrow', 'Narrow: uses phrases '
                        'and single words in query    '), ('broad',
                        'Broad: uses only phrases')], value='narrow'),
                     form.Dropdown('mincount', [2, 3, 4, 5, 6, 7, 8, 9],
                         value=5))


class index:

    def GET(self):
        form = urlForm()
        return render.index(form)

    def POST(self):
        form = urlForm()
        if not form.validates():
            return render.index(form)
        else:
            ref_url = form['URL'].value
            search_phrases, search_words = al.build_search_string(
                    ref_url, min_count=5, stop_words=REF.stop_words,
                    late_kills=REF.late_kills)
            query = "%s+%s" % (search_phrases, search_words)
            source_sites = dict((key, value[0]) for (key, value) in
                                REF.source_sites.iteritems()
                                if abs(value[1]) <= 0.7)
            result = al.full_results(source_sites, query, max_links=3)
            return render.results(result)

# if __name__ == '__main__':

app = web.application(urls, globals())
wsgiapp = app.wsgifunc()
#app.run()
