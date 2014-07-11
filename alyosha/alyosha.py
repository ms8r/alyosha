import requests
from goose import Goose
from lxml import html
import random
import re
import logging
from collections import Counter
import unicodedata
from datetime import date, timedelta
import nltk

import reference as REF

nltk.data.path.append('./nltk_data/')

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


# get_proxies shamelessly copied from howdoi:
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


class WebArticleError(Exception):
    pass


class ArticleExtractionError(WebArticleError):
    pass


class ArticleFormatError(WebArticleError):
    pass


class InvalidUrlError(WebArticleError):
    pass


class PageRetrievalError(WebArticleError):
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
    wlist : list
        `text` as list of lower case strings without punctuation marks.
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
    The following exceptions all inherit from WebArticleError:

    ArticleFormatError
        If path component of `url` points to non-html resource.
    ArticleExtractionError
        If goose fails to identify any article text in the page referenced by
        `url`.
    PageRetrievalError
        Raised if
            - the web page cannot be retrieved by requests (e.g. timeout)
            - the GET request returns a non-OK status code
    """
    # file extensions to be excluded (will raise InvalidUrlError):
    exclude_formats = ['pdf', 'doc', 'mp3', 'mp4']
    # Weight given to phrases when calculating combined match score. The number
    # of common phrases will be multiplied by this weight and added to
    # nominator and denominator of the word match score. Not hugely scientific,
    # but seems to do the trick...
    _phrase_match_score_weight = 4

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
            have been constructed. Thus you can have a word like 'report'
            appear in the search string as part of a multiple word phrase
            ("OECD Report on Public Health") but not as a single word (which
            would have almost zero selectivity for a news article).
        """
        if not valid_url(ref_url):
            raise InvalidUrlError(ref_url)
        # check if url points to non-html:
        p_url = urlparse(ref_url)
        if p_url[2].endswith(tuple(WebArticle.exclude_formats)):
            raise ArticleFormatError(p_url[2])

        if not late_kills:
            late_kills = []

        self.url = ref_url
        try:
            result = requests.get(ref_url, headers={'User-Agent':
                    random.choice(REF.user_agents)}, proxies=_get_proxies())
        except requests.exceptions.RequestException:
            raise PageRetrievalError
        if not result.status_code == requests.codes.ok:
            raise PageRetrievalError

        article = Goose().extract(raw_html=result.text)
        self.title = article.title
        self.text = article.cleaned_text
        if not self.text:
            logging.debug("could not extract article from %s" % ref_url)
            raise ArticleExtractionError(ref_url)

        def build_wlist(raw_text):
            raw_text = unicodedata.normalize(
                    'NFKC', raw_text)
            # strip punctuation to build word list excluding stop_list
            raw_text = re.sub(ur'[\u2019]+', u'\'', raw_text)
            raw_text = re.sub(ur'\'s', '', raw_text)
            raw_text = re.sub(ur'n\'t', '', raw_text)
            result = [w.lower() for w in re.findall(ur'\w+', raw_text)]
            short_num = re.compile(r'0*\d$')
            return [w for w in result if not w in ['m', 've', 't', 'd'] and
                    not short_num.match(w)]

        self.wlist = build_wlist(self.text)
        self.wcount = len(self.wlist)
        logging.debug("built %d word list for article \"%s\"" %
                (self.wcount, self.title))
        no_stop_wlist = [w for w in self.wlist if w not in stop_words]

        def phrase_counts(word_list, phrase_length=2, min_count=0):
            """
            Looks for multiple word phrases in text.  Takes `word_list` and
            checks for repeated occurence of multiple word phrases (e.g.
            'snowden files').  Returns a list of tuples (phrase, count), sorted
            by count in descending order.  `phrase_length` indicates how many
            words should be in a phrase. Only phrases with at least `min_count`
            occurences in `word_list` will be included in the result.
            """
            assert 1 <= phrase_length <= len(word_list)
            cols = []
            for i in range(phrase_length):
                cols.append(word_list[i:])
            phrases = ([' '.join(c) for c in zip(*cols)])
            result = Counter(phrases).most_common()
            return [r for r in result if r[1] >= min_count]

        # get word/phrase counts:
        wnl = nltk.WordNetLemmatizer()
        lemma_count = {}
        for w, c in Counter(no_stop_wlist).most_common():
            lemma = wnl.lemmatize(w)
            lemma_count[lemma] = c + lemma_count.setdefault(lemma, 0)
        lemmatized = [(w, c) for (w, c) in lemma_count.iteritems()]
        lemmatized.sort(key=lambda t: t[1], reverse=True)
        self.top_words = [w for w in lemmatized if w[0] not in late_kills]
        # TODO: establish count threshold for phrases as average of top n word
        # counts:
        n = min(10, len(self.top_words))
        min_count = (sum([c[1] for c in self.top_words[:n]]) / float(n)
                if n > 0 else float('nan'))
        min_count = max(3, int(round(min_count / 2.5)))
        search_term_list = [lemmatized]
        for i in range(1, len(no_stop_wlist)):
            terms = phrase_counts(no_stop_wlist, i + 1, min_count=min_count)
            if not terms:
                break
            # only keep phrases that also appear as such in pre-stop-word-kill
            # text:
            terms = [t for t in terms if t[0] in ' '.join(self.wlist)]
            if terms:
                search_term_list.append(terms)

        # eliminate redundancies (word/shorter phrase contained in longer
        # phrase):
        pruned_list = []
        for short_terms, long_terms in zip(search_term_list[:-1],
                                           search_term_list[1:]):
            short_terms = [s for s in short_terms if not s[0] in
                           ' '.join([t[0] for t in long_terms])]
            pruned_list.append(short_terms)
        pruned_list.append(search_term_list[-1])

        phrases = []
        # iterating in reverse order to put multiple word phrases first
        # NOTE: reversing no longer required
        first_element = len(pruned_list) - 1
        for i, terms in enumerate(reversed(pruned_list)):
            if i == first_element:
                pass
            else:
                phrases += [t for t in terms]

        self.top_phrases = phrases

    def search_string(self, num_terms=6, use_phrases=True, force_phrases=True):
        """
        Returns a search string based on the articles top words and phrases.

        Arguments:
        ----------
        num_terms : int
            Total number of terms (single words and phrases) to be includes in
            search string.
        use_phrases : boolean
            If `False` only single words will be used in search string.
        force_phrases : boolean
            If `True`, phrases will be included in quotes.

        Returns:
        --------
        A string with space separated search terms. Multiple word phrases will
        be enclosed in '"' if `force_phrases was set to `True`.
        """
        if use_phrases:
            num_phrases = min(num_terms, len(self.top_phrases))
            encl = '"' if force_phrases else ''
            result = ' '.join(['%s%s%s' % (encl, p[0], encl)
                    for p in self.top_phrases[:num_phrases]])
            top_words = self.pruned_top_words
        else:
            num_phrases = 0
            result = ""
            top_words = self.top_words
        num_words = min(num_terms - num_phrases, len(top_words))
        if num_words > 0:
            words = ' '.join([t[0] for t in top_words[:num_words]])
            result = (result + ' ' + words).lstrip()

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
        # TODO: calculate as dot product between word vectors
        p_base = max(len(self.top_phrases), len(other.top_phrases))
        if p_base > 0:
            p1 = [p[0] for p in self.top_phrases]
            p_intersect = set([p[0] for p in self.top_phrases]).intersection(
                    set([p[0] for p in other.top_phrases]))
            p_overlap = len(p_intersect) / float(p_base)
        else:
            p_intersect = set()
            p_overlap = 0.

        w_base = min(num_words, max(len(self.top_words), len(other.top_words)))
        w_min = min(num_words, len(self.top_words), len(other.top_words))
        if w_base > 0:
            w_intersect = set([w for w in self.top_words[:w_min]]).intersection(
                    set([w for w in other.top_words[:w_min]]))
            wi_len = len(w_intersect)
            pi_len = len(p_intersect)
            w_overlap = wi_len / float(w_base)
            m = WebArticle._phrase_match_score_weight
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
        phrases = [p[0] for p in self.top_phrases]
        return [w for w in self.top_words if w[0] in ' '.join(phrases)]

    @property
    def pruned_top_words(self):
        """
        Same as self.top_words - self.phrase_overlaps, retaining original order
        of self.top_words
        """
        excludes = self.phrase_overlaps
        return [w for w in self.top_words if not w in excludes]


