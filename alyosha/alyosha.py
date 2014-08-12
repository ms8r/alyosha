import random
import re
import logging
from collections import Counter
import unicodedata
from datetime import datetime as dt
from datetime import date, timedelta
import time
import requests
from goose import Goose
from lxml import html
import numpy as np
import nltk
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures

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
    Will retrieve an URL, extract the main article and expose word/phrase lists
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
    stem_tops : list
        list of tuples with stemmed words from wlist and corresponding counts.

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
    # stemmer used to normalize words for article comparison
    stemmer = nltk.stem.SnowballStemmer('english')

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

        self.wlist = build_wlist(self.text)
        self.wcount = len(self.wlist)
        logging.debug("built %d word list for article \"%s\"" %
                (self.wcount, self.title))

        sl = [WebArticle.stemmer.stem(w) for w in self.wlist if w not in
              REF.stop_words.union(REF.late_kills) and len(w) > 2]
        self.stem_tops = Counter(sl).most_common()

    def search_string(self, num_terms=6, use_phrases=True,
            force_phrases=True):
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
        Will also assign the attributes `_lemmas', `_top_words`, and `_phrases`
        if these do not exist yet.
        """
        try:
            getattr(self, '_lemmas')
        except AttributeError:
            self._make_lemmas(min_char=2)
        try:
            getattr(self, '_top_words')
        except AttributeError:
            self._top_words = [w for w, c in
                    Counter(self._lemmas).most_common() if w not in
                    REF.late_kills]
        num_phrases = 0
        result = ""
        words = self._top_words
        if use_phrases:
            try:
                getattr(self, '_phrases')
            except AttributeError:
                self._find_phrases(num_phrases=2)
            if self._phrases:
                num_phrases = min(num_terms, len(self._phrases))
                encl = '"' if force_phrases else ''
                result = ' '.join(['%s%s%s' % (encl, p, encl)
                        for p in self._phrases[:num_phrases]])
                words = [w for w in words if w not in
                         ' '.join(self._phrases[:num_phrases])]
        num_words = min(num_terms - num_phrases, len(words))
        if num_words > 0:
            words = ' '.join([t for t in words[:num_words]])
            result = (result + ' ' + words).lstrip()

        return result

    def _find_phrases(self, num_phrases=None):
        try:
            getattr(self, '_lemmas')
        except AttributeError:
            self._make_lemmas()
        bcf = BigramCollocationFinder.from_words(self._lemmas)
        phrases = bcf.nbest(BigramAssocMeasures.likelihood_ratio, num_phrases)
        phrases = [' '.join(p) for p in phrases]
        self._phrases = [p for p in phrases if p in ' '.join(self.wlist)]

    def _make_lemmas(self, min_char=2):
        """
        Builds and stores lemmatized word list based on `self.wlist` and
        `REF.stop_words`, including only words with at least `min_char`
        characters. Result will be assigned to `self.lemmas`.
        """
        wnl = nltk.WordNetLemmatizer()
        tagged = [(w, REF.pos_map.get(t, 'n')) for w, t in
                  nltk.pos_tag(self.wlist) if w not in REF.stop_words and
                  len(w) >= min_char]
        self._lemmas = [wnl.lemmatize(*t) for t in tagged]

    def match_score(self, other, num_words=20):
        """
        Determine "content proximity" between two `WebArticle` as the cosine
        between the two object's vector space representation, including the
        `num_words` most frequent words from each object's `top_words`
        attribute.
        """
        num_words = min(num_words, len(self.stem_tops), len(other.stem_tops))
        da = dict(self.stem_tops[:num_words])
        db = dict(other.stem_tops[:num_words])
        voc = list(set(da.keys()) | set(db.keys()))
        a = np.array([[da.get(w, 0), db.get(w, 0)] for w in voc])
        return np.dot(a[:, 0], a[:, 1]) / (np.linalg.norm(a[:, 0]) *
                                           np.linalg.norm(a[:, 1]))


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
    search_str : str
        Search terms that were passed to constructor
    search_ops : list of tuples
        Search operator/vaue pairs that were passed to the constructor.
    search_kwds : dict
        Search operator/value pairs that were passed to the constructor.
        This may also include a keyword 'exact' which, if `True` will force
        ignoring search results for which Google automatically relaxed the
        search criteria (e.g. by ommitting quotes around phrases) because the
        original query yielded no results.
    alt_query : str
        Will be set to alternative search string proposed by Google if it
        cannot find results for the original query. `None` otherwise.
    """

    _search_url = 'https://www.google.com/search?q={0}'

    # XPath strings to grab search results
    _xp_resnum = '//div[@id="resultStats"]'
    _xp_altquery = '///div[@id="topstuff"]//div[@class="med"]'
    # NOTE: the `div[@class-"srg"] part excludes news items at the top of the
    # page (not stable); not an issue if request is sent with additional search
    # parameter (e.g. 'allintext')
    # NOTE: _prefix only required if more than 1 search result
    _prefix = '//div[@id="ires"]//div[@class="srg"]//li[@class="g"]'
    # `_xp_title` points to `a` tags containing titles as text content and urls
    # as `href` attributes: need multiple xp's to collect news items at top of
    # results and regular results
    _xp_title = [
            # _prefix + '//span[@class="tl"]/a[1]',
            '//h3[@class="r"]/a[1]'
    ]
    _xp_link = '//cite'
    _xp_desc = '//div[@class="s"]//span[@class="st"]'

    _resnum_re = re.compile(r'\D*([\d.,]+) result')
    # NOTE: date works only for US format 'mmm dd, yyyy'
    _date_re = re.compile(r'[a-zA-Z]+ \d{1,2}, \d{4,4}')

    def __init__(self, *search_ops, **search_kwds):
        """
        Calls `self.search()` if any of the arguments are specified.

        Arguments:
        ----------
        search_ops : list of 2-item tuples
            Each element must be a `(option, value)` combination with `option`
            being a search option recognized by Google. The can be used for
            options that can be repeated in a query (e.g. 'ext') and therefore
            don't fit into search_kwds.
        search_kwds : keyword argument dict
            Maps values to search opions. Specifically the constructor will
            look for keywords `search_str` (the string to be searched for) and
            `exact` (which, if `True` will ignore results for which Google
            automatically relaxes the query, e.g. by removing quotes around
            phrases. All other arguments will be interpreted as Google accepted
            search parameters/modifiers, mapped to their respective values.

        Raises:
        -------
        `EmptySearchResult` if no results can be found.
        `ResultParsingError` if results could not be parsed successfully.
        `PageRetrievalError` if
            - the web page cannot be retrieved by requests (e.g. timeout)
            - the GET request returns a non-OK status code
        """
        if not (search_ops or search_kwds):
            return
        search_str = search_kwds.get('search_str', '')
        if 'search_str' in search_kwds:
            del search_kwds['search_str']
        try:
            self.search(search_str, *search_ops, **search_kwds)
        except EmptySearchResult:
            raise
        except ResultParsingError:
            raise
        except PageRetrievalError:
            raise

    def search(self, search_str, *search_ops, **search_kwds):
        """
        Runs search and updates attributes.

        Arguments:
        ----------
        search_str : str
            Terms to be searched; will be url quoted before appending to url
        search_ops : list of tuples
            Search operators with associated values to be passed to google;
            examples: `site`, `link`, `daterange`, `-ext` (for filetype
            exclusion, e.g. `-ext:pdf`). `search_ops` can be used for
            oeprators that can appear in multiple instances (e.g. `-ext`).
        search_kwds : dict
            Search operators as key: value pairs. If `'allintext' in
            search_kwds` and `search_kwds['allintext'] == True`, the search
            terms will be prefixed by 'alltintext:'. Will specifically look for
            keyword `exact` which, if set to `True`, will ignore results if
            Google reports "No results" but relaxes search criteria (e.g. by
            ommitting quotes) to show alternative results.

            See also:
             - https://developers.google.com/search-appliance/documentation/614/xml_reference
             - https://support.google.com/websearch/answer/136861

        Returns:
        --------
        Number of search results reported by Google as int.

        Raises:
        -------
        `EmptySearchResult` if no results can be found.
        `ResultParsingError` if results could not be parsed successfully.
        `PageRetrievalError` if
            - the web page cannot be retrieved by requests (e.g. timeout)
            - the GET request returns a non-OK status code
        """
        # reset `res`, `resnum` and `relaxed_query` in case we get tripped
        # somewehere...
        self.res = self.resnum = self.alt_query = None
        # construct search string:
        exact = search_kwds.get('exact', False)
        if 'exact' in search_kwds:
            del search_kwds['exact']
        if 'allintext' in search_kwds:
            if search_kwds['allintext']:
                search_str = "allintext:%s" % search_str
            del search_kwds['allintext']
        ops = (["%s:%s" % (s[0], s[1]) for s in search_ops]
                + ["%s:%s" % (k, v) for (k, v) in search_kwds.iteritems()])
        query = ' '.join([search_str] + ops).lstrip()

        self.search_str = search_str
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

        # check if Google relaxed query:
        relaxed = parsed.xpath(GoogleSerp._xp_altquery)
        if relaxed:
            if not len(relaxed) == 2:
                logging.debug("Google seems to indicate alternative search "
                              "string for '%s'; unable to parse", query)
            elif relaxed[0].text_content().lower().startswith(
                    "no results found"):
                if exact:
                    self.resnum = 0
                    raise EmptySearchResult
                self.alt_query = relaxed[1].xpath('a')[0].text_content()

        pre = GoogleSerp._prefix if self.resnum > 1 else ''
        atags = []
        for xp in GoogleSerp._xp_title:
            atags += parsed.xpath(pre + xp)
        if not atags:
            logging.info("could not find any search results, "
                         "raising EmptySearchResult")
            raise EmptySearchResult

        titles = [a.text_content() for a in atags]
        urls = [a.attrib['href'] for a in atags]
        links = [c.text_content() for c in parsed.xpath(pre +
                                                        GoogleSerp._xp_link)]
        descs = [c.text_content() for c in parsed.xpath(pre +
                                                        GoogleSerp._xp_desc)]
        if not len(titles) == len(links) == len(descs) == len(urls):
            raise ResultParsingError
        dates = [GoogleSerp._date_re.match(d) for d in descs]
        for i, d in enumerate(dates):
            dates[i] = (dt.strptime(d.group(), '%b %d, %Y').date()
                        if d else None)
        self.res = [{'title': t, 'link': a, 'desc': x, 'url': u, 'date': d}
                for (t, a, x, u, d) in zip(titles, links, descs, urls, dates)]
        logging.debug("stored %d results in res dict" % len(titles))

        return self.resnum


