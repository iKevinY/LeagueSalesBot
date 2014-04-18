#! /usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, re, math, datetime
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
kSuccess = '\033[32m'
kSpecial = '\033[36m'
kReset = '\033[0m'

def getContent():
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

    # http://na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-0415-0418
    # Hyphen below to strip leading zero
    mdStart = saleStart.strftime("%m%d")
    mdEnd = saleEnd.strftime("%m%d")
    dmStart = saleStart.strftime("%d%m")
    dmEnd = saleEnd.strftime("%d%m")
    naLink1 = "http://na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(mdStart, mdEnd)
    naLink2 = "http://na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(dmStart, dmEnd)
    euwLink1 = "http://euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(dmStart, dmEnd)
    euwLink2 = "http://euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(mdStart, mdEnd)

    if saleStart.month == saleEnd.month:
        dateRange = "({0}–{1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%-d"))
    else:
        dateRange = "({0} – {1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%B %-d"))

    print "Last sale ended on {0}. Requesting {1}".format(lastrun.lastSaleEnd, naLink1)
    try:
        header, content = httplib2.Http().request(naLink1)
    except httplib2.ServerNotFoundError:
        sys.exit(kWarning + "Connection error. " + kReset + "Terminating script.")

    # Tries the EU-W page if the NA page does not exist
    if header.status == 404:
        print kWarning + "NA page not found. " + kReset + "Requesting EU-W page: " + euwLink1
        header, content = httplib2.Http().request(euwLink1)

        if header.status == 404:
            print(kWarning + "EU-W page not found. " + kSpecial + "Attempting alternate date format." + kReset)

            print "Requesting alternate date format NA page: {0}".format(naLink2)
            header, content = httplib2.Http().request(naLink2)

            if header.status == 404:
                print kWarning + "NA page not found. " + kReset + "Requesting EU-W page: " + euwLink2
                header, content = httplib2.Http().request(euwLink2)

                if header.status == 404:
                    sys.exit(kWarning + "EU-W page not found. " + kReset + "Terminating script.")
                else:
                    naLink = naLink2
                    euwLink = euwLink2

            else:
                naLink = naLink2
                euwLink = euwLink2

        else:
            naLink = naLink1
            euwLink = euwLink1

    else:
        naLink = naLink1
        euwLink = euwLink1

    print kSuccess + "Post found!" + kReset + "\n"
    return content, dateRange, naLink, euwLink

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

        imageString = "[Splash Art]({0}), [In-Game]({1})".format(sale.splash, sale.inGame)
    else: # sale.isSkin == False
        champName = sale.name.replace('.', '')
        if champName == "Jarvan IV":
            champName = "Jarvan"
        try:
            champName = champName.rsplit(' ', 1)[0] + champName.rsplit(' ', 1)[1].lower()
        except IndexError:
            pass

        imageString = "[Splash Art](http://riot-web-static.s3.amazonaws.com/images/news/Champ_Splashes/{0}_Splash.jpg)".format(champName)

    champLink = "http://leagueoflegends.wikia.com/wiki/" + champName.replace(" ", "_")
    iconName = re.sub('\ |\.|\'', '', champName.lower())
    icon = "[](/{0})".format(iconName)

    return "|" + icon + "|**[" + sale.name + "](" + champLink + ")**|" + str(sale.sale) + " RP|" + str(sale.regular) + " RP|" + imageString + "|"

def makePost(saleArray, naLink, euwLink, dateRange):
    # Automate rotation of sale rotation
    rotationSchedule = [[975, 750, 520], [1350, 975, 520], [975, 750, 520], [975, 975, 520]]
    nextRotation = rotationSchedule[lastrun.rotation % 4]

    faqArray = [
    ("I recently bought one of these skins/champions.",
        "If you made the purchase within the past two weeks, you can [open a support ticket](https://support.leagueoflegends.com/anonymous_requests/new) and have the difference refunded."),
    ("How do you know the prices of the next skin sale?",
        "The skin sales follow a [four-stage rotation](http://forums.na.leagueoflegends.com/board/showthread.php?t=3651816)."),
    ("How does this bot work?",
        "/u/LeagueSalesBot is written in [Python](http://www.python.org/). It uses the [PRAW](https://praw.readthedocs.org/en/latest/) library to interface with Reddit's [API](http://www.reddit.com/dev/api) and [httplib2](http://code.google.com/p/httplib2/) to retrieve data from sale pages.")
    ]

    faq = ""
    for q in faqArray:
        faq = faq + "> **{0}**".format(q[0]) + "\n\n" + "{0}".format(q[1]) + "\n\n"

    sales = ""
    for sale in saleArray:
        sales = sales + saleOutput(sale) + "\n"

    postTitle = "[Skin Sale] " + saleArray[0].name + ", " + saleArray[1].name + ", " + saleArray[2].name + " " + dateRange

    return postTitle, (
        "| Icon | Skin/Champion | Sale Price | Regular Price | Images |\n" +
        "|:----:|:-------------:|:----------:|:-------------:|:------:|\n" +
        sales + '\n'
        "Next skin sale: **{0} RP, {1} RP, {2} RP**. ".format(nextRotation[0], nextRotation[1], nextRotation[2]) +
        "Link to sale pages ([NA]({0}), [EUW]({1})).".format(naLink, euwLink) + '\n\n----\n\n' +
        "### Frequently Asked Questions\n\n" + faq + '----\n'
        "^This ^bot ^was ^written ^by ^/u/Pewqazz. ^Feedback ^and ^suggestions ^are ^welcomed ^in ^/r/LeagueSalesBot."
    )

