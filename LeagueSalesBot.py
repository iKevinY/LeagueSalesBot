#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import os, sys, re, calendar, datetime
import httplib2, praw
import settings, lastrun

class Sale:
    pass
class Skin(Sale):
    isSkin = True
class Champ(Sale):
    isSkin = False

def getContent(testURL = None):
    if testURL:
        print "Testing URL supplied. Scraping {0}.".format(testURL)
        header, content = httplib2.Http().request(testURL)
        articleLink = testURL
    else:
        # Get string of end of last sale from lastrun.py
        lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, "%Y-%m-%d")

        # If lastrun.rotation is even, the last sale was posted on a Thursday so the next sale will start a day after the
        # end date of the previous sale. Otherwise, the next sale will start on the same day that the last sale ended on.
        if (lastrun.rotation % 2) == 0:
            saleStart = lastSaleEnd + datetime.timedelta(1)
        else:
            saleStart = lastSaleEnd

        # Sales always end 3 days after they start (four-day-long sales)
        saleEnd = saleStart + datetime.timedelta(3)

        # Hackish way of stripping leading zeros from months
        saleStartString = saleStart.strftime("X%m%d").replace("X0", "").replace("X", "") # hacky
        saleEndString = saleEnd.strftime("X%m%d").replace("X0", "").replace("X", "") # hacky

        articleLink = "http://beta.na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(saleStartString, saleEndString)

        print "Last sale ended on {0}. Trying {1}.".format(lastrun.lastSaleEnd, articleLink)

        header, content = httplib2.Http().request(articleLink)

    if header.status == 404:
        print "Page not found."
        sys.exit(1)
    else:
        pass

    articleDate = re.findall("http://beta.na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-(\d+)(\d{2})-(\d+)(\d{2})", articleLink)[0]

    startMonth = calendar.month_name[int(articleDate[0])]
    endMonth = calendar.month_name[int(articleDate[2])]

    startDate = articleDate[1].lstrip('0')
    endDate = articleDate[3].lstrip('0')

    if startMonth == endMonth:
        postTitle = "Champion & Skin Sale (" + startMonth + " " + startDate + "–" + endDate + ")"
    else:
        postTitle = "Champion & Skin Sale (" + startMonth + " " + startDate + " – " + endMonth + " " + endDate + ")"

    if testURL:
        print postTitle + "\n"

    header, content = httplib2.Http().request(articleLink)

    return content, postTitle, articleLink

def saleOutput(sale):
    if sale.isSkin == True:
        # Try all exception skins (reference: http://leagueoflegends.wikia.com/wiki/Champion_skin)
        if   re.compile(".*? Mundo").match(sale.name):          champName = "Dr. Mundo"
        elif re.compile(".*? Jarvan IV").match(sale.name):      champName = "Jarvan IV"
        elif re.compile(".*? Lee Sin").match(sale.name):        champName = "Lee Sin"
        elif re.compile(".*? Master Yi").match(sale.name):      champName = "Master Yi"
        elif re.compile(".*? Miss Fortune").match(sale.name):   champName = "Miss Fortune"
        elif re.compile(".*? Twisted Fate").match(sale.name):   champName = "Twisted Fate"
        elif re.compile(".*? Xin Zhao").match(sale.name):       champName = "Xin Zhao"

        elif sale.name == "Emumu":                              champName = "Amumu"
        elif sale.name == "Annie In Wonderland":                champName = "Annie"
        elif sale.name == "iBlitzcrank":                        champName = "Blitzcrank"
        elif sale.name == "Mr. Mundoverse":                     champName = "Dr. Mundo"
        elif sale.name == "Gragas, Esq":                        champName = "Gragas"
        elif sale.name == "Snowmerdinger":                      champName = "Heimerdinger"
        elif sale.name == "Jaximus":                            champName = "Jax"
        elif sale.name == "Kennen M.D.":                        champName = "Kennen"
        elif sale.name == "Samurai Yi":                         champName = "Master Yi"
        elif sale.name == "AstroNautilus":                      champName = "Nautilus"
        elif sale.name == "Nunu Bot":                           champName = "Nunu"
        elif sale.name == "Brolaf":                             champName = "Olaf"
        elif sale.name == "Lollipoppy":                         champName = "Poppy"
        elif sale.name == "Rumble in the Jungle":               champName = "Rumble"
        elif sale.name == "Nutcracko":                          champName = "Shaco"
        elif sale.name == "Jack of Hearts":                     champName = "Twisted Fate"
        elif sale.name == "Giant Enemy Crabgot":                champName = "Urgot"
        elif sale.name == "Urf the Manatee":                    champName = "Warwick"
        
        else: champName = sale.name.rsplit(' ', 1)[1]
        
        imageString = "[Splash Art](" + sale.splash + "), [In-Game](" + sale.inGame + ")"
    else: # sale.isSkin == False
        champName = sale.name
        imageString = "[Splash Art](" + sale.splash + ")"

    champLink = "http://leagueoflegends.wikia.com/wiki/" + champName.replace(" ", "_")
    icon = "[](/" + champName.lower().replace(" ", "").replace(".", "").replace("'", "") + ")"

    # Calculate regular price of skin/champion
    if (sale.cost == 487) or (sale.cost == 292):
        regularPrice = sale.cost * 2 + 1
    else:
        regularPrice = sale.cost * 2

    return "|" + icon + "|**[" + sale.name + "](" + champLink + ")**|" + str(sale.cost) + " RP|" + str(regularPrice) + " RP|" + imageString + "|"

