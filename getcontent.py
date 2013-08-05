import sys
import re
import httplib2
import settings

# Load news page on League of Legends website
header, content = httplib2.Http().request("http://beta.na.leagueoflegends.com/en/news/store/sales/")

# Check news page for first <h4> element with "champion-and-skin-sales" in slug
articleData = re.findall("<h4><a href=\"(.*?champion.*?skin-sale.*?)\">(.*?)</a></h4>", content)[0]
articleSlug = articleData[0]
articleName = articleData[1]
articleLink = "http://beta.na.leagueoflegends.com" + articleSlug

if articleLink == settings.lastArticleLink:
    sys.exit(0)
else:
    pass

articleDate = re.findall(".*?: (\d{1,2}.\d{1,2} - \d{1,2}.\d{1,2})", articleName)[0]
postTitle = "Champion & Skin Sale (" + articleDate + ")"

header, content = httplib2.Http().request(articleLink)
