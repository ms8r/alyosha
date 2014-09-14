What is Thify?
==============

Think of Thify as a "counter recommendation engine" for news feeds and editorial content on the web.

There is an increasingly vibrant discussion about how the filtering algorithms behind news feeds reinforce existing biases and prejudices. As a recent [blog comment](http://mathbabe.org/2014/06/30/thanks-for-a-great-case-study-facebook/#comments) put it:

> There was a time when there were only three major news sources available to
> people on a daily basis and the news they provided was governed by a
> fairness doctrine. The segmentation that began with cable TV has
> increased with the internet... This segmentation leads to a situation
> where one’s world view is constantly reinforced making it harder for
> open-mindedness to prevail.

Thify tries to go against this trend of self-reinforcing world views. Given the URL of a news article, an editorial or a blog post on some subject, Thify will suggest additional articles on the same subject from sources *across the opinion spectrum*. It will show you content that you normally wouldn't look at, but that's substantial and relevant enough to have a debate about. Think of it as a *"if you like this you might not agree with this, but it's still worth reading"*. For more background on Thify please look at the [Why?](/thify-why) section.

Want to try it? It's dead simple. Say you've read an article in your favorite news or editorial source, and you ask yourself if there is more to that story than meets the eye. Simply take the article's URL and paste it into the entry field on the [Thify home page](/). Then hit the "I'll take it straight" button and Thify will crank away, analyzing the article at your URL and searching for content on the same subject from a range of sources. The result is presented as a spread across the traditional "left to right" political spectrum, with the best content matches ranking at the top. You may be surprised (or perhaps not) at how simply filling in some factual gaps can broaden or shift your view on a subject. For more details (including what's behind that "Check search specs" button on the home page) please check out the [How?](/thify-how) section.

A few comments on using Thify:

* Thify is in an "early draft" stage and probably feels a bit rough around the edges. It is not a commercial undertaking. It's a first shot at an idea that came out of an after dinner discussion. We're simply curious to see if we can turn this into something useful. If you have any comments or ideas please [let us now](/thify-contact).

* You get more and better results for topics that already have been in the news for a few days. More news sites will have picked up the topic and search engines will have had a chance to index it.

* I've found that [generating search terms](/thify-how) from your article works pretty well for classic editorial style content and for news articles that are at least 500 words long (the typical article is usually closer to 1,000 words). It can run into trouble with blog posts with plenty of colloquialisms because it may interpret those as [characteristic phrases](http://en.wikipedia.org/wiki/Collocation) even though they have no selectivity for a search engine.

What about privacy?
-------------------

Thify does not track any information about you or your searches. Neither does it use cookies to "mark" your computer in any way (in fact: it does not use cookies - period). Thify's results page includes some JavaScript but this does not collect any information about you or your browser.  The JavaScript is required to communicate search results back and forth between your browser and the server. It also updates the results page as search results come back from the server (a pure HTTP request would have to fetch everything in one go and risk timing out).
