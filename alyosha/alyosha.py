import requests
from goose import Goose
from lxml import html
from lxml.html.clean import Cleaner
import random
import re
from collections import Counter
import unicodedata

import reference as REF

try:
    from urllib.parse import quote as url_quote
except ImportError:
    from urllib import quote as url_quote

try:
    from urllib import getproxies
except ImportError:
    from urllib.request import getproxies

SEARCH_URL = 'https://www.google.com/search?q=site:{0}%20{1}'


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
            headers={'User-Agent': random.choice(REF.user_agents)},
            proxies=get_proxies())
    return html.fromstring(result.text)


def result_links(html, max_links=0):
    """
    Returns a list with (heading, url) tuples. If max_links > 0 at most
    max_links links will be returned
    """
    results = html.xpath('//h3[@class="r"]/a')
    if max_links:
        results = results[:min(len(results), max_links)]
    headings = [t.text_content() for t in results]
    urls = [t.attrib['href'].replace('/url?q=', '', 1) for t in results]
    return zip(headings, urls)


def fetch_teasers(urls, max_len=0):
    """
    Returns a list of article texts for the urls passed in `urls`.
    If `max_len > 0` at most `max_len` characters will be returned per teaser.
    """
    pass


def full_results(source_sites, query, max_links=0):
    """
    Returns a dict mapping resulting link_lists to source sites.

    Arguments:
    ---------
    source_sites : dict
        Mapping of source names to urls
    query : str
        Seach query string
    max_links : int
        If > 0 at most max_links results will be returned per source site.
    """
    result = {}
    for source in source_sites:
        html = site_results(source_sites[source], query)
        link_list = result_links(html, max_links)
        result[source] = link_list
    return result

def build_search_string(ref_url, stop_words=None):
    """
    Analyses the page at ref_url to returns a list of search terms, sorted in
    order of decreasing "importance".
    """
    result = requests.get(ref_url, headers={'User-Agent':
            random.choice(REF.user_agents)}, proxies=get_proxies())
    article = Goose().extract(raw_html=result.text)
    article.wlist = _build_wlist(article.cleaned_text, stop_words)

    return article


def _simple_wc(word_list, max_items=0):
    """
    Returns a list of tuples (word, count).  max_items > 0 it will return
    at most a list with max_items.
    """
    pass

def _key_phrases(word_list, exclusions=None, max_length=0, max_items=0):

    pass

def _build_wlist(plain_text, stop_words):
    plain_text = unicodedata.normalize(
            'NFKC', plain_text)
    if not stop_words:
        stop_words = []
    # strip punctuation to build word list excluding stop_list
    # TODO: deal with unicode apostrophes
    plain_text = re.sub(ur'[\u2019]+', u'\'', plain_text)
    plain_text = re.sub(ur'\'s', '', plain_text)
    plain_text = re.sub(ur'n\'t', '', plain_text)
    wlist = re.findall(ur'\w+', plain_text)
    return [w for w in wlist if w not in stop_words]

