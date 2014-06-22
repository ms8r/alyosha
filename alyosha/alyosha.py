import requests
from lxml import html
import random

try:
    from urllib.parse import quote as url_quote
except ImportError:
    from urllib import quote as url_quote

try:
    from urllib import getproxies
except ImportError:
    from urllib.request import getproxies

SEARCH_URL = 'https://www.google.com/search?q=site:{0}%20{1}'

SOURCE_SITES = {
    'WSJ': 'wsj.com',
    'Bloomberg': 'bloomberg.com',
    'Huffington Post': 'huffingtonpost.com',
}

# user agents tuple taken from howdoi:
USER_AGENTS = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
               'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
               'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',)


# get_proxies shamelessly copied from howdoi:
def get_proxies():
    proxies = getproxies()
    filtered_proxies = {}
    for key, value in proxies.items():
        if key.startswith('http'):
            if not value.startswith('http'):
                filtered_proxies[key] = 'http://%s' % value
            else:
                filtered_proxies[key] = value
    return filtered_proxies

def site_results(site, query):
    """
    Returns lxml.etree with search results
    """
    result = requests.get(SEARCH_URL.format(site, url_quote(query)),
            headers={'User-Agent': random.choice(USER_AGENTS)},
            proxies=get_proxies())
    return html.fromstring(result.text)

def result_links(html, max_links=0):
    """
    Returns a list with (heading, url) tuples. If max_length > 0 at most
    max_length links will be returned
    """
    results = html.xpath('//h3[@class="r"]/a')
    if max_links:
        results = results[:min(len(results), max_links)]
    headings = [t.text_content() for t in results]
    urls = [t.attrib['href'].replace('/url?q=', '', 1) for t in results]
    return zip(headings, urls)

