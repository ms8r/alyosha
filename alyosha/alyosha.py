import requests
from goose import Goose
from lxml import html
from lxml.html.clean import Cleaner
import random
import re
from collections import counter

import lookup as LU

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
            headers={'User-Agent': random.choice(LU.USER_AGENTS)},
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

def build_search_string(ref_url, stop_words, *args, **kwargs):
    """
    Analyses the page at ref_url to returns a list of search terms, sorted in
    order of decreasing "importance".
    """
    article = Goose().extract(url)

def _simple_wc(word_list, max_items=0):
    """
    Returns a list of tuples (word, count).  max_items > 0 it will return at
    most a list with max_items.
    """
    pass

def _key_phrases(word_list, exclusions=None, max_length, max_items):
    pass

def _text_to_wordlist(text, stop_words):
    """
    Strips punctuation and stop words from text and returns the result as a
    list of words.
    """
    wlist = re.findall(r'\w+', plain_text.encode('utf-8'))
    return [w for w in wlist if w not in stop_words]
