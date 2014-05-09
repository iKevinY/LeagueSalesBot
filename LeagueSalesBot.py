#! /usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, re, datetime, time
import httplib2, praw
import settings, lastrun

"""Create classes for sale types (skins and champions)"""
class Sale():
    saleName = ""
    regularCost = 0
    saleCost = 0
    champName = ""
    wikiLink = ""
    icon = "[](/)"
class Skin(Sale):
    isSkin = True
    skinName = ""
    splashArt = ""
    inGameArt = ""
class Champ(Sale):
    isSkin = False
    splashName = ""

"""Define variables for ANSI-coloured terminal messages"""
kWarning = '\033[31m'
kSuccess = '\033[32m'
kSpecial = '\033[36m'
kReset = '\033[0m'

def getContent(testLink = None):
    if testLink:
        naLink = testLink if "//na" in testLink else "/#"
        euwLink = testLink if "//euw" in testLink else "/#"

        if not "-v" in sys.argv:
            print testLink + "...",

        try:
            header, content = httplib2.Http().request(testLink)
        except httplib2.ServerNotFoundError:
            sys.exit(kWarning + "Connection error. " + kReset + "Terminating script.")

        if header.status != 200:
            print (kWarning + str(header.status) + kReset)
            sys.exit(kWarning + "Terminating script." + kReset)
        else:
            if not "-v" in sys.argv:
                print kSuccess + "200" + kReset
            start, end = re.findall(".*(\d{4})-(\d{4})", testLink)[0]
            saleStart = datetime.datetime.strptime(start, "%m%d")
            saleEnd = datetime.datetime.strptime(end, "%m%d")

    else:
        """
        If lastrun.rotation is even, the last sale was posted on a Thursday so the next sale will start a day after the
        end date of the previous sale. Otherwise, the next sale will start on the same day that the last sale ended on.
        """
        lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, "%Y-%m-%d")
        saleStart = lastSaleEnd + datetime.timedelta((lastrun.rotation + 1) % 2)
        saleEnd = saleStart + datetime.timedelta(3) # Four-day-long sales

        mdStart, mdEnd = saleStart.strftime("%m%d"), saleEnd.strftime("%m%d")
        dmStart, dmEnd = saleStart.strftime("%d%m"), saleEnd.strftime("%d%m")

        links = [
            "http://na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(mdStart, mdEnd),
            "http://na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(dmStart, dmEnd),
            "http://euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(dmStart, dmEnd),
            "http://euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(mdStart, mdEnd)
        ]

        print "Last sale ended on " + kSpecial + lastSaleEnd.strftime("%B %-d") + kReset + ". Requesting sale pages."

        naLink, euwLink = None, None

        while (not naLink) and (not euwLink):
            for i, link in enumerate(links):
                try:
                    header, content = httplib2.Http().request(link)
                except httplib2.ServerNotFoundError:
                    sys.exit(kWarning + "Connection error. " + kReset + "Terminating script.")

                print link + "..." + ' ' * ("//na" in link),

                if header.status != 200:
                    print kWarning + str(header.status) + kReset
                else:
                    print kSuccess + "200" + kReset
                    naLink, euwLink = links[i % 2], links[i % 2 + 2]
                    break
            else:
                if "-r" in sys.argv:
                    print "Sleeping for 10 (c-X to force quit)..."
                    time.sleep(10)
                else:
                    sys.exit(kWarning + "Terminating script." + kReset)

        print kSuccess + "Post found!" + kReset + "\n"

    if saleStart.month == saleEnd.month:
        dateRange = "({0}–{1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%-d"))
    else:
        dateRange = "({0} – {1})".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%B %-d"))

    return content, dateRange, naLink, euwLink

def saleOutput(sale):
    """Generates one row of sale table"""
    if sale.isSkin:
        # Champions with multi-part names
        for key, value in settings.multiNames.iteritems():
            if re.match(key, sale.saleName):
                sale.champName = value
                break
        else:
            # Try all exception skins skins
            for key, v in settings.exceptSkins.iteritems():
                if sale.saleName == key:
                    sale.champName = value
                    break
            else:
                sale.champName = sale.saleName.rsplit(' ', 1)[1] # Champion name is final word of skin name

        mediaString = "**[Skin Spotlight]({0})**, [Splash Art]({1}), [In-Game]({2})".format(sale.spotlight, sale.splashArt, sale.inGameArt)
    else:
        # Generate correct splash art URL; champion name in URL is of format "Anivia", "Jarvan", "Masteryi", "Khazix"
        sale.splashName = sale.saleName.replace('.', '').replace("'", ' ')
        if sale.splashName == "Jarvan IV":
            sale.splashName = "Jarvan"

        try:
            sale.splashName = sale.splashName.rsplit(' ', 1)[0] + sale.splashName.rsplit(' ', 1)[1].lower()
        except IndexError:
            pass

        sale.champName = sale.saleName
        mediaString = "**[Champion Spotlight]({0})**, [Splash Art](http://riot-web-static.s3.amazonaws.com/images/news/Champ_Splashes/{1}_Splash.jpg)".format(sale.spotlight, sale.splashName)

    sale.wikiLink = "http://leagueoflegends.wikia.com/wiki/" + sale.champName.replace(" ", "_")
    sale.icon = "[](/{0})".format(re.sub('\ |\.|\'', '', sale.champName.lower())) # Removes ' ', '.', and "'" characters from name

    return "|{0}|**[{1}]({2})**|{3} RP|~~{4} RP~~|{5}|".format(sale.icon, sale.saleName, sale.wikiLink, str(sale.saleCost), str(sale.regularCost), mediaString)

