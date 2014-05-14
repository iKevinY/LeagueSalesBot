LeagueSalesBot
==============

LeagueSalesBot is a Reddit bot that posts League of Legends sales to [/r/LeagueOfLegends](http://www.reddit.com/r/LeagueOfLegends). It was inspired by a similar bot – [/u/FreeChampionsBot](http://www.reddit.com/user/FreeChampionsBot) – that posts the free champion rotation. This bot was programmed as an exercise in learning Python.

The bot is run via a cron job that is set to run between 7am and 8am on days where the new sales are posted. It searches the [sales page](http://beta.na.leagueoflegends.com/en/news/store/sales) on the main League of Legends website and checks whether a new post has appeared since the last time the bot successfully posted to the subreddit; if so, it scrapes that post for the sale data and formats and posts it to Reddit. If you're up in arms about the fact that I have used regular expressions to parse an HTML document rather than a library like [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/), more on that in a blog post I wrote about the coding of this bot.

There are a couple of files that this bot uses but aren't included in this Git repository: `lastrun.py` and `settings.py`. The former houses information about the last time the bot successfully posted, to keep track of what sale was most recent and also at what point in the skin sale prices rotation it is currently at.

```python
lastSaleEnd = "2013-08-12"
rotation = 3
```

`settings.py` contains information like the username and password of the bot, the user agent used, the subreddit the bot is posting to, and also what page the bot should search in order to check for a new sale. In addition, this file stores information about two-part champion names, exception skins, and the FAQ content.

```python
username = "LeagueSalesBot"
password = ""
userAgent = ""
subreddits = ["leagueoflegends", "LeagueSalesBot"]

# Dictionary containing regexes for champions with two-part names
twoParts = {".*? Miss Fortune": "Miss Fortune", ".*? Mundo": "Dr. Mundo"}

# Dictionary containing skins not in format "[skin name] [champion name]"
exceptSkins = {"AstroNautilus": "Nautilus"}

# Contains questions and answers for FAQ
faqArray = ()
```
