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

# Define variables for ANSI-coloured terminal messages
kWarning = '\033[31m'
kSuccess = '\033[32m'
kSpecial = '\033[36m'
kReset = '\033[0m'

def getContent(testLink = None):
    if testLink:
        naLink = testLink
        euwLink = None
        try:
            header, content = httplib2.Http().request(testLink)
        except httplib2.ServerNotFoundError:
            sys.exit(kWarning + "Connection error. " + kReset + "Terminating script.")

        start, end = re.findall(".*(\d{4})-(\d{4})", testLink)[0]

        saleStart = datetime.datetime.strptime(start, "%m%d")
        saleEnd = datetime.datetime.strptime(end, "%m%d")

        if saleStart.month == saleEnd.month:
            dateRange = "({0}–{1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%-d"))
        else:
            dateRange = "({0} – {1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%B %-d"))
    else:
        # Get string of end of last sale from lastrun.py
        lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, "%Y-%m-%d")

        # If lastrun.rotation is even, the last sale was posted on a Thursday so the next sale will start a day after the
        # end date of the previous sale. Otherwise, the next sale will start on the same day that the last sale ended on.
        saleStart = lastSaleEnd + datetime.timedelta((lastrun.rotation + 1) % 2)

        # Sales always end 3 days after they start (four-day-long sales)
        saleEnd = saleStart + datetime.timedelta(3)

        # Insert leading hyphen to strip leading zero
        mdStart = saleStart.strftime("%m%d")
        mdEnd = saleEnd.strftime("%m%d")
        dmStart = saleStart.strftime("%d%m")
        dmEnd = saleEnd.strftime("%d%m")

        links = {}
        links[0] = "http://na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(mdStart, mdEnd)
        links[1] = "http://na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(dmStart, dmEnd)
        links[2] = "http://euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(dmStart, dmEnd)
        links[3] = "http://euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(mdStart, mdEnd)
        naLink, euwLink = None, None

        if saleStart.month == saleEnd.month:
            dateRange = "({0}–{1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%-d"))
        else:
            dateRange = "({0} – {1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%B %-d"))

        print "Last sale ended on {0}.".format(lastrun.lastSaleEnd)

        for i in range(len(links)):
            try:
                header, content = httplib2.Http().request(links[i])
            except httplib2.ServerNotFoundError:
                sys.exit(kWarning + "Connection error. " + kReset + "Terminating script.")

            print "Requesting {0}".format(links[i])

            if header.status == 404:
                if i == 3:
                    sys.exit(kWarning + "Not found. Terminating script." + kReset)
                else:
                    print kWarning + "Not found." + kReset
            elif header.status == 403:
                if i == 3:
                    sys.exit(kWarning + "403 Forbidden. Terminating script." + kReset)
                else:
                    print kWarning + "403 Forbidden." + kReset
            else:
                if i % 2 == 0:
                    naLink, euwLink = links[0], links[2]
                else:
                    naLink, euwLink = links[1], links[3]
                break

        print kSuccess + "Post found!" + kReset + "\n"

    return content, dateRange, naLink, euwLink or "#"

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

        spotlightString = "[Skin Spotlight]({0})".format(sale.spotlight)
        imageString = "[Splash Art]({0}), [In-Game]({1})".format(sale.splash, sale.inGame)
    else: # sale.isSkin == False
        champName = sale.name.replace('.', '')
        if champName == "Jarvan IV":
            champName = "Jarvan"
        try:
            champName = champName.rsplit(' ', 1)[0] + champName.rsplit(' ', 1)[1].lower()
        except IndexError:
            pass

        spotlightString = "[Champion Spotlight]({0}), ".format(sale.spotlight) or ""
        imageString = "[Splash Art](http://riot-web-static.s3.amazonaws.com/images/news/Champ_Splashes/{0}_Splash.jpg)".format(champName)

    champLink = "http://leagueoflegends.wikia.com/wiki/" + champName.replace(" ", "_")
    iconName = re.sub('\ |\.|\'', '', champName.lower())
    icon = "[](/{0})".format(iconName)

    return "|{0}|**[{1}]({2})**|{3} RP|~~{4} RP~~|{5}{6}|" \
        .format(icon, sale.name, champLink, str(sale.sale), str(sale.regular), spotlightString, imageString)

