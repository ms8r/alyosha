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
        for source in al.SOURCE_SITES:
            html = al.site_results(al.SOURCE_SITES[source], qp.q)
            link_list = al.result_links(html, max_links=3)
            result[source] = link_list
        return render.index(result)

# if __name__ == '__main__':

app = web.application(urls, globals())
wsgiapp = app.wsgifunc()
# app.run()
