How does Thify work?
====================

It's pretty straight forward, for those who are interested.  When you submit an URL at the Thify home page you kick off the following process:

#. Thify fetches the web page at the URL you submitted and analyzes it to extract the text of the main article on the page (i.e. it ignores e.g. banner text, side bars, etc.).

#. Once it has the plain text of the article it uses a "[bag of words](http://en.wikipedia.org/wiki/Bag-of-words_model)" approach to find the words and phrases which are most characteristic for the text. To do so, it splits the text into a list of words, eliminates [stop words](http://en.wikipedia.org/wiki/Stop_words), [lemmatizes](http://en.wikipedia.org/wiki/Lemmatisation) the remaining words, tries to find [characteristic phrases](http://en.wikipedia.org/wiki/Collocation), and then takes the most frequent (lemmatized) words and phrases to construct a search string.

#. With this search string Thify then goes out and searches a number of news sites (~20 at this point) to find content on the same subject as your original article from other sources.

#. For each news site Thify will retrieve the full articles for the top *n* matches (as per their search rank; currently *n =* 3) and then compare each of these articles against your original article. It calculates a [cosine similarity](http://en.wikipedia.org/wiki/Cosine_similarity) score (a number between 0 and 1) that indicates how good a match an article from the search results is for your original article. "Match" here means addressing the same subject or issue as your article rather than expressing the same opinions (which it may or may not do). A score between 0.4 and 0.8 typically is a good match. If you go much lower you risk picking up pieces that address the key issues only on the periphery. With a score higher than 0.8 you increase the risk that you're simply looking at a rehash of your original article.

#. As Thify finds results that exceed a minimum match score and word count threshold it arranges them on a "left to right" scale, depending on their source. This is a pretty crude presentation (in a way it goes against one of Thify's [main intents](/thify_why)) but so far I haven't found a practical solution for a more differentiated representation of the results. Luckily (in this case), the editorial policies of most news sources are so narrow these days, that the simplistic "left to right" tagging still works pretty well. Please [let me know](/contact) if you have other ideas or suggestions!

That's it! If you click on the "Check search specs" button after entering your URL (rather than the "I'll take it straight" button) Thify will insert an additional step between (2.) and (3.) above. In this case it will show you a page with seach parameters it has derived from your original article, allowing you to adjust these before running the search. This might be useful if you get results that include either too many or too few matches - just go back, click on "Check search specs" and change, for example, the search string or the minimum match score.

<a name="thify-how-technology"></a>From a technology angle Thify is mostly built upon community driven open source projects:

* The main code is written in [Python](https://www.python.org/) and runs on a virtual linux box/shared server infrastructure ([Heroku](https://www.heroku.com/)).

* It uses [web.py](http://webpy.org/) as a web/application server (running behind [Gunicorn](http://gunicorn.org/)). Web.py is a brilliantly simple and lightweight web framwork, orginally developed by [Aaron Swartz](http://en.wikipedia.org/wiki/Aaron_Swartz).

* It uses [Redis](http://redis.io/) and [Vincent Driessen](http://nvie.com/about/)'s [RQ](http://python-rq.org/) to coordinate between the web server and background "worker" processes.

* It uses a Python version of [Goose](https://pypi.python.org/pypi/goose-extractor/) by [Xavier Grangier](https://github.com/grangier) for article extraction.

* For processing the extracted text, Thify uses [NLTK](www.nltk.org), the Python *Natural Language Toolkit* that has a strong following among linguistics enthusiasts and academics.

* And last but not least it uses [JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript) and [jQuery](http://jquery.com/) for some client side scripting that allows [asynchronous communication](http://en.wikipedia.org/wiki/Ajax_%28programming%29) with the server and dynamic/selective page updating.

The complete code for Thify can be found on [GitHub](https://github.com/ms8r/alyosha) under the project's original name, *[Alyosha](/thify-thanks)*.