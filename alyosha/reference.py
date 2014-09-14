from collections import namedtuple
from collections import OrderedDict

# tuple has: site, 'right'..'left' score (-1, 1), and priority/weight
# (heavy sinks to botom)
SrcEntry = namedtuple('SrcEntry', ['site', 'specVal', 'weight', 'label', 'id'])

# source grouping: intervals below are open on the left
src_cats = OrderedDict([
        ('left', (0.5, 1.0)),
        ('center', (-0.5, 0.5)),
        ('right', (-1.0, -0.5)),
])

source_sites = [
        # right outfield:
        SrcEntry('townhall.com', -0.9, 60, 'Townhall', 'townhall'),
        SrcEntry('foxnews.com', -0.7, 50, 'FoxNews', 'foxnews'),
        SrcEntry('weeklystandard.com', -0.7, 45, 'The Weekly Standard', 'weeklystandard'),
        SrcEntry('nationalreview.com', -0.6, 40, 'National Review', 'nationalreview'),
        SrcEntry('econlib.org', -0.6, 30, 'EconLib', 'econlib'),
        # right center:
        SrcEntry('hoover.org', -0.4, 55, 'Hoover Institution', 'hoover'),
        # FT blocks with registration page
        # SrcEntry('ft.com', -0.3, 25, # 'Financial Times', 'ft.com'),
        SrcEntry('wsj.com', -0.3, 55, 'WSJ', 'wsj'),
        SrcEntry('economist.com', -0.3, 15, 'The Economist', 'economist'),
        SrcEntry('lawfareblog.com', -0.2, 55, 'Lawfare', 'lawfareblog'),
        SrcEntry('csmonitor.com', -0.1, 5, 'Christian Science Monitor', 'csmonitor'),
        SrcEntry('fivethirtyeight.com', -0.1, 55, 'FiveThirtyEight', 'fivethirtyeight'),
        # left center:
        SrcEntry('factcheck.org', 0.1, 60, 'FactCheck', 'factcheck'),
        SrcEntry('theguardian.com', 0.4, 25, 'The Guardian', 'theguardian'),
        SrcEntry('spiegel.de', 0.2, 55, 'Der Spiegel', 'spiegel'),
        SrcEntry('brookings.edu', 0.2, 25, 'Brookings', 'brookings'),
        SrcEntry('theatlantic.com', 0.2, 30, 'The Atlantic', 'theatlantic'),
        SrcEntry('slate.com', 0.4, 40, 'Slate Magazine', 'slate'),
        SrcEntry('washingtonpost.com', 0.2, 15, 'Washington Post', 'washingtonpost'),
        SrcEntry('nytimes.com', 0.2, 15, 'New York Times', 'nytimes'),
        # left outfield:
        SrcEntry('msnbc.com', 0.6, 55, 'MNBC', 'msnbc'),
        SrcEntry('motherjones.com', 0.7, 30, 'Mother Jones', 'motherjones'),
        SrcEntry('huffingtonpost.com', 0.6, 45, 'Huffington Post', 'huffingtonpost'),
        SrcEntry('dailykos.com', 0.7, 40, 'Daily Kos', 'dailykos'),
        SrcEntry('thenation.com', 0.9, 35, 'The Nation', 'thenation'),
]

def cat_sources(category, max_weight=100, sites_only=False, sort_by='weight',
        reverse=False, mask=None):
    """
    Returns a list of sources for `category`, including only itmes with a
    quality weight <= `max_weight`.

    Arguments:
    ----------
    category : str
        One of 'right', 'center', 'left'.
    max_weight : number
        Quality rating cut-off; only items with a quality weight <=
        `max_weight` will be included in the result.
    sites_only : boolean
        If `True` the returned list will only consist of the sources' site
        strings. Otherwise the full `SrcEntry` tuples will be included in the
        list.
    sort_by : str
        Attribute by which sort result.
    reverse : boolean
        Sort order will be reversed if `True` (i.e. descending).
    mask : boolean list
        If specified, only sources for which the corresponding item in mask
        evaluates to `True` will be included in the result.

    Returns:
    --------
    List of `SrcEntry` named tuples if `urls_only==False`, list of `site`strings
    otherwise.
    """
    if not mask:
        mask = [True] * len(source_sites)
    lb, ub = src_cats[category]
    sources = [t for m, t in zip(mask, source_sites) if m and
               (lb <= t.specVal < ub) and t.weight <= max_weight]
    sources.sort(key=lambda k: getattr(k, sort_by), reverse=reverse)
    if sites_only:
        sources = [t.site for t in sources]

    return sources


# user agents tuple taken from howdoi:
user_agents = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
               'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
               'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',)