def makePost(saleArray, dateRange, naLink, euwLink = "/#"):
    """Formats sale data into Reddit post"""
    rotationSchedule = [[975, 750, 520], [1350, 975, 520], [975, 750, 520], [975, 975, 520]]
    nextRotation = rotationSchedule[lastrun.rotation % 4]

    faq, sales = "", ""

    for q in settings.faqArray:
        faq = faq + "> **{0}**\n\n{1}\n\n".format(*q) # Uses * to unpack list into arguments

    for sale in saleArray:
        sales = sales + saleOutput(sale) + "\n"

    postTitle = "[Skin Sale] " + ", ".join([sale.saleName for sale in saleArray if sale.isSkin]) + " " + dateRange

    postBody = (
        "| Icon | Skin/Champion | Sale Price | Regular Price | Media |\n" +
        "|:----:|:-------------:|:----------:|:-------------:|:-----:|\n" +
        sales + '\n'
        "Next skin sale: **{0} RP, {1} RP, {2} RP**. ".format(*nextRotation) +
        "Link to sale pages ([NA]({0}), [EUW]({1})).\n\n----\n\n".format(naLink, euwLink) +
        "### Frequently Asked Questions\n\n" + faq + '----\n'
        "^Coded ^by ^/u/Pewqazz. ^Feedback, ^suggestions, ^and ^bug ^reports ^are ^welcomed ^in ^/r/LeagueSalesBot."
    )

    return postTitle, postBody


def getSpotlight(name, isSkin):
    """Finds appropriate champion or skin spotlight video for sale"""
    if isSkin:
        channel = "SkinSpotlights"
        suffix = "+skin+spotlight"
    else:
        channel = "RiotGamesInc"
        suffix = "+champion+spotlight"

    url = "https://www.youtube.com/user/" + channel + "/search?query=" + name.replace(" ", "+") + suffix
    header, content = httplib2.Http().request(url)

    try:
        slug, vidTitle = re.findall("<h3 class=\"yt-lockup-title\"><a .* href=\"(\S*)\">(.*)<\/a><\/h3>", content)[0]
    except IndexError:
        return "/#", None
    else:
        return "https://www.youtube.com" + slug, vidTitle

def updateLastRun():
    """Make appropriate changes to lastrun.py if post succeeds"""
    saleEndText = (datetime.datetime.now() + datetime.timedelta(4)).strftime("%Y-%m-%d")
    directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(directory, 'lastrun.py')
    with open(path, 'r+') as f:
        f.write("lastSaleEnd = \"{0}\"\nrotation = {1}\n".format(saleEndText, str((lastrun.rotation + 5) % 4)))

    print kSuccess + "Updated lastrun.py." + kReset

def submitPost(postTitle, postBody):
    """Post to subreddits defined in settings.py"""
    r = praw.Reddit(user_agent=settings.userAgent)
    r.login(settings.username, settings.password)
    for subreddit in settings.subreddits:
        r.submit(subreddit, postTitle, text=postBody)

    print kSuccess + "Post successfully submitted to " + ", ".join(settings.subreddits) + "." + kReset


def parseSales(content):
    """Finds sale data from sale page"""
    saleRegex = re.compile("<h4>(?:<a href.+?>)*\s*?(.+?)\s*?(?:<\/a>)*<\/h4>\s+?<strike.*?>(\d{3,4})<\/strike> (\d{3,4}) RP")
    imageRegex = re.compile("(http://riot-web-static\.s3\.amazonaws\.com/images/news/Skin_Sales/\S*?\.jpg)")
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    for i, sale in enumerate(saleArray):
        sale.saleName, sale.regularCost, sale.saleCost = re.findall(saleRegex, content)[i]
        sale.spotlight, sale.vidTitle = getSpotlight(sale.saleName, sale.isSkin)

        if not "-v" in sys.argv:
            print "{0} ({1} RP), {2}".format(sale.saleName, sale.saleCost, sale.vidTitle or "No spotlight found")

        if sale.isSkin:
            sale.splashArt = re.findall(imageRegex, content)[i * 4]
            sale.inGameArt = re.findall(imageRegex, content)[(i * 4) + 2]

    return saleArray

if __name__ == "__main__":
    testLink = next((sys.argv[i] for i, arg in enumerate(sys.argv) if "http://" in arg), None)

    content, dateRange, naLink, euwLink = getContent(testLink)
    saleArray = parseSales(content)
    postTitle, postBody = makePost(saleArray, dateRange, naLink, euwLink)

    if "-v" in sys.argv:
        print postBody
    else:
        print kSpecial + postTitle + kReset

    if not testLink:
        submitPost(postTitle, postBody)
        updateLastRun()

    sys.exit(0)