class SiteResults(GoogleSerp):
    """
    Wrapper around GoogleSerp for site specific results

    Attributes:
    -----------
    Inherited from `GoogleSerp` (see doc string): `res`, `resnum`,
    `search_ops`, `search_kwds`, `search_str`

    site : str
        `site` argument that was passed to constructor
    back_days: int
        Number of days to search into past
    """
    exclude_formats = WebArticle.exclude_formats

    def __init__(self, site, *search_ops, **search_kwds):
        """
        Arguments:
        ----------
        site : str
            Site to which search is to be restricted (e.g. 'nytimes.com')
        search_ops : list of tuples
            Will be passed to `GoogleSerp` constructor; see
            `GoogleSerp.__init__` docstring.
        search_kwds : dict
            Will look for keyword `back_days` which, if present, will restrict
            the search results to documents that have been modified no longer
            than `back_days` days ago. Note that this will also exclude any
            documents which are lacking date information., The value mapped to
            `back_days` will be converted to a `daterange` search argument and
            `back_days` will be replaced by `daterange` in `search_kwds` All
            other keyword arguments will be passed straight to the `GoogleSerp`
            constructor. See `GoogleSerp.__init__` docstring for more info.
        """
        if not search_ops:
            search_ops = []
        search_ops += [('-ext', x) for x in SiteResults.exclude_formats]
        if not search_kwds:
            search_kwds = {}
        search_kwds['site'] = site
        back_days = search_kwds.get('back_days', None)
        if back_days:
            del search_kwds['back_days']
            now = date.today()
            then = now - timedelta(days=back_days)
            search_kwds['daterange'] = (then.isoformat() + '..' +
                                        now.isoformat())

        super(SiteResults, self).__init__(*search_ops, **search_kwds)

        self.site = site
        self.back_days = back_days