def makePost(saleArray, bannerLink, articleLink):
    # Automate rotation of sale rotation
    rotation = [[975, 750, 520], [1350, 975, 520], [975, 750, 520], [975, 975, 520]]
    nextRotation = rotation[lastrun.rotation % 4]

    sales = ""
    for sale in saleArray:
        sales = sales + saleOutput(sale) + "\n"

    return (
        "| Icon | Skin/Champion | Sale Price | Regular Price | Images |\n" +
        "|:----:|:-------------:|:----------:|:-------------:|:------:|\n" +
        sales +
        "Next skin sale: **{0} RP, {1} RP, {2} RP**. ".format(nextRotation[0], nextRotation[1], nextRotation[2]) +
        "Link to [source post]({0}) and [sale banner]({1}).".format(articleLink, bannerLink) + "\n\n----\n" +
        "^This ^bot ^was ^written ^by ^/u/Pewqazz. ^Feedback ^and ^suggestions ^are ^welcomed ^in ^/r/LeagueSalesBot."
    )

def main(testURL = None):
    content, postTitle, articleLink = getContent(testURL)

    saleRegex = re.compile("<ul><li>(.*?<strong>\d{3} RP</strong>)</li></ul>")
    imageRegex = re.compile("<a href=\"(http://riot-web-static\.s3\.amazonaws\.com/images/news/\S*?\.jpg)\"")
    bannerRegex = re.compile("<img .*? src=\"(http://beta\.na\.leagueoflegends\.com/\S*?articlebanner\S*?.jpg)?\S*?\"")

    # Declare sale objects
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    # Set sale text to .text attributes of saleArray elements
    for i in range(len(saleArray)):
        # Clean the "Â" character from end of sale names
        saleArray[i].text = unicode(re.findall(saleRegex, content)[i], "utf-8")

        text = (re.sub('<.*?>', '', saleArray[i].text))

        # Strip " ___ RP" from end of string
        saleArray[i].name = text[:-7]
        saleArray[i].cost = int(re.findall('\d+', text)[0])

        # Skins have splash and in-game while champions only have splash art
        if saleArray[i].__class__ is Skin:
            saleArray[i].splash = re.findall(imageRegex, content)[(i*2)]
            saleArray[i].inGame = re.findall(imageRegex, content)[(i*2)+1]
        elif saleArray[i].__class__ is Champ:
            saleArray[i].splash = re.findall(imageRegex, content)[i+3]
        else:
            pass

    bannerLink = re.findall(bannerRegex, content)[0]

    postBody = makePost(saleArray, bannerLink, articleLink)

    if testURL:
        print postBody
    else:
        # Post to Reddit
        r = praw.Reddit(user_agent=settings.userAgent)
        r.login(settings.username, settings.password)
        r.submit(settings.subreddit, postTitle, text=postBody)

        # Format date
        saleEnd = datetime.datetime.now()
        saleEnd = saleEnd + datetime.timeDelta(3)
        saleEnd = saleEnd.strftime("%Y-%m-%d")
        
        # Make appropriate changes to lastrun.py if post succeeds
        directory = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(directory, 'lastrun.py')
        f = open(path, 'r+')
        f.write("lastSaleEnd = {0}".format(saleEnd))
        f.close()
