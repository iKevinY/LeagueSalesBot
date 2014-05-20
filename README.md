LeagueSalesBot
==============

LeagueSalesBot is a Reddit bot that posts League of Legends champion and skin sales to [/r/leagueoflegends](http://www.reddit.com/r/leagueoflegends). It was inspired by a similar bot – [/u/FreeChampionsBot](http://www.reddit.com/user/FreeChampionsBot) – that posts the free champion rotation. This bot was programmed as an exercise in learning Python.

The bot is run via cron at approximately 7:00 Pacific Time on Mondays and Thursdays (when the new sales are posted). It searches the [sales page](http://na.leagueoflegends.com/en/news/store/sales) on the main League of Legends website and checks whether a new post has appeared since the last time the bot successfully posted to the subreddit; if so, it scrapes that post for the sale data and formats and posts it to Reddit.

There are a couple of files that this bot uses but are not included in this Git repository: `lastrun.py` and `settings.py`. The former houses information about the last time the bot successfully posted, to keep track of what sale was most recent and also at what point in the skin sale prices rotation it is currently at.

```python
lastSaleEnd = "2013-08-12"
lastRotation = 3
```

`settings.py` contains information like the username and password of the bot, the user agent used, the subreddit the bot is posting to, and also what page the bot should search in order to check for a new sale. In addition, this file stores information about two-part champion names, exception skins, and the FAQ content.

```python
username = "LeagueSalesBot"
password = ""
userAgent = ""

subreddits = (
    (subreddit, isLinkPost),
    ...
)

# Dictionary containing regexes for champions with two-part names
twoParts = {
    ".*? Lee Sin": "Lee Sin",
    ".*? Mundo": "Dr. Mundo"
    ...
}

# Dictionary containing skins not in format "[skin name] [champion name]"
exceptSkins = {
    "AstroNautilus": "Nautilus"
    ...
}

# Contains question and answer tuples for FAQ
faqArray = (
    (question, answer),
    ...
)
```
