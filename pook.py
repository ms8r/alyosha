import os
import web
import threading
from alyosha import alyosha as al
from alyosha import reference as REF

render = web.template.render('templates/')

urls = (
    '/', 'index'
)

class index:

    def GET(self):
        qp = web.input(q=None)
        result = {}
        if not qp.q:
            return render.index(result)
        source_sites = dict((key, value[0]) for (key, value) in
                            REF.source_sites.iteritems())
        result = al.full_results(source_sites, qp.q, max_links=3)
        return render.index(result)

if __name__ == '__main__':

    app = web.application(urls, globals())
    wsgiapp = app.wsgifunc()
    # app.run()
