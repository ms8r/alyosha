import os
import web
import threading
from alyosha import alyosha as al

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
        result = al.full_results(al.SOURCE_SITES, qp.q, max_links=3)
        return render.index(result)

# if __name__ == '__main__':

app = web.application(urls, globals())
wsgiapp = app.wsgifunc()
# app.run()