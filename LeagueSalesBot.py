#! /usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, re, math, datetime, webbrowser
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

def openBanner(bannerLink = None):

    if (lastrun.rotation % 2) == 0:
        delta = datetime.timedelta(1)
    else:
        delta = datetime.timedelta(0)

    inputDate = datetime.datetime.strptime(lastrun.lastSaleEnd, "%Y-%m-%d") + delta

    year = str(inputDate.year)
    if len(str(inputDate.month)) == 1:
        month = "0" + str(inputDate.month)
    else:
        month = str(inputDate.month)
    day = inputDate.day
    bannerLink = (
        "http://beta.na.leagueoflegends.com/sites/default/files/styles/wide_medium/public/upload/{0}.{1}.{2}.articlebanner.champskinsale.jpg".format(year, month, day))

    header, content = httplib2.Http().request(bannerLink)

    print "Using sale start date of {0}. Banner returned {1}.".format(inputDate.strftime("%Y-%m-%d"), header.status)

    if header.status == 200:
        confirm = raw_input("Open in browser? (Y/N) ".format(header.status))
        if (confirm == "y") or (confirm == "Y"):
            webbrowser.open(bannerLink)
        sys.exit(0)
    else:
        sys.exit(header.status)

def logForbidden(content):
    """
    fileName = datetime.datetime.now().strftime("%H.%M.%S") + "-403.html"
    directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(directory, 'logs/' + fileName)
    f = open(path, 'w')
    f.write(content)
    f.close()
    print kWarning + "403 forbidden. " + kReset + "Wrote page content to " + fileName
    """
    print kWarning + "403 forbidden." + kReset
    sys.exit(403)

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

    mdStartDate = saleStart.strftime("%-m%d")
    mdEndDate = saleEnd.strftime("%-m%d")
    dmStartDate = saleStart.strftime("%d%-m")
    dmEndDate = saleEnd.strftime("%d%-m")
    naLink1 = "http://beta.na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(mdStartDate, mdEndDate)
    naLink2 = "http://beta.na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(dmStartDate, dmEndDate)
    euwLink1 = "http://beta.euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(dmStartDate, dmEndDate)
    euwLink2 = "http://beta.euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(mdStartDate, mdEndDate)

    if saleStart.month == saleEnd.month:
        postTitle = "Champion & Skin Sale ({0}–{1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%-d"))
    else:
        postTitle = "Champion & Skin Sale ({0} – {1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%B %-d"))

    return naLink1, naLink2, euwLink1, euwLink2, postTitle

