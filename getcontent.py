import httplib2
import sys

""" Determine URL to HTTP GET """

url = "http://beta.na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-802-805"


""" HTTP GET using httplib2 """

header, content = httplib2.Http().request(url)

if header.status == 404:
    sys.exit(0)
elif header.status == 200:
    pass