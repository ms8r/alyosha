import requests
from goose import Goose
from lxml import html
import random
import re
import logging
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


# get_proxies shamrequestelessly copied from howdoi:
def _get_proxies():
    proxies = getproxies()
    filtered_proxies = {}
    for key, value in proxies.items():
        if key.startswith('http'):
            if not value.startswith('http'):
                filtered_proxies[key] = 'http://%s' % value
            else:
                filtered_proxies[key] = value
    return filtered_proxies


class EmptySearchResult(Exception):
    pass


class ResultParsingError(Exception):
    pass


class WebArticle(object):
    """
    Will retrieve aN URL, extract the main article and expose word/phrase lists
    and counts.

    Attributes:
    -----------
        url : str
            URL from which instance was constructed
        title : str
            Title of article as provided by Goose().extract()
        text : str
            Cleaned text of article
        wcount : int
            Number of words in cleaned text
        top_words : list
            Unique list of words, sorted by descending frequency
        top_phrases : list
            Unique list of multi-word phrases, sorted first by length of
            phrase, then by frequency
        phrase_overlaps : list
            List of single words in top_words that also appear as part of a
            phrase in top_phrases
        pruned_top_words : list
            top_words - phrase_overlaps, with original order of top_words
            retained
    """
    def __init__(self, ref_url, stop_words=None, late_kills=None):
        """
        Arguments:
        ----------
        ref_url : str
            Web page from which search terms are to be extracted
        stop_words : sequence or set
            List or set with common words to be excluded from search string.
            `stop_list` will be applied *before* any multiple word phrases are
            constructed.
        late_kills : sequence or set
            Like `stop_words` but the words in `late_kills` will only be
            eliminated from the search string *after* multiple word phrases
            have been constructed. This you can have a word like 'report'
            appear in the search string as part of a multiple word phrase
            ("OECD Report on Public Health") but not as a single word (which
            would have almost zero selectivity for a news article.
        """
        if not late_kills:
            late_kills = []

        self.url = ref_url
        result = requests.get(ref_url, headers={'User-Agent':
                random.choice(REF.user_agents)}, proxies=_get_proxies())
        article = Goose().extract(raw_html=result.text)
        self.title = article.title
        self.text = article.cleaned_text

        def build_wlist(raw_text, stop_words):
            raw_text = unicodedata.normalize(
                    'NFKC', raw_text)
            if not stop_words:
                stop_words = []
            # strip punctuation to build word list excluding stop_list
            raw_text = re.sub(ur'[\u2019]+', u'\'', raw_text)
            raw_text = re.sub(ur'\'s', '', raw_text)
            raw_text = re.sub(ur'n\'t', '', raw_text)
            wlist = re.findall(ur'\w+', raw_text)
            fwcount = len(wlist)
            wlist = [w for w in wlist if w not in stop_words]
            return wlist, fwcount

        wlist, self.wcount = build_wlist(self.text, stop_words)
        logging.debug("built %d word list for article \"%s\"" %
                (len(wlist), self.title))

        def phrase_counts(word_list, phrase_length=2, min_count=0):
            """
            Looks for multiple word phrases in text.  Takes `word_list` and
            checks for repeated occurence of multiple word phrases (e.g.
            'snowden files').  Returns a list of tuples (phrase, count), sorted
            by count in descending order.  `phrase_length` indicates how many
            words whould be in a phrase.  If `min_count` > 0 only phrases that
            occur at least `min_count` times will be returned.
            """
            assert 1 <= phrase_length <= len(word_list)
            cols = []
            for i in range(phrase_length):
                cols.append(word_list[i:])
            phrases = ([' '.join(c) for c in zip(*cols)])
            top_list = Counter(phrases).most_common()
            top_list = [t for t in top_list if t[1] >= min_count]
            return top_list

        # get word/phrase counts:
        min_count = max(2, int(round(len(wlist)/100.)))
        search_term_list = []
        for i in range(len(wlist)):
            # frequency threshold for phrases only:
            m = min_count if i > 0 else 0
            terms = phrase_counts(wlist, i + 1, m)
            if not terms:
                break
            search_term_list.append([t[0] for t in terms])

        # keep full word search list:
        self.top_words = [w for w in search_term_list[0]
                          if w not in late_kills]
        # eliminate redundancies:
        pruned_list = []
        for short_terms, long_terms in zip(search_term_list[:-1],
                                           search_term_list[1:]):
            short_terms = [t for t in short_terms
                           if not t in ' '.join(long_terms)]
            pruned_list.append(short_terms)
        pruned_list.append(search_term_list[-1])

        phrases = []
        # iterating in reverse order to put multiple word phrases first
        # NOTE: reversing no longer required
        first_element = len(pruned_list) - 1
        for i, terms in enumerate(reversed(pruned_list)):
            # kill weak single words and enclose multiple word phrases in
            # double quotes:
            if i == first_element:
                pass
                # pruned_words no longer stored - use pruned_top_words property
                # instead
                # pruned_words = [t for t in terms if t not in late_kills]
            else:
                phrases += ['"%s"' % t for t in terms]

        self.top_phrases = phrases

    @property
    def phrase_overlaps(self):
        """
        Provides a list of the words in self.top_words that are also part of a
        multi-word phrase in self.top_phrases
        """
        return [w for w in self.top_words if w in ' '.join(self.top_phrases)]

    @property
    def pruned_top_words(self):
        """
        Same as self.top_words - self.phrase_overlaps, retaining original order
        of self.top_words
        """
        excludes = self.phrase_overlaps
        return [w for w in self.top_words if not w in excludes]


