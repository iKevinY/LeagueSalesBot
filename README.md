LeagueSalesBot
==============

LeagueSalesBot is a Reddit bot that posts League of Legends sales to [/r/LeagueOfLegends](http://www.reddit.com/r/LeagueOfLegends). It was inspired by a similar bot – [/u/FreeChampionsBot](http://www.reddit.com/user/FreeChampionsBot) – that posts the free champion rotation. This bot was programmed as an exercise in learning Python.

The bot is run via a cron job that is set to run between 7am and 8am on days where the new sales are posted. It searches the [sales page](http://beta.na.leagueoflegends.com/en/news/store/sales) on the main League of Legends website and checks whether a new post has appeared since the last time the bot successfully posted to the subreddit; if so, it scrapes that post for the sale data and formats and posts it to Reddit.

If you're up in arms about the fact that I have used regular expressions to parse an HTML document rather than a library like [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/), more on that in a blog post I wrote about the coding of this bot.