def makePost(saleArray, dateRange, naLink, euwLink = "#"):
    # Automate rotation of sale rotation
    rotationSchedule = [[975, 750, 520], [1350, 975, 520], [975, 750, 520], [975, 975, 520]]
    nextRotation = rotationSchedule[lastrun.rotation % 4]

    faqArray = [
    ("I recently bought one of these skins/champions.",
        "Since the full May sale schedule was [already posted](http://na.leagueoflegends.com/en/news/store/sales/may-champion-and-skin-sale-schedule), partial refunds will not be offered for the sales announced in the schedule."),
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
        "| Icon | Skin/Champion | Sale Price | Regular Price | Media |\n" +
        "|:----:|:-------------:|:----------:|:-------------:|:-----:|\n" +
        sales + '\n'
        "Next skin sale: **{0} RP, {1} RP, {2} RP**. ".format(nextRotation[0], nextRotation[1], nextRotation[2]) +
        "Link to sale pages ([NA]({0}), [EUW]({1})).".format(naLink, euwLink) + '\n\n----\n\n' +
        "### Frequently Asked Questions\n\n" + faq + '----\n'
        "^This ^bot ^was ^written ^by ^/u/Pewqazz. ^Feedback, ^suggestions, ^and ^bug ^reports ^are ^welcomed ^in ^/r/LeagueSalesBot."
    )

def submitPost(postTitle, postBody):
    r = praw.Reddit(user_agent=settings.userAgent)
    r.login(settings.username, settings.password)
    for subreddit in settings.subreddits:
        r.submit(subreddit, postTitle, text=postBody)
    print kSuccess + "Post successfully submitted to " + ", ".join(settings.subreddits) + "." + kReset

    # Make appropriate changes to lastrun.py if post succeeds
    saleEndText = (datetime.datetime.now() + datetime.timedelta(4)).strftime("%Y-%m-%d")

    directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(directory, 'lastrun.py')
    f = open(path, 'r+')
    f.write("lastSaleEnd = \"{0}\"\nrotation = {1}\n".format(saleEndText, str((lastrun.rotation + 5) % 4)))
    f.close()

    print kSuccess + "Updated lastrun.py." + kReset


def getSpotlight(name, isSkin):
    content, slug = None, None
    if isSkin:
        url = "https://www.youtube.com/user/SkinSpotlights/search?query=" + name.replace(" ", "+") + "+skin+spotlight"
        header, content = httplib2.Http().request(url)
    else:
        url = "https://www.youtube.com/user/RiotGamesInc/search?query=" + name.replace(" ", "+") + "+champion+spotlight"
        header, content = httplib2.Http().request(url)

    vidRegex = re.compile("<h3 class=\"yt-lockup-title\"><a .* href=\"(\S*)\">.*<\/a><\/h3>")

    try:
        slug = re.findall(vidRegex, content)[0]
    except IndexError:
        sys.exit(kWarning + "Invalid YouTube lookup" + kReset)
    else:
        return "https://www.youtube.com" + slug


if __name__ == "__main__":
    testLink = False
    try:
        sys.argv[1]
    except IndexError:
        content, dateRange, naLink, euwLink = getContent()
    else:
        testLink = True
        content, dateRange, naLink, euwLink = getContent(sys.argv[1])

    saleRegex = re.compile("<h4>(?:<a href.+?>)*\s*?(.+?)\s*?(?:<\/a>)*<\/h4>\s+?<strike.*?>(\d{3,4})<\/strike> (\d{3,4}) RP")
    imageRegex = re.compile("(http://riot-web-static\.s3\.amazonaws\.com/images/news/Skin_Sales/\S*?\.jpg)")
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    for i in range(0, 6):
        saleArray[i].name, saleArray[i].regular, saleArray[i].sale = re.findall(saleRegex, content)[i]
        saleArray[i].spotlight = getSpotlight(saleArray[i].name, saleArray[i].isSkin)

        if saleArray[i].__class__ is Skin:
            saleArray[i].splash = re.findall(imageRegex, content)[(i*4)]
            saleArray[i].inGame = re.findall(imageRegex, content)[(i*4)+2]

    postTitle, postBody = makePost(saleArray, dateRange, naLink, euwLink)

    print kSpecial + postTitle + kReset

    for sale in saleArray:
        print "{0} ({1} RP), {2}".format(sale.name, sale.sale, sale.spotlight or "No spotlight found")

    if not testLink:
        submitPost(postTitle, postBody)

    sys.exit(0)