def build_wlist(raw_text):
    """
    Tokenizes raw text into word list.
    """
    pattern = r'''(?x)          # set flag to allow verbose regexps
              ([A-Z]\.)+        # abbreviations, e.g. U.S.A.
            | \w+(-\w+)*        # words with optional internal hyphens
            | \$?\d+(\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
    '''
    raw_text = unicodedata.normalize('NFKC', raw_text)
    raw_text = re.sub(ur'[\u2019]+', u'\'', raw_text)
    raw_text = re.sub(u'n\'t', u' not', raw_text)
    raw_text = re.sub(u'\'ve', u' have', raw_text)
    return [w.lower() for w in nltk.regexp_tokenize(raw_text, pattern)]


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


def best_matches(wa, sources, search_str, back_days=None,
        min_wc=0, min_match=0, num_matches=1, exact=False, delay=0,
         *search_ops, **search_kwds):
    """
    Returns a list of dicts with ranked search results for matches against
    `wa`.

    Arguments:
    ---------
    wa : WebArticle object
        Reference artticle against which to match results.
        WebArticle.match_score() will be used to evaluate content match.
    sources : sequence
        List of strings with sites to search. Sites will be searched in order
        until the list is exhausted or at most `num_matches` eligible matches
        have been found.
    search_str : str
        Query to be submitted; will be url quoted before appending to url
    search_ops : list of tuples
        Will be passed to `GoogleSerp` constructor; see
        `GoogleSerp.__init__` docstring.
    min_wc : int
        Minimum length (in number of words) for a match to be eligible.
    min_match : float [0..1]
        Minimum match score with `wa` for a search result to be eligible.
    num_matches : int
        Maximum number of matches to return.
    back_days : int
        If specified a `daterange' operator will be appended to the search
        string, restricting the search results to documents that have been
        modified no longer than `back_days` days ago. Note that this will
        also exclude any documents which are lacking date information.
    exact : Boolean
        If `True` will ignore search results in which Google relaxed the search
        query (e.g. by removing quotes from phrases).
    delay : number
        If `delay > 0` there will be a random delay between 0 and `delay`
        seconds in between calls to Google. This can be used to mitigate the
        risk of being blocked by Google.
    search_kwds : dict
        Will be passed to `GoogleSerp` constructor; see
        `GoogleSerp.__init__` docstring.

    Returns:
    --------
    List af dicts with search results ranked by content match. Dict
    keys are 'src', 'wc', 'score', 'title', 'url', 'link', 'desc'.
    """
    matches = []
    for src in sources:
        if len(matches) >= num_matches:
            break
        try:
            if delay > 0:
                time.sleep(delay * random.random())
            sr = SiteResults(src, search_str=search_str, back_days=back_days,
                    exact=exact, *search_ops, **search_kwds)
        except EmptySearchResult:
            logging.debug("SiteResults: empty search result for %s", src)
            continue
        except ResultParsingError:
            logging.debug("SiteResults: parsing error for %s", src)
            continue
        except PageRetrievalError:
            logging.debug("SiteResults: PageRetrievalError for %s", src)
            continue
        logging.debug("%s: found %d matches", src, sr.resnum)
        # NOTE: num_matches guesstimated (look at no more than two hits per
        # source)
        m = get_match(wa, sr, min_wc=min_wc, min_match=min_match,
                num_tries=2)
        if m:
            logging.debug("found match with score %.3f: %s from %s",
                    m['score'], m['title'], m['src'])
            matches.append(m)

    return sorted(matches, key=lambda k: k['score'], reverse=True)


