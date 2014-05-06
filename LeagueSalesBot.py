#! /usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, re, datetime, time
import httplib2, praw
import settings, lastrun

# Create classes for sale types (skins and champions)
class Sale():
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
        if "//na" in testLink:
            naLink, euwLink = testLink, "/#"
        else:
            naLink, euwLink = "/#", testLink

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
        # Get string of end of last sale from lastrun.py
        lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, "%Y-%m-%d")

        # If lastrun.rotation is even, the last sale was posted on a Thursday so the next sale will start a day after the
        # end date of the previous sale. Otherwise, the next sale will start on the same day that the last sale ended on.
        saleStart = lastSaleEnd + datetime.timedelta((lastrun.rotation + 1) % 2)

        # Sales always end 3 days after they start (four-day-long sales)
        saleEnd = saleStart + datetime.timedelta(3)

        # Insert leading hyphen to strip leading zero
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
            for link in links:
                try:
                    header, content = httplib2.Http().request(link)
                except httplib2.ServerNotFoundError:
                    sys.exit(kWarning + "Connection error. " + kReset + "Terminating script.")

                print link + "..." + ' ' * ("//na" in link),

                if header.status != 200:
                    print kWarning + str(header.status) + kReset
                else:
                    print kSuccess + "200" + kReset
                    i = links.index(link)
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
    if sale.isSkin:
        # Champions with multi-part names
        for k, v in settings.twoParters.iteritems():
            if re.match(k, sale.name):
                champName = v
                break
        else:
            # Try all exception skins skins
            for k, v in settings.exceptSkins.iteritems():
                if sale.name == k:
                    champName = v
                    break
            else:
                champName = sale.name.rsplit(' ', 1)[1] # Champion name is final word of skin name

        spotlightString = "**[Skin Spotlight]({0})**, ".format(sale.spotlight)
        imageString = "[Splash Art]({0}), [In-Game]({1})".format(sale.splash, sale.inGame)
    else:
        champName = sale.name
        # Generate correct splash art URL; champion name in URL is of format "Anivia", "Jarvan", "Masteryi", "Khazix"
        splashName = sale.name.replace('.', '').replace("'", ' ')
        if splashName == "Jarvan IV":
            splashName = "Jarvan"
        try:
            splashName = splashName.rsplit(' ', 1)[0] + splashName.rsplit(' ', 1)[1].lower()
        except IndexError:
            pass

        spotlightString = "**[Champion Spotlight]({0})**, ".format(sale.spotlight)
        imageString = "[Splash Art](http://riot-web-static.s3.amazonaws.com/images/news/Champ_Splashes/{0}_Splash.jpg)".format(splashName)

    champLink = "http://leagueoflegends.wikia.com/wiki/" + champName.replace(" ", "_")
    iconName = re.sub('\ |\.|\'', '', champName.lower()) # Removes ' ', '.', and "'" characters from name
    icon = "[](/{0})".format(iconName)

    return "|{0}|**[{1}]({2})**|{3} RP|~~{4} RP~~|{5}{6}|".format(
        icon, sale.name, champLink, str(sale.sale), str(sale.regular), spotlightString, imageString)

def makePost(saleArray, dateRange, naLink, euwLink = "/#"):
    rotationSchedule = [[975, 750, 520], [1350, 975, 520], [975, 750, 520], [975, 975, 520]]
    nextRotation = rotationSchedule[lastrun.rotation % 4]

    faq, sales = "", ""

    for q in settings.faqArray:
        faq = faq + "> **{0}**".format(q[0]) + "\n\n" + "{0}".format(q[1]) + "\n\n"

    for sale in saleArray:
        sales = sales + saleOutput(sale) + "\n"

    postTitle = "[Skin Sale] " + saleArray[0].name + ", " + saleArray[1].name + ", " + saleArray[2].name + " " + dateRange

    postBody = (
        "| Icon | Skin/Champion | Sale Price | Regular Price | Media |\n" +
        "|:----:|:-------------:|:----------:|:-------------:|:-----:|\n" +
        sales + '\n'
        "Next skin sale: **{0} RP, {1} RP, {2} RP**. ".format(nextRotation[0], nextRotation[1], nextRotation[2]) +
        "Link to sale pages ([NA]({0}), [EUW]({1})).".format(naLink, euwLink) + '\n\n----\n\n' +
        "### Frequently Asked Questions\n\n" + faq + '----\n'
        "^Coded ^by ^/u/Pewqazz. ^Feedback, ^suggestions, ^and ^bug ^reports ^are ^welcomed ^in ^/r/LeagueSalesBot."
    )

    return postTitle, postBody


def getSpotlight(name, isSkin):
    if isSkin:
        url = "https://www.youtube.com/user/SkinSpotlights/search?query=" + name.replace(" ", "+") + "+skin+spotlight"
    else:
        url = "https://www.youtube.com/user/RiotGamesInc/search?query=" + name.replace(" ", "+") + "+champion+spotlight"

    header, content = httplib2.Http().request(url)

    try:
        slug, vidTitle = re.findall("<h3 class=\"yt-lockup-title\"><a .* href=\"(\S*)\">(.*)<\/a><\/h3>", content)[0]
    except IndexError:
        return "/#", None
    else:
        return "https://www.youtube.com" + slug, vidTitle


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


def parseData(content):
    saleRegex = re.compile("<h4>(?:<a href.+?>)*\s*?(.+?)\s*?(?:<\/a>)*<\/h4>\s+?<strike.*?>(\d{3,4})<\/strike> (\d{3,4}) RP")
    imageRegex = re.compile("(http://riot-web-static\.s3\.amazonaws\.com/images/news/Skin_Sales/\S*?\.jpg)")
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    for sale in saleArray:
        i = saleArray.index(sale)
        sale.name, sale.regular, sale.sale = re.findall(saleRegex, content)[i]
        sale.spotlight, sale.vidTitle = getSpotlight(sale.name, sale.isSkin)

        if not "-v" in sys.argv: # Terminal output
            print "{0} ({1} RP), {2}".format(sale.name, sale.sale, sale.vidTitle or "No spotlight found")

        if sale.isSkin:
            sale.splash = re.findall(imageRegex, content)[(i*4)]
            sale.inGame = re.findall(imageRegex, content)[(i*4)+2]

    return saleArray

if __name__ == "__main__":
    testLink = next((sys.argv[i] for i, s in enumerate(sys.argv) if "http://" in s), None)

    content, dateRange, naLink, euwLink = getContent(testLink)
    saleArray = parseData(content)
    postTitle, postBody = makePost(saleArray, dateRange, naLink, euwLink)

    if "-v" in sys.argv:
        print postBody
    else:
        print kSpecial + postTitle + kReset

    if not testLink:
        submitPost(postTitle, postBody)
        pass

    sys.exit(0)
