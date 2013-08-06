#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import httplib2
import calendar

import lastrun
import settings

# Load news page on League of Legends website
header, content = httplib2.Http().request(settings.newsPage)

# Check news page for first <h4> element with "champion-and-skin-sales" in slug
articleData = re.findall("<h4><a href=\"(.*?champion.*?skin-sale.*?)\">(.*?)</a></h4>", content)[0]
articleSlug = articleData[0]
articleName = articleData[1]
articleLink = "http://beta.na.leagueoflegends.com" + articleSlug

if articleLink == lastrun.articleLink:
    print 'First sale is same as last posted sale. (' + articleLink + ')'
    sys.exit(0)
else:
    pass

articleDate = re.findall(".*?: (\d{1,2})\.(\d{1,2}) - (\d{1,2})\.(\d{1,2})", articleName)[0]

firstMonth = calendar.month_name[int(articleDate[0])]
secondMonth = calendar.month_name[int(articleDate[2])]

firstDate = articleDate[1].lstrip('0')
secondDate = articleDate[3].lstrip('0')

if firstMonth == secondMonth:
    postTitle = "Champion & Skin Sale (" + firstMonth + " " + firstDate + "–" + secondDate + ")"
else:
    postTitle = "Champion & Skin Sale (" + firstMonth + " " + firstDate + " – " + secondMonth + " " + secondDate + ")"

header, content = httplib2.Http().request(articleLink)
