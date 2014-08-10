# TODO: complete priority ranking
# tuple has: site, 'right'..'left' score (-1, 1), and priority/weight
# (heavy sinks to botom)
source_sites = {
        # right outfield:
        'Townhall': ('townhall.com', -0.9, 90),
        'FoxNews': ('foxnews.com', -0.7, 60),
        'The Weekly Standard': ('weeklystandard.com', -0.7, 50),
        'National Review': ('nationalreview.com', -0.6, 40),
        'EconLib': ('econlib.org', -0.6, 30),
        # right center:
        'Hoover Institution': ('hoover.org', -0.4, 30),
        # FT blocks with registration page
        # 'Financial Times': ('ft.com', -0.3, 25),
        'WSJ': ('wsj.com', -0.3, 20),
        'The Economist': ('economist.com', -0.3, 15),
        'Lawfare': ('lawfareblog.com', -0.2, 35),
        'Christian Science Monitor': ('csmonitor.com', -0.1, 5),
        'FiveThirtyEight': ('fivethirtyeight.com', -0.1, 15),
        # left center:
        'FactCheck': ('factcheck.org', 0.1, 50),
        'The Guardian': ('theguardian.com', 0.4, 25),
        'Der Spiegel': ('spiegel.de', 0.2, 30),
        'Brookings': ('brookings.edu', 0.2, 25),
        'The Atlantic': ('theatlantic.com', 0.2, 30),
        'Slate Magazine': ('slate.com', 0.4, 40),
        'Washington Post': ('washingtonpost.com', 0.2, 15),
        'New York Times': ('nytimes.com', 0.2, 15),
        # left outfield:
        'MNBC': ('msnbc.com', 0.6, 50),
        'Mother Jones': ('motherjones.com', 0.7, 30),
        'Huffington Post': ('huffingtonpost.com', 0.6, 45),
        'Daily Kos': ('dailykos.com', 0.7, 40),
        'The Nation': ('thenation.com', 0.9, 35),
}

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
    'issue', 'instance', 'just', 'need', 'best', 'better', 'worst', 'lot'
])


# maps NLTK POS tags onto WordNet tags for lemmatizing
# NOTE: not all tags are mapped; looks need to provide default via get
pos_map = {
        'JJ': 'a',
        'JJR': 'a',
        'JJRJR': 'a',
        'JJS': 'a',
        'JJ|RB': 'a',
        'JJ|VBG': 'a',
        'MD': 'v',
        'NN': 'n',
        'NNP': 'n',
        'NNPS': 'n',
        'NNS': 'n',
        'NN|NNS': 'n',
        'NN|SYM': 'n',
        'NN|VBG': 'n',
        'NP': 'n',
        'RB': 'r',
        'RBR': 'r',
        'RBS': 'r',
        'RB|RP': 'r',
        'RB|VBG': 'r',
        'VB': 'v',
        'VBD': 'v',
        'VBD|VBN': 'v',
        'VBG': 'v',
        'VBG|NN': 'v',
        'VBN': 'v',
        'VBP': 'v',
        'VBP|TO': 'v',
        'VBZ': 'v',
        'VP': 'v',
        'WRB': 'r'
}