def submitPost(postTitle, postBody):
    r = praw.Reddit(user_agent = settings.userAgent)
    r.login(settings.username, settings.password)
    r.submit("LeagueSalesBot", postTitle, text = postBody)
    print kSuccess + "Post successfully submitted to Reddit." + kReset

    # Make appropriate changes to lastrun.py if post succeeds
    saleEndText = (datetime.datetime.now() + datetime.timedelta(4)).strftime("%Y-%m-%d")

    directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(directory, 'lastrun.py')
    f = open(path, 'r+')
    f.write("lastSaleEnd = \"{0}\"\nrotation = {1}\n".format(saleEndText, str((lastrun.rotation + 5) % 4)))
    f.close()

    print kSuccess + "Updated lastrun.py." + kReset

def manualPost():
    rotationSchedule = [[975, 750, 520], [1350, 975, 520], [975, 750, 520], [975, 975, 520]]
    thisRotation = rotationSchedule[(lastrun.rotation % 4) - 1]
    lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, "%Y-%m-%d")

    if (lastrun.rotation % 2) == 0:
        saleDefault = lastSaleEnd + datetime.timedelta(1)
    else:
        saleDefault = lastSaleEnd

    try:
        saleStart = datetime.datetime.strptime(raw_input("Enter sale starting date [{0}]: ".format(saleDefault.strftime("%Y-%m-%d"))), "%Y-%m-%d")
    except ValueError:
        saleStart = saleDefault

    saleEnd = saleStart + datetime.timedelta(3)

    naStartDate = saleStart.strftime("%-m%d")
    naEndDate = saleEnd.strftime("%-m%d")
    naLink = "http://na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(naStartDate, naEndDate)

    euwStartDate = saleStart.strftime("%d%-m")
    euwEndDate = saleEnd.strftime("%d%-m")
    euwLink = "http://euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(euwStartDate, euwEndDate)

    if saleStart.month == saleEnd.month:
        postTitle = "Champion & Skin Sale ({0}–{1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%-d"))
    else:
        postTitle = "Champion & Skin Sale ({0} – {1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%B %-d"))

    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    print kSpecial + postTitle + kReset

    # Skins
    for sale in saleArray:
        if sale.__class__ is Skin:
            thisRegular = thisRotation[saleArray.index(sale)]
            print "Skin #{0}:".format(saleArray.index(sale)+1)
            sale.name = raw_input("Name (skin price {0} RP): ".format(thisRegular))
            try:
                sale.name.rsplit(' ', 1)[1]
            except IndexError:
                champName = raw_input("Champion name: ")
                saleTitle = raw_input("Sale title: ")
            else:
                champName = raw_input("Champion name [{0}]: ".format(sale.name.rsplit(' ', 1)[1])).replace(" ", "") or sale.name.rsplit(' ', 1)[1]
                saleTitle = raw_input("Sale title [{0}]: ".format(sale.name.rsplit(' ', 1)[0])).replace(" ", "") or sale.name.rsplit(' ', 1)[0]
            sale.cost = int(math.floor(thisRegular / 2))
            sale.splash = "http://riot-web-static.s3.amazonaws.com/images/news/Skin_Sales/{0}_{1}_Splash.jpg".format(champName, saleTitle)
            sale.inGame = "http://riot-web-static.s3.amazonaws.com/images/news/Skin_Sales/{0}_{1}_SS.jpg".format(champName, saleTitle)
        else:
            print "Champion #{0}:".format(saleArray.index(sale)-2)
            sale.name = raw_input("Name: ")
            sale.cost = int(raw_input("Sale price (292-585, 395-790, 440-880, 487-975): "))
            saleName = sale.name.replace('.', '')
            if saleName == "Jarvan IV":
                saleName = "Jarvan"
            try:
                saleName = saleName.rsplit(' ', 1)[0] + saleName.rsplit(' ', 1)[1].lower()
            except IndexError:
                pass

            sale.splash = "http://riot-web-static.s3.amazonaws.com/images/news/Champ_Splashes/{0}_Splash.jpg".format(saleName)

    print "\n"
    postBody = makePost(saleArray, naLink, euwLink, dateRange)

    print "" + postBody

    prompt = raw_input("Post to Reddit? (Y/N) ")
    if prompt == "Y" or prompt == "y":
        pass
    else:
        print kWarning + "Did not post to Reddit." + kReset
        sys.exit(0)

    submitPost(postTitle, postBody)
    sys.exit(0)


def main():
    content, dateRange, naLink, euwLink = getContent()

    saleRegex = re.compile("<h4>(?:<a href.+?>)*\s*?(.+?)\s*?(?:<\/a>)*<\/h4>\s+?<strike.*?>(\d{3,4})<\/strike> (\d{3,4}) RP")
    imageRegex = re.compile("(http://riot-web-static\.s3\.amazonaws\.com/images/news/Skin_Sales/\S*?\.jpg)")

    # Declare sale objects
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    for i in range(0, 6):
        print re.findall(saleRegex, content)[i]
        saleArray[i].name, saleArray[i].regular, saleArray[i].sale = re.findall(saleRegex, content)[i]

        # Skins have splash and in-game while champions only have splash art
        if saleArray[i].__class__ is Skin:
            saleArray[i].splash = re.findall(imageRegex, content)[(i*4)]
            saleArray[i].inGame = re.findall(imageRegex, content)[(i*4)+2]

    postTitle, postBody = makePost(saleArray, naLink, euwLink, dateRange)

    print kSpecial + postTitle + kReset
    print postBody

    submitPost(postTitle, postBody)
    sys.exit(0)