def get_match(wa, sr, min_wc=0, min_match=0, num_tries=1):
    """
    Will try to retrieve a match from SiteResult object `sr` with a minimum
    length of `min_wc` words and a minimum content match of `min_match` against
    WebArticle object `wa`. Will try at most `num_tries` elements in `sr` to
    produce a match.

    Returns a dict with the match if found or None otherwise. Dict keys are
    'src', 'wc', 'score', 'title', 'url', 'link', 'desc'.
    """
    result = None
    stop = min(num_tries, len(sr.res))
    for r in sr.res[:stop]:
        url = r['url']
        title = r['title']
        if duplicate_urls(wa.url, url):
            logging.debug("Skipping %s, same as reference article", url)
            continue
        try:
            wb = WebArticle(url, REF.stop_words, REF.late_kills)
        except WebArticleError:
            logging.debug("%s: failed to extract article '%s'",
                    sr.site, title)
            continue
        if wb.wcount < min_wc:
            logging.debug("%s: discarding '%s', only %d words",
                          sr.site, title, wb.wcount)
            continue
        match_score = wa.match_score(wb, num_words=20)
        if match_score >= min_match:
            result = {'src': sr.site, 'wc': wb.wcount, 'score': match_score,
                    'title': title, 'url': url, 'link': r['link'], 'desc':
                    r['desc']}
            break
        else:
            logging.debug("dicarding \"%s\" from %s with score %.3f", title,
                    sr.site, match_score)

    return result


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