class SiteResults(object):
    """
    Container for search results.

    Attributes:
    -----------
    res : List of dicts
        Keys are 'title', 'link', 'description', 'url'; res['link'] may miss
        the scheme (e.g. 'http://') and contain ellipses (...) whereas 'url'
        will always be a complete valid url.
    resnum : int
        Number of results as returned by Google
    site : str
        `site` argument that was passed to constructor
    query : str
        Search query that was passed to constructor

    Will raise `EmptySearchResult` if no results can be found.
    """

    _search_url = 'https://www.google.com/search?q=site:{0}%20{1}'

    # XPath strings to grab search results
    # NOTE: the `div[@class-"srg"] part excludes news items at the top of the
    # page (not stable)
    _prefix = '//div[@id="ires"]//div[@class="srg"]//li[@class="g"]'
    # `_xp_title` points to `a` tags containing titles as text content and urls
    # as `href` attributes: need multiple xp's to collect news items at top of
    # results and regular results
    _xp_title = [
            # _prefix + '//span[@class="tl"]/a[1]',
            _prefix + '//h3[@class="r"]/a[1]'
    ]
    _xp_link = _prefix + '//cite'
    _xp_desc = _prefix + '//div[@class="s"]//span[@class="st"]'
    _xp_resnum = '//div[@id="resultStats"]'

    _resnum_re = re.compile(r'\D*([\d.,]+) result')

    def __init__(self, site, query):
        """
        Arguments:
        ----------
        site : str
            Site to which search is to be restricted (e.g. 'nytimes.com')
        query : str
            Query ro be submitted; will be url quoted before appending to url
        """
        self.site = site
        self.query = query
        logging.debug("searching for '%s' on %s" % (query, site))

        result = requests.get(SiteResults._search_url.format(site,
                url_quote(query)), headers={'User-Agent':
                random.choice(REF.user_agents)}, proxies=_get_proxies())
        parsed = html.fromstring(result.text)

        try:
            s = parsed.xpath(SiteResults._xp_resnum)[0].text_content()
            m = SiteResults._resnum_re.match(s) if s else None
            self.resnum = int(m.group(1).replace(',', '').replace('.', ''))
        except IndexError:
            self.resnum = None
        logging.debug("google reports %s results" % self.resnum)

        atags = []
        for xp in SiteResults._xp_title:
            atags += parsed.xpath(xp)
        if not atags:
            logging.debug("could not find any search results, "
                          "raising EmptySearchResult")
            raise EmptySearchResult

        titles = [a.text_content() for a in atags]
        urls = [a.attrib['href'] for a in atags]
        links = [c.text_content() for c in parsed.xpath(SiteResults._xp_link)]
        descs = [c.text_content() for c in parsed.xpath(SiteResults._xp_desc)]
        if not len(titles) == len(links) == len(descs) == len(urls):
            raise ResultParsingError

        self.res = [{'title': t, 'link': a, 'desc': d, 'url': u}
                    for t, a, d, u in zip(titles, links, descs, urls)]
        logging.debug("stored %d results in res dict" % len(titles))


def full_results(source_sites, query):
    """
    Returns a dict with SiteResults objects mapped to their respective sources.

    Arguments:
    ---------
    source_sites : dict
        Mapping of source names to urls
    query : str
        Seach query string
    """
    res = {}
    for s in source_sites:
        try:
            res[s] = SiteResults(source_sites[s], query)
        except EmptySearchResult:
            continue
        except ResultParsingError:
            logging.warning("ResultParsingError on site %s with query %s"
                            % (s, query))
            continue

    return res