def getContent(testURL = None):
    if testURL:
        print "Test URL provided. Scraping {0}".format(testURL)
        try:
            header, content = httplib2.Http().request(testURL)
        except httplib2.ServerNotFoundError:
            sys.exit(kWarning + "Connection error. " + kReset + "Terminating script.")
            
        if header.status == 404:
            sys.exit(kWarning + "{0} not found (404). ".format(testURL) + kReset + "Terminating script.")
        elif header.status == 403:
            logForbidden(content)
        else:
            try:
                saleStart, saleEnd = re.findall("http://beta\.(?:na|euw)\.leagueoflegends\.com/\S*?-(\d{3,4})-(\d{3,4})", testURL)[0]
            except IndexError:
                sys.exit(kWarning + "Unknown region/unrecognized URL." + kReset)
            else:
                pass

            dateFormat = raw_input("Enter format of date in given URL (MD / DM): ")

            if dateFormat == "MD" or dateFormat == "md":
                givenFormat = "%m%d"
                altFormat = "%d%m"
            elif dateFormat == "DM" or dateFormat == "dm":
                givenFormat = "%d%m"
                altFormat = "%m%d"
            else:
                sys.exit(kWarning + "Invalid date string format. " + kReset + "Terminating script.")

            startDate = datetime.datetime.strptime(saleStart, givenFormat)
            endDate = datetime.datetime.strptime(saleEnd, givenFormat)

            if ".na." in testURL:
                naLink = testURL
                euwLink = "http://beta.euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(
                    startDate.strftime(altFormat), endDate.strftime(altFormat))
            elif ".euw." in testURL:
                euwLink = testURL
                naLink = "http://beta.na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(
                    startDate.strftime(altFormat), endDate.strftime(altFormat))

            if startDate.month == endDate.month:
                postTitle = "Champion & Skin Sale ({0}–{1})".format(startDate.strftime("%B %-d"), endDate.strftime("%-d"))
            else:
                postTitle = "Champion & Skin Sale ({0} – {1})".format(startDate.strftime("%B %-d"), endDate.strftime("%B %-d"))

    else: # not testURL
        naLink1, naLink2, euwLink1, euwLink2, postTitle = generateLinks()
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
                    elif header.status == 403:
                        logForbidden(content)
                    else:
                        naLink = naLink2
                        euwLink = euwLink2

                elif header.status == 403:
                    logForbidden(content)
                else:
                    naLink = naLink2
                    euwLink = euwLink2


            elif header.status == 403:
                logForbidden(content)
            else:
                naLink = naLink1
                euwLink = euwLink1

        elif header.status == 403:
                logForbidden(content)
        else:
            naLink = naLink1
            euwLink = euwLink1

    if testURL:
        print kSpecial + postTitle + kReset
    else:
        print kSuccess + "Post found!" + kReset + "\n"

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
        
        imageString = "[Splash Art]({0}), [In-Game]({1})".format(sale.splash, sale.inGame)
    else: # sale.isSkin == False
        champName = sale.name
        imageString = "[Splash Art]({0})".format(sale.splash)

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

    faqArray = [
    ("I recently bought one of these skins/champions.",
        "If you made the purchase within the past two weeks, you can [open a support ticket](https://support.leagueoflegends.com/anonymous_requests/new) and have the difference refunded."),
    ("How do you know the prices of the next skin sale?",
        "The skin sales follow a [four-stage rotation](http://forums.na.leagueoflegends.com/board/showthread.php?t=3651816)."),
    ("What skins and champions will go on sale next?",
        "Unfortunately, /u/LeagueSalesBot is a Reddit bot, not a psychic. That being said, Jagz has created a [spreadsheet](https://docs.google.com/spreadsheet/lv?key=0AgTL8IK0A37pdHB2MmNfVG93enV2SnpJeHhxTHhZcUE) with data on what skins and champions are due to go on sale."),
    ("How does this bot work?",
        "/u/LeagueSalesBot is written in [Python](http://www.python.org/). It uses the [PRAW](https://praw.readthedocs.org/en/latest/) library to interface with Reddit's [API](http://www.reddit.com/dev/api) and [httplib2](http://code.google.com/p/httplib2/) to retrieve data from sale pages.")
    ]

    faq = ""
    for q in faqArray:
        faq = faq + "> **{0}**".format(q[0]) + "\n\n" + "{0}".format(q[1]) + "\n\n"

    sales = ""
    for sale in saleArray:
        sales = sales + saleOutput(sale) + "\n"

    return (
        "| Icon | Skin/Champion | Sale Price | Regular Price | Images |\n" +
        "|:----:|:-------------:|:----------:|:-------------:|:------:|\n" +
        sales + '\n'
        "Next skin sale: **{0} RP, {1} RP, {2} RP**. ".format(nextRotation[0], nextRotation[1], nextRotation[2]) +
        "Link to sale pages ([NA]({0}), [EUW]({1})) and [banner image]({2}).".format(naLink, euwLink, bannerLink) + '\n\n----\n\n' +
        "### Frequently Asked Questions\n\n" + faq + '----\n'
        "^This ^bot ^was ^written ^by ^/u/Pewqazz. ^Feedback ^and ^suggestions ^are ^welcomed ^in ^/r/LeagueSalesBot."
    )

