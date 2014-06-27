import web
from web import form
import logging
import os.path
import sys
from alyosha import alyosha as al
from alyosha import reference as REF
# TODO: add threading for web requests

# Configure the logger
fmt = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
logging.basicConfig(filename='alyosha.log',
                    level=logging.DEBUG,
                    format=fmt)
logger = logging.getLogger(os.path.basename(__file__))
# file_handler = logging.FileHandler("alyosha.log")
# logger.addHandler(file_handler)
# console_handler = logging.StreamHandler(sys.stdout)
# logger.addHandler(console_handler)

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
                     form.Dropdown('MinCount', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
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
            logger.debug("ref_url=%s" % ref_url)
            scope = form['Scope'].value
            logger.debug("scope=%s" % scope)
            min_count = int(form['MinCount'].value)
            logger.debug("min_count=%d" % min_count)
            search_phrases, search_words = al.build_search_string(
                    ref_url, min_count=min_count, stop_words=REF.stop_words,
                    late_kills=REF.late_kills)
            logger.debug("search_phrases=%s" % search_phrases)
            logger.debug("search_words=%s" % search_words)
            query = search_phrases
            if scope == 'narrow':
                query = "%s+%s" % (query, search_words)
            source_sites = dict((key, value[0]) for (key, value) in
                                REF.source_sites.iteritems()
                                if abs(value[1]) <= 0.5)
            logger.debug("source_sites=%s" % source_sites.keys())
            result = al.full_results(source_sites, query, max_links=3)
            return render.results(result)

# if __name__ == '__main__':

app = web.application(urls, globals())
wsgiapp = app.wsgifunc()
# app.run()