# list of stop words taken from
# http://norm.al/2009/04/14/list-of-english-stop-words
stop_words = frozenset([
    'a', 'about', 'above', 'across', 'after', 'afterwards', 'again',
    'against', 'all', 'almost', 'alone', 'along', 'already', 'also',
    'although', 'always', 'am', 'among', 'amongst', 'amoungst', 'amount',
    'an', 'and', 'another', 'any', 'anyhow', 'anyone', 'anything', 'anyway',
    'anywhere', 'are', 'around', 'as', 'at', 'back', 'be', 'became',
    'because', 'become', 'becomes', 'becoming', 'been', 'before',
    'beforehand', 'behind', 'being', 'below', 'beside', 'besides', 'between',
    'beyond', 'bill', 'both', 'bottom', 'but', 'by', 'call', 'can', 'cannot',
    'cant', 'co', 'computer', 'con', 'could', 'couldnt', 'cry', 'de',
    'describe', 'detail', 'do', 'done', 'down', 'due', 'during', 'each',
    'eg', 'eight', 'either', 'eleven', 'else', 'elsewhere', 'empty',
    'enough', 'etc', 'even', 'ever', 'every', 'everyone', 'everything',
    'everywhere', 'except', 'few', 'fifteen', 'fify', 'fill', 'find', 'fire',
    'first', 'five', 'for', 'former', 'formerly', 'forty', 'found', 'four',
    'from', 'front', 'full', 'further', 'get', 'give', 'go', 'had', 'has',
    'hasnt', 'have', 'he', 'hence', 'her', 'here', 'hereafter', 'hereby',
    'herein', 'hereupon', 'hers', 'herself', 'him', 'himself', 'his', 'how',
    'however', 'hundred', 'i', 'ie', 'if', 'in', 'inc', 'indeed', 'interest',
    'into', 'is', 'it', 'its', 'itself', 'keep', 'last', 'latter', 'latterly',
    'least', 'less', 'ltd', 'made', 'many', 'may', 'me', 'meanwhile',
    'might', 'mill', 'mine', 'more', 'moreover', 'most', 'mostly', 'move',
    'much', 'must', 'my', 'myself', 'name', 'namely', 'neither', 'never',
    'nevertheless', 'next', 'nine', 'no', 'nobody', 'none', 'noone', 'nor',
    'not', 'nothing', 'now', 'nowhere', 'of', 'off', 'often', 'on', 'once',
    'one', 'only', 'onto', 'or', 'other', 'others', 'otherwise', 'our',
    'ours', 'ourselves', 'out', 'over', 'own', 'part', 'per', 'perhaps',
    'please', 'put', 'rather', 're', 'same', 'see', 'seem', 'seemed',
    'seeming', 'seems', 'serious', 'several', 'she', 'should', 'show',
    'side', 'since', 'sincere', 'six', 'sixty', 'so', 'some', 'somehow',
    'someone', 'something', 'sometime', 'sometimes', 'somewhere', 'still',
    'such', 'system', 'take', 'ten', 'than', 'that', 'the', 'their', 'them',
    'themselves', 'then', 'thence', 'there', 'thereafter', 'thereby',
    'therefore', 'therein', 'thereupon', 'these', 'they', 'thick', 'thin',
    'third', 'this', 'those', 'though', 'three', 'through', 'throughout',
    'thru', 'thus', 'to', 'together', 'too', 'top', 'toward', 'towards',
    'twelve', 'twenty', 'two', 'un', 'under', 'until', 'up', 'upon', 'us',
    'very', 'via', 'was', 'we', 'well', 'were', 'what', 'whatever', 'when',
    'whence', 'whenever', 'where', 'whereafter', 'whereas', 'whereby',
    'wherein', 'whereupon', 'wherever', 'whether', 'which', 'while',
    'whither', 'who', 'whoever', 'whole', 'whom', 'whose', 'why', 'will',
    'with', 'within', 'without', 'would', 'yet', 'you', 'your', 'yours',
    'yourself', 'yourselves',
    # added items based on early trial and error:
    'says', 'said', 'reported', 'mr', 'mrs', 'percent', 'including', 'end',
    'likely', 'unlikely', 'wrote', 'does'
])

# additional stop words that will only be culled from final search string, i.e.
# these words are still available to construct "search phrases"
late_kills = frozenset([
    'report', 'reported', 'reporting', 'face', 'facing', 'like', 'read',
    'reads', 'different', 'think', 'thought', 'people', 'big', 'new', 'issues',
    'issue', 'instance', 'just', 'need', 'best', 'better', 'worst', 'lot',
    'day', 'use',
])