def submitPost(postTitle, postBody):
    # Post to Reddit (first /r/leagueoflegends, and then /r/LeagueSalesBot for archival purposes)
    r = praw.Reddit(user_agent=settings.userAgent)
    r.login(settings.username, settings.password)
    r.submit("leagueoflegends", postTitle, text=postBody)
    r.submit("LeagueSalesBot", postTitle, text=postBody)

    print kSuccess + "Posted to Reddit." + kReset
    
    # Make appropriate changes to lastrun.py if post succeeds
    saleEndText = (datetime.datetime.now() + datetime.timedelta(4)).strftime("%Y-%m-%d")

    directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(directory, 'lastrun.py')
    f = open(path, 'r+')
    f.write("lastSaleEnd = \"{0}\"\nrotation = {1}\n".format(saleEndText, str(lastrun.rotation + 1)))
    f.close()

    print kSuccess + "Updated lastrun.py successfully." + kReset

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
    naLink = "http://beta.na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(naStartDate, naEndDate)

    euwStartDate = saleStart.strftime("%d%-m")
    euwEndDate = saleEnd.strftime("%d%-m")
    euwLink = "http://beta.euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(euwStartDate, euwEndDate)

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
            sale.splash = "http://riot-web-static.s3.amazonaws.com/images/news/Skins/{0}_{1}_Splash.jpg".format(champName, saleTitle)
            sale.inGame = "http://riot-web-static.s3.amazonaws.com/images/news/Skins/{0}_{1}_SS.jpg".format(champName, saleTitle)
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

    bannerLink = raw_input("Enter URL of banner link: ") or "##"

    postBody = makePost(saleArray, bannerLink, naLink, euwLink)

    print "" + postBody

    prompt = raw_input("Post to Reddit? (Y/N) ")
    if prompt == "Y" or prompt == "y":
        prompt = raw_input("Confirm? (Y/N) ")
        if prompt == "Y" or prompt == "y":
            pass
        else:
            print kWarning + "Did not post to Reddit." + kReset
            sys.exit(0)
    else:
        print kWarning + "Did not post to Reddit." + kReset
        sys.exit(0)

    # submitPost(postTitle, postBody)

    sys.exit(0)


def main(testURL = None):
    content, postTitle, naLink, euwLink = getContent(testURL)

    saleRegex = re.compile("<ul><li>(.*?<strong>\d{3,4} RP</strong>)</li></ul>")
    imageRegex = re.compile("<a href=\"(http://riot-web-static\.s3\.amazonaws\.com/images/news/\S*?\.jpg)\"")
    bannerRegex = re.compile("(http://beta\.(?:na|euw)\.leagueoflegends\.com/\S*?articlebanner\S*?.jpg)?\S*?")

    # Declare sale objects
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    # Set sale text to .text attributes of saleArray elements
    for i in range(len(saleArray)):
        # Clean the "Â" character from end of sale names
        try:
            saleArray[i].text = unicode(re.findall(saleRegex, content)[i], "utf-8")
        except IndexError:
            # That annoying error.
            fileName = datetime.datetime.now().strftime("%H.%M.%S") + " IndexError.html"
            directory = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(directory, 'logs/' + fileName)
            f = open(path, 'w')
            f.write(content)
            f.close()

            print kWarning + "Page is not formatted correctly. " + kReset + "Wrote page content to " + fileName
            sys.exit(2)

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
        prompt = raw_input("Post to Reddit? (Y/N) ")
        if prompt == "Y" or prompt == "y":
            prompt = raw_input("Confirm? (Y/N) ")
            if prompt == "Y" or prompt == "y":
                pass
            else:
                print kWarning + "Did not post to Reddit." + kReset
                sys.exit(0)
        else:
            print kWarning + "Did not post to Reddit." + kReset
            sys.exit(0)

    print kSpecial + postTitle + kReset
    print postBody

    submitPost(postTitle, postBody)

    sys.exit(0)
