source_sites = {
    'WSJ': ('wsj.com', -0.5),
    'The Guardian': ('theguardian.com', 0.5),
    'The Economist': ('economist.com', -0.5),
    'Der Spiegel': ('spiegel.de', 0.25),
    'Huffington Post': ('huffingtonpost.com', 0.5),
    'Lawfare': ('lawfareblog.com', -0.5),
    'Brookings': ('brookings.edu', 0.25),
    'Slate Magazine': ('slate.com', 0.5),
    'Washington Post': ('washingtonpost.com', 0.5),
    'National Review': ('nationalreview.com', -0.7),
    'Townhall': ('townhall.com', -1.0),
    'The Weekly Standard': ('weeklystandard.com', -0.7),
    'Daily Kos': ('dailykos.com', 0.7),
    'The Nation': ('thenation.com', 1.0),
    'FactCheck': ('factcheck.org', 0.0),
    'Vote Smart': ('votesmart.org', 0.0),
    'EconLib': ('econlib.org', -0.5),
    'Hoover Institution': ('hoover.org', -0.5),
    'Financial Times': ('ft.com', -0.4)
}

# user agents tuple taken from howdoi:
user_agents = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
               'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
               'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',)

# list of stop words taken from
# http://norm.al/2009/04/14/list-of-english-stop-words/
# augmented by capitalzed words
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
    'yourself', 'yourselves', 'A', 'About', 'Above', 'Across', 'After',
    'Afterwards', 'Again', 'Against', 'All', 'Almost', 'Alone', 'Along',
    'Already', 'Also', 'Although', 'Always', 'Am', 'Among', 'Amongst',
    'Amoungst', 'Amount', 'An', 'And', 'Another', 'Any', 'Anyhow', 'Anyone',
    'Anything', 'Anyway', 'Anywhere', 'Are', 'Around', 'As', 'At', 'Back',
    'Be', 'Became', 'Because', 'Become', 'Becomes', 'Becoming', 'Been',
    'Before', 'Beforehand', 'Behind', 'Being', 'Below', 'Beside', 'Besides',
    'Between', 'Beyond', 'Bill', 'Both', 'Bottom', 'But', 'By', 'Call',
    'Can', 'Cannot', 'Cant', 'Co', 'Computer', 'Con', 'Could', 'Couldnt',
    'Cry', 'De', 'Describe', 'Detail', 'Do', 'Done', 'Down', 'Due', 'During',
    'Each', 'Eg', 'Eight', 'Either', 'Eleven', 'Else', 'Elsewhere', 'Empty',
    'Enough', 'Etc', 'Even', 'Ever', 'Every', 'Everyone', 'Everything',
    'Everywhere', 'Except', 'Few', 'Fifteen', 'Fify', 'Fill', 'Find', 'Fire',
    'First', 'Five', 'For', 'Former', 'Formerly', 'Forty', 'Found', 'Four',
    'From', 'Front', 'Full', 'Further', 'Get', 'Give', 'Go', 'Had', 'Has',
    'Hasnt', 'Have', 'He', 'Hence', 'Her', 'Here', 'Hereafter', 'Hereby',
    'Herein', 'Hereupon', 'Hers', 'Herself', 'Him', 'Himself', 'His', 'How',
    'However', 'Hundred', 'I', 'Ie', 'If', 'In', 'Inc', 'Indeed', 'Interest',
    'Into', 'Is', 'It', 'Its', 'Itself', 'Keep', 'Last', 'Latter', 'Latterly',
    'Least', 'Less', 'Ltd', 'Made', 'Many', 'May', 'Me', 'Meanwhile',
    'Might', 'Mill', 'Mine', 'More', 'Moreover', 'Most', 'Mostly', 'Move',
    'Much', 'Must', 'My', 'Myself', 'Name', 'Namely', 'Neither', 'Never',
    'Nevertheless', 'Next', 'Nine', 'No', 'Nobody', 'None', 'Noone', 'Nor',
    'Not', 'Nothing', 'Now', 'Nowhere', 'Of', 'Off', 'Often', 'On', 'Once',
    'One', 'Only', 'Onto', 'Or', 'Other', 'Others', 'Otherwise', 'Our',
    'Ours', 'Ourselves', 'Out', 'Over', 'Own', 'Part', 'Per', 'Perhaps',
    'Please', 'Put', 'Rather', 'Re', 'Same', 'See', 'Seem', 'Seemed',
    'Seeming', 'Seems', 'Serious', 'Several', 'She', 'Should', 'Show',
    'Side', 'Since', 'Sincere', 'Six', 'Sixty', 'So', 'Some', 'Somehow',
    'Someone', 'Something', 'Sometime', 'Sometimes', 'Somewhere', 'Still',
    'Such', 'System', 'Take', 'Ten', 'Than', 'That', 'The', 'Their', 'Them',
    'Themselves', 'Then', 'Thence', 'There', 'Thereafter', 'Thereby',
    'Therefore', 'Therein', 'Thereupon', 'These', 'They', 'Thick', 'Thin',
    'Third', 'This', 'Those', 'Though', 'Three', 'Through', 'Throughout',
    'Thru', 'Thus', 'To', 'Together', 'Too', 'Top', 'Toward', 'Towards',
    'Twelve', 'Twenty', 'Two', 'Un', 'Under', 'Until', 'Up', 'Upon', 'Us',
    'Very', 'Via', 'Was', 'We', 'Well', 'Were', 'What', 'Whatever', 'When',
    'Whence', 'Whenever', 'Where', 'Whereafter', 'Whereas', 'Whereby',
    'Wherein', 'Whereupon', 'Wherever', 'Whether', 'Which', 'While',
    'Whither', 'Who', 'Whoever', 'Whole', 'Whom', 'Whose', 'Why', 'Will',
    'With', 'Within', 'Without', 'Would', 'Yet', 'You', 'Your', 'Yours',
    'Yourself', 'Yourselves',
    # added items based on early trial and error:
    'says', 'said', 'reported', 'Mr', 'Mrs', 'percent', 'including', 'end',
    'likely', 'unlikely'
])

# additional stop words that will only be culled from final search string, i.e.
# these words are still available to construct "search phrases"
late_kills = frozenset([
    'report', 'reported', 'reporting', 'reporting', 'face', 'facing',
    'Facing', 'Report', 'Reported', 'Face'
])
