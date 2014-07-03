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
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


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


class ArticleExtractionError(Exception):
    pass


class ArticleFormatError(Exception):
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

    Mehtods:
    --------
    search_string :
        Returns search string based on article content.
    match_score :
        Compares content to another WebArticle and provides a score tuple
        indicating how well the content matches.

    Raises:
    -------
    ArticleFormatError
        If path component of `url` points to non-html resource.
    ArticleExtractionError
        If goose fails to identify any article text in the page referenced by
        `url`.
    """

    # Weight given to phrases when calculating combined match score. The number
    # of common phrases will be multiplied by this weight and added to
    # nominator and denominator of the word match score. Not hugely scientific,
    # but seems to do the trick...
    phrase_match_score_weight = 4

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
        # check if url points to non-html:
        p_url = urlparse(ref_url)
        if p_url[2].endswith(('.pdf', '.jpg', '.gif', '.mp3', '.mp4')):
            raise ArticleFormatError

        if not late_kills:
            late_kills = []

        self.url = ref_url
        result = requests.get(ref_url, headers={'User-Agent':
                random.choice(REF.user_agents)}, proxies=_get_proxies())
        article = Goose().extract(raw_html=result.text)
        self.title = article.title
        self.text = article.cleaned_text
        if not self.text:
            logging.debug("could not extract article from %s" % ref_url)
            raise ArticleExtractionError

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
            wlist = [w.lower() for w in wlist if w not in stop_words]
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
                phrases += [t for t in terms]

        self.top_phrases = phrases

    def search_string(self, use_phrases=True, num_terms=6):
        """
        Returns a search string based on the articles top words and phrases.

        Arguments:
        ----------
        use_phrases : boolean
            If `False` only single words will be used in search string.
        num_terms : int
            Total number of terms (single words and phrases) to be includes in
            search string.

        Returns:
        --------
        A string with space separated search terms. Multiple word phrases will
        be enclosed in '"'.
        """
        if use_phrases:
            num_phrases = min(num_terms, len(self.top_phrases))
            result = ' '.join(['"%s"' % p
                    for p in self.top_phrases[:num_phrases]])
            top_words = self.pruned_top_words
        else:
            num_phrases = 0
            result = ""
            top_words = self.top_words
        num_words = min(num_terms - num_phrases, len(top_words))
        if num_words > 0:
            result += ' ' + ' '.join(top_words[:num_words])

        return result

    def match_score(self, other, num_words=20):
        """
        Determines the intersection of top words between self and other as a
        percentage of the number of top words considered.

        Arguments:
        ----------
        other : WebArticle object
            Article to compare self with.
        num_words : int
            Total number of single words to be includes in comparison.  Phrases
            will always be included at thir full length.

        Returns:
        --------
        Tuple (phrase overlap percentage, word overlap percentage, combined
        score) with all three values being between 0 and 1 inclusive.
        """
        p_base = max(len(self.top_phrases), len(other.top_phrases))
        if p_base > 0:
            p_intersect = set(self.top_phrases).intersection(
                    set(other.top_phrases))
            p_overlap = len(p_intersect) / float(p_base)
        else:
            p_intersect = set()
            p_overlap = 0.

        w_base = min(num_words, max(len(self.top_words), len(other.top_words)))
        w_min = min(num_words, len(self.top_words), len(other.top_words))
        if w_base > 0:
            w_intersect = set(self.top_words[:w_min]).intersection(
                    set(other.top_words[:w_min]))
            wi_len = len(w_intersect)
            pi_len = len(p_intersect)
            w_overlap = wi_len / float(w_base)
            m = WebArticle.phrase_match_score_weight
            combined_score = (wi_len + m * pi_len) / float(w_base +
                                                            m * pi_len)
        else:
            w_intersect = set()
            w_overlap = 0.
            combined_score = p_overlap

        return (p_overlap, w_overlap, combined_score)

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

    Raises:
    -------
    `EmptySearchResult` if no results can be found.
    `ResultParsingError` if results could not be parsed successfully.
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


def rank_matches(wa, sources):
    """
    Returns a list of dicts with ranked search results for matches against
    `article`.

    Arguments:
    ---------
    wa : WebArticle object
        Reference artticle against which to match results.
        WebArticle.match_score() will be used to evaluate content match.
    sources : dict
        Mapping of source names to urls
    """
    # minimum word count for matching article to make it into ranking:
    wc_threshold = 400

    query = wa.search_string()
    logging.debug("searching %s for '%s'", ' ,'.join(sources.keys()), query)
    res = {}
    for src, url in sources.iteritems():
        try:
            res[src] = SiteResults(url, query)
        except EmptySearchResult:
            logging.debug("empty search result for %s", src)
            continue
        except ResultParsingError:
            logging.debug("parsing error for %s", src)
        logging.debug("%s: found %d matches", url, res[src].resnum)

    # for now we just look at top match for each site:
    matches = []
    for src, sr in res.iteritems():
        url = sr.res[0]['url']
        title = sr.res[0]['title']
        if _duplicate_url(wa.url, url):
            logging.debug("Skipping %s, same as reference article", url)
            continue
        try:
            wb = WebArticle(url, REF.stop_words, REF.late_kills)
        except (ArticleExtractionError, ArticleFormatError):
            logging.debug("%s: failed to extract article '%s'",
                    src, title)
            continue
        if wb.wcount < wc_threshold:
            logging.debug("%s: discarding '%s', only %d words",
                          src, title, wb.wcount)
            continue
        __, __, match_score = wa.match_score(wb)
        matches.append({'src': src, 'wc': wb.wcount, 'score': match_score,
                'title': title, 'url': url, 'link': sr.res[0]['link'],
                'desc': sr.res[0]['desc']})

    return sorted(matches, key=lambda k: k['score'], reverse=True)


def _duplicate_url(url1, url2):
    p_url1 = urlparse(url1)
    p_url2 = urlparse(url2)
    # consider same if netloc and path match:
    if p_url1[1:3] == p_url2[1:3]:
        return True
    else:
        return False
