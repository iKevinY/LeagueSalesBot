#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import os, sys, re, datetime
import httplib2, praw
import settings, lastrun

# Create classes for sale types (skins and champions)
class Sale:
    pass
class Skin(Sale):
    isSkin = True
class Champ(Sale):
    isSkin = False

# Keywords for ANSI-coloured terminal messages
kWarning = '\033[31m'
kSpecial = '\033[36m'
kReset = '\033[0m'

def generateLinks():
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

    naStartDate = saleStart.strftime("%-m%d")
    naEndDate = saleEnd.strftime("%-m%d")
    naLink = "http://beta.na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(naStartDate, naEndDate)

    euwStartDate = saleStart.strftime("%d%-m")
    euwEndDate = saleEnd.strftime("%d%-m")
    euwLink = "http://beta.euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(euwStartDate, euwEndDate)

    if saleStart.month == saleEnd.month:
        postTitle = "Champion & Skin Sale ({0}–{1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%-d"))
    else:
        postTitle = "Champion & Skin Sale ({0} – {1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%B %-d"))

    return naLink, euwLink, postTitle

def getContent(testURL = None):
    if testURL:
        print "Test URL provided. Scraping {0}".format(testURL)
        try:
            header, content = httplib2.Http().request(testURL)
        except httplib2.ServerNotFoundError:
            print kWarning + "Connection error. " + kReset + "Terminating script."
            sys.exit(1)

        if header.status == 404:
            print kWarning + "{0} not found. ".format(testURL) + kReset + "Terminating script."
            sys.exit(1)
        else:
            try:
                saleStart, saleEnd = re.findall("http://beta\.(?:na|euw)\.leagueoflegends\.com/\S*?-(\d{3,4})-(\d{3,4})", testURL)[0]
            except IndexError:
                print "Unknown region/unrecognized URL."
                sys.exit(1)
            else:
                pass

            if ".na." in testURL:
                naLink = testURL
                startDate = datetime.datetime.strptime(saleStart, "%m%d")
                endDate = datetime.datetime.strptime(saleEnd, "%m%d")
                euwLink = "http://beta.euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(
                    startDate.strftime("%d%-m"), endDate.strftime("%d%-m"))
            elif ".euw." in testURL:
                euwLink = testURL
                startDate = datetime.datetime.strptime(saleStart, "%d%m")
                endDate = datetime.datetime.strptime(saleEnd, "%d%m")
                naLink = "http://beta.na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(
                    startDate.strftime("%-m%d"), endDate.strftime("%-m%d"))

            if startDate.month == endDate.month:
                postTitle = "Champion & Skin Sale ({0}–{1})".format(startDate.strftime("%B %-d"), endDate.strftime("%-d"))
            else:
                postTitle = "Champion & Skin Sale ({0} – {1})".format(startDate.strftime("%B %-d"), endDate.strftime("%B %-d"))

    else: # not testURL
        naLink, euwLink, postTitle = generateLinks()
        
        print "Last sale ended on {0}. Requesting {1}".format(lastrun.lastSaleEnd, naLink)

        try:
            header, content = httplib2.Http().request(naLink)
        except httplib2.ServerNotFoundError:
            print kWarning + "Connection error. " + kReset + "Terminating script."
            sys.exit(1)

        # Tries the EU-W page if the NA page does not exist
        if header.status == 404:
            print kWarning + "NA page not found. " + kReset + "Requesting EU-W page: " + euwLink
            header, content = httplib2.Http().request(euwLink)
            if header.status == 404:
                print kWarning + "EU-W page not found. " + kReset + "Terminating script."
                sys.exit(1)
            else:
                pass
        else:
            pass

    if testURL:
        print kSpecial + postTitle + kReset

    return content, postTitle, naLink, euwLink

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
    iconName = re.sub('\ |\.|\'', '', champName.lower())
    icon = "[](/{0})".format(iconName)

    # Calculate regular price of skin/champion
    if (sale.cost == 487) or (sale.cost == 292):
        regularPrice = sale.cost * 2 + 1
    else:
        regularPrice = sale.cost * 2

    return "|" + icon + "|**[" + sale.name + "](" + champLink + ")**|" + str(sale.cost) + " RP|" + str(regularPrice) + " RP|" + imageString + "|"

def makePost(saleArray, bannerLink, naLink, euwLink):
    # Automate rotation of sale rotation
    rotationSchedule = [[975, 750, 520], [1350, 975, 520], [975, 750, 520], [975, 975, 520]]
    nextRotation = rotationSchedule[lastrun.rotation % 4]

    sales = ""
    for sale in saleArray:
        sales = sales + saleOutput(sale) + "\n"

    return (
        "| Icon | Skin/Champion | Sale Price | Regular Price | Images |\n" +
        "|:----:|:-------------:|:----------:|:-------------:|:------:|\n" +
        sales +
        "Next skin sale: **{0} RP, {1} RP, {2} RP**. ".format(nextRotation[0], nextRotation[1], nextRotation[2]) +
        "Link to sale pages ([NA]({0}), [EU-W]({1})) and [banner image]({2}).".format(naLink, euwLink, bannerLink) + "\n\n----\n" +
        "^This ^bot ^was ^written ^by ^/u/Pewqazz. ^Feedback ^and ^suggestions ^are ^welcomed ^in ^/r/LeagueSalesBot."
    )

def main(testURL = None):
    content, postTitle, naLink, euwLink = getContent(testURL)

    saleRegex = re.compile("<ul><li>(.*?<strong>\d{3,4} RP</strong>)</li></ul>")
    imageRegex = re.compile("<a href=\"(http://riot-web-static\.s3\.amazonaws\.com/images/news/\S*?\.jpg)\"")
    bannerRegex = re.compile("<img .*? src=\"(http://beta\.(?:na|euw)\.leagueoflegends\.com/\S*?articlebanner\S*?.jpg)?\S*?\"")

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

    postBody = makePost(saleArray, bannerLink, naLink, euwLink)

    if testURL:
        print postBody
        sys.exit(0)
    else:
        # Post to Reddit (first /r/leagueoflegends, and then /r/LeagueSalesBot for archival purposes)
        r = praw.Reddit(user_agent=settings.userAgent)
        r.login(settings.username, settings.password)
        r.submit("leagueoflegends", postTitle, text=postBody)
        r.submit("LeagueSalesBot", postTitle, text=postBody)

        # Format date
        saleEndText = (datetime.datetime.now() + datetime.timedelta(3)).strftime("%Y-%m-%d")
        
        # Make appropriate changes to lastrun.py if post succeeds
        directory = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(directory, 'lastrun.py')
        f = open(path, 'r+')
        f.write("lastSaleEnd = \"{0}\"\nrotation = {1}\n".format(saleEndText, str(lastrun.rotation + 1)))
        f.close()

        sys.exit(0)