class GoogleSerp(object):
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
    search_terms : str
        Search terms that were passed to constructor
    search_ops : dict
        Dictionary with the search operators that were passed to the
        constructor.
    """

    _search_url = 'https://www.google.com/search?q={0}'

    # XPath strings to grab search results
    # NOTE: the `div[@class-"srg"] part excludes news items at the top of the
    # page (not stable)
    # NOTE: news items not an issue if request is sent with additional search
    # parameter (e.g. 'allintext')
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
    # TODO: catch single search result cases and scrape differently

    _resnum_re = re.compile(r'\D*([\d.,]+) result')

    def __init__(self, search_terms, *search_ops, **search_kwds):
        """
        Arguments:
        ----------
        search_terms : str
            Terms to be searched; will be url quoted before appending to url
        allintext: boolean
            If True, `search_terms` will be prefixed by `allintext:`
        search_ops : list of tuples
            Search operators with associated values to be passed to google;
            examples: `site`, `link`, `daterenge`, `-ext` (for filetype
            exclusion, e.g. `-ext:pdf`). `search_ops` can be used for
            oeprators that can appear in multiple instances (e.g. `-ext`).
        search_kwds : dict
            Search operators as key: value pairs. If `'allintext' in
            search_kwds` and `search_kwds['allintext'] == True`, the search
            terms will be prefixed by 'alltintext:'
            See also:
             - https://developers.google.com/search-appliance/documentation/614/xml_reference
             - https://support.google.com/websearch/answer/136861

        Raises:
        -------
        `EmptySearchResult` if no results can be found.
        `ResultParsingError` if results could not be parsed successfully.
        `PageRetrievalError` if
            - the web page cannot be retrieved by requests (e.g. timeout)
            - the GET request returns a non-OK status code
        """
        # construct search string:
        if 'allintext' in search_kwds:
            if search_kwds['allintext']:
                search_terms = "allintext:%s" % search_terms
            del search_kwds['allintext']
        ops = (["%s:%s" % (s[0], s[1]) for s in search_ops]
                + ["%s:%s" % (k, v) for (k, v) in search_kwds.iteritems()])
        query = ' '.join([search_terms] + ops).lstrip()

        self.search_terms = search_terms
        self.search_ops = search_ops
        self.search_kwds = search_kwds
        logging.debug("searching for '%s'" % query)

        try:
            result = requests.get(GoogleSerp._search_url.format(
                    url_quote(query)), headers={'User-Agent':
                    random.choice(REF.user_agents)}, proxies=_get_proxies())
        except requests.exceptions.RequestException:
            raise PageRetrievalError
        if not result.status_code == requests.codes.ok:
            raise PageRetrievalError
        parsed = html.fromstring(result.text)

        try:
            s = parsed.xpath(GoogleSerp._xp_resnum)[0].text_content()
            m = GoogleSerp._resnum_re.match(s) if s else None
            self.resnum = int(m.group(1).replace(',', '').replace('.', ''))
        except IndexError:
            self.resnum = None
        logging.debug("google reports %s results" % self.resnum)

        atags = []
        for xp in GoogleSerp._xp_title:
            atags += parsed.xpath(xp)
        if not atags:
            logging.info("could not find any search results, "
                          "raising EmptySearchResult")
            raise EmptySearchResult

        titles = [a.text_content() for a in atags]
        urls = [a.attrib['href'] for a in atags]
        links = [c.text_content() for c in parsed.xpath(GoogleSerp._xp_link)]
        descs = [c.text_content() for c in parsed.xpath(GoogleSerp._xp_desc)]
        if not len(titles) == len(links) == len(descs) == len(urls):
            raise ResultParsingError

        self.res = [{'title': t, 'link': a, 'desc': d, 'url': u}
                    for t, a, d, u in zip(titles, links, descs, urls)]
        logging.debug("stored %d results in res dict" % len(titles))


class SiteResults(GoogleSerp):
    """
    Wrapper around GoogleSerp for site specific results

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
    back_days: int
        Numbder days to search into past
    """
    exclude_formats = WebArticle.exclude_formats

    def __init__(self, site, query, back_days=None):
        """
        Arguments:
        ----------
        site : str
            Site to which search is to be restricted (e.g. 'nytimes.com')
        query : str
            Query ro be submitted; will be url quoted before appending to url
        back_days : int
            If specified a `daterange' operator will be appended to the search
            string, restricting the search results to documents that have been
            modified no longer than `back_days` days ago. Note that this will
            also exclude any documents which are lacking date information.
        """
        search_ops = [('-ext', x) for x in SiteResults.exclude_formats]
        search_ops.append(('site', site))
        if back_days:
            now = date.today()
            then = now - timedelta(days=back_days)
            search_ops.append(('daterange', then.isoformat() + '..' +
                              now.isoformat()))

        super(SiteResults, self).__init__(query, *search_ops, allintext=True)

        self.site = site
        self.query = query
        self.back_days = back_days


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
    back_days = 90

    query = wa.search_string()
    logging.debug("searching %s for '%s'", ' ,'.join(sources.keys()), query)
    res = {}
    for src, url in sources.iteritems():
        try:
            res[src] = SiteResults(url, query, back_days=back_days)
        except EmptySearchResult:
            logging.debug("SiteResult: empty search result for %s", src)
            continue
        except ResultParsingError:
            logging.debug("SiteResult: parsing error for %s", src)
            continue
        except PageRetrievalError:
            logging.debug("SiteResult: PageRetrievalError for %s", src)
            continue

        logging.debug("%s: found %d matches", url, res[src].resnum)

    # for now we just look at top match for each site:
    # TODO: change to allow looking at top n matches
    matches = []
    for src, sr in res.iteritems():
        url = sr.res[0]['url']
        title = sr.res[0]['title']
        if duplicate_urls(wa.url, url):
            logging.debug("Skipping %s, same as reference article", url)
            continue
        try:
            wb = WebArticle(url, REF.stop_words, REF.late_kills)
        except WebArticleError:
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


def duplicate_urls(url1, url2):
    p_url1 = urlparse(url1)
    p_url2 = urlparse(url2)
    # consider same if netloc and path match:
    if p_url1[1:3] == p_url2[1:3]:
        return True
    else:
        return False


def valid_url(url):
    """
    Returns None if no valid url can be derived from url, else a (structurally)
    valid url.
    """
    p_url = urlparse(url)
    # must at least have netloc:
    if not p_url[1]:
        return None
    # check if scheme is present:
    if not p_url[0]:
        url = 'http://' + url
    return url
