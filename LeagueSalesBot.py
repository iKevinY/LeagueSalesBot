#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import os, sys, re, calendar
import httplib2, praw
import settings, lastrun

class Sale:
    pass
class Skin(Sale):
    isSkin = True
class Champ(Sale):
    isSkin = False

def getContent(isTest):
    # Load news page on League of Legends website
    header, content = httplib2.Http().request(settings.newsPage)

    # Check news page for first <h4> element with "champion-and-skin-sales" in slug
    articleSlug, articleName = re.findall("<h4><a href=\"(.*?champion.*?skin-sale.*?)\">(.*?)</a></h4>", content)[0]

    articleLink = "http://beta.na.leagueoflegends.com" + articleSlug

    if articleLink == lastrun.articleLink:
        print 'First sale is same as last posted sale. (' + articleLink + ')'
        if isTest:
            pass
        else:
            sys.exit(0)
    else:
        pass

    articleDate = re.findall(".*?: (\d{1,2})\.(\d{1,2}) - (\d{1,2})\.(\d{1,2})", articleName)[0]

    startMonth = calendar.month_name[int(articleDate[0])]
    endMonth = calendar.month_name[int(articleDate[2])]

    startDate = articleDate[1].lstrip('0')
    endDate = articleDate[3].lstrip('0')

    if startMonth == endMonth:
        postTitle = "Champion & Skin Sale (" + startMonth + " " + startDate + "–" + endDate + ")"
    else:
        postTitle = "Champion & Skin Sale (" + startMonth + " " + startDate + " – " + endMonth + " " + endDate + ")"

    if isTest:
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
    else: # isSkin == False
        champName = sale.name
        imageString = "[Splash Art](" + sale.splash + ")"

    champLink = "http://leagueoflegends.wikia.com/wiki/" + champName.replace(" ", "_")
    icon = "[](/" + champName.lower().replace(" ", "").replace(".", "").replace("'", "") + ")"

    # Calculate regular price of item
    if (sale.cost == 487) or (sale.cost == 292):
        regularPrice = str(int(sale.cost) * 2 + 1)
    else:
        regularPrice = str(int(sale.cost) * 2)

    return "|" + icon + "|**[" + sale.name + "](" + champLink + ")**|" + str(sale.cost) + " RP|" + str(regularPrice) + " RP|" + imageString + "|"

def makePost(saleArray, bannerLink, articleLink):
    # Automate rotation of sale rotation
    rotation = [[975, 750, 520], [1350, 975, 520], [975, 750, 520], [975, 975, 520]]
    nextRotation = rotation[lastrun.rotation%4]

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

def main(isTest):
    content, postTitle, articleLink = getContent(isTest)

    # Declare sale objects
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    saleRegex = re.compile("<ul><li>(.*?<strong>\d{3} RP</strong>)</li></ul>")
    imageRegex = re.compile("<a href=\"(http://riot-web-static\.s3\.amazonaws\.com/images/news/\S*?\.jpg)\"")
    bannerRegex = re.compile("<img .*? src=\"(http://beta\.na\.leagueoflegends\.com/\S*?articlebanner\S*?.jpg)?\S*?\"")

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

    if isTest:
        print postBody
    else:
        # Post to Reddit
        r = praw.Reddit(user_agent=settings.userAgent)
        r.login(settings.username, settings.password)
        r.submit(settings.subreddit, postTitle, text=postBody)
        
        # Make appropriate changes to lastrun.py if post succeeds
        directory = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(directory, 'lastrun.py')
        f = open(path, 'r+')
        f.write("articleLink = \"" + articleLink + "\"\n" + "rotation = " + str(lastrun.rotation + 1) + "\n")
        f.close()
