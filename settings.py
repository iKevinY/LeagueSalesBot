userAgent = "/u/LeagueSalesBot written by /u/Pewqazz (@iKevinY). Source code found at https://github.com/iKevinY/LeagueSalesBot."

baseTitle = '[Champion & Skin Sale] {0} ({1})'
baseLink = 'http://{0}.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{1}-{2}'

subreddits = [
    ["leagueoflegends", False],
    ["LeagueSalesBot", False],
]

faqArray = [
    ["I recently bought one of these skins/champions.",
        "If the purchase was made within the past two weeks, you can [open a support ticket](https://support.leagueoflegends.com/anonymous_requests/new) and have the difference refunded."],
    ["How do you know the prices of the next skin sale?",
        "The skin sales follow a [four-stage rotation](http://forums.na.leagueoflegends.com/board/showthread.php?t=3651816)."],
    ["How does this bot work?",
        "/u/LeagueSalesBot is written in [Python](http://www.python.org/). It uses the [PRAW](https://praw.readthedocs.org/en/latest/) library to interface with [Reddit's API](http://www.reddit.com/dev/api) and [httplib2](https://github.com/jcgregorio/httplib2) to crawl the sale pages."],
]

salePostedInAdvanced = True

if salePostedInAdvanced:
    month = 'July'
    link = 'http://na.leagueoflegends.com/en/news/store/sales/july-champion-and-skin-sales'
    faqArray[0][1] = "Since the [full {0} sale schedule]({1}) has already been posted, partial refunds are not being offered.".format(month, link)
