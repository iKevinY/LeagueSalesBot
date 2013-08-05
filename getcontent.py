import sys
import re
import httplib2

# Load news page on League of Legends website
header, content = httplib2.Http().request("http://beta.na.leagueoflegends.com/en/news/store/sales/")

# Check news page for first <h4> element with "champion-and-skin-sales" in slug
articleData = re.findall("<h4><a href=\"(.*?skin-sale.*?)\">(.*?)</a></h4>", content)[0]
articleLink = "http://beta.na.leagueoflegends.com" + articleData[0]
articleName = articleData[1]

articleDate = re.findall(".*?: (\d{1,2}.\d{1,2} - \d{1,2}.\d{1,2})", articleName)[0]
postTitle = "Champion & Skin Sale [" + articleDate + "]"
lastArticleLink = "http://beta.na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-123-123"

if articleLink != lastArticleLink:
    pass
else:
    sys.exit(0)

header, content = httplib2.Http().request(articleLink)
