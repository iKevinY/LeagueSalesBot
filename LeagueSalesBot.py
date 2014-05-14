#! /usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, re, datetime, time, textwrap, math
import httplib2, praw, click
import settings, lastrun

"""Create classes for sale types (skins and champions)"""
class Sale():
    saleName = ""
    regularCost = ""
    saleCost = ""
    champName = ""
    wikiLink = ""
    icon = ""
class Skin(Sale):
    isSkin = True
    splashArt = ""
    inGameArt = ""
class Champ(Sale):
    isSkin = False
    infoPage = ""


"""Define functions for printing ANSI-coloured terminal messages"""
sReset = '\033[0m'
sSpecial = lambda s: '\033[36m' + s + sReset
sSuccess = lambda s: '\033[32m' + s + sReset
sWarning = lambda s: '\033[31m' + s + sReset


def formatRange(saleStart, saleEnd):
    """Returns properly formatted date range for sale start and end"""
    if saleStart.month == saleEnd.month:
        return "{0}–{1}".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%-d"))
    else:
        return"{0} – {1}".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%B %-d"))


def getContent(testLink, delay, refresh, verbose):
    """Loads appropriate content based on most recent sale or supplied test link"""
    if testLink:
        naLink = testLink if "//na" in testLink else "/#"
        euwLink = testLink if "//euw" in testLink else "/#"

        if not verbose:
            print testLink + "...",

        try:
            header, content = httplib2.Http().request(testLink)
        except httplib2.ServerNotFoundError:
            sys.exit(sWarning("Connection error."))

        if header.status != 200:
            print (sWarning(str(header.status)))
            sys.exit(sWarning("Terminating script."))
        else:
            if not verbose:
                print sSuccess("200")

            try:
                start, end = re.findall(".*(\d{4})-(\d{4})", testLink)[0]
            except IndexError:
                sys.exit(sWarning("Invalid sale page URL."))

            saleStart = datetime.datetime.strptime(start, "%m%d")
            saleEnd = datetime.datetime.strptime(end, "%m%d")
            dateRange = formatRange(saleStart, saleEnd)

    else:
        """
        If lastrun.rotation is an even value, the last sale was posted on a Thursday
        so the next sale will start a day after the end date of the previous sale.
        Otherwise, the next sale will start on the same day that the last sale ended on.
        """
        lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, "%Y-%m-%d")
        saleStart = lastSaleEnd + datetime.timedelta((lastrun.rotation + 1) % 2)
        saleEnd = saleStart + datetime.timedelta(3) # Four-day-long sales

        dateRange = formatRange(saleStart, saleEnd)

        monthDate = saleStart.strftime("%m%d"), saleEnd.strftime("%m%d")
        dateMonth = saleStart.strftime("%d%m"), saleEnd.strftime("%d%m")

        links = ("http://{0}.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{1}-{2}".format(
            l[0], *l[1]) for l in (("na", monthDate), ("na", dateMonth), ("euw", dateMonth), ("euw", monthDate)))

        naLink, euwLink = None, None

        print "Last sale ended on {0}. Requesting {1} sale.".format(
            sSpecial(lastSaleEnd.strftime("%B %-d")), sSpecial(dateRange))

        if delay:
            print "Sleeping for {0} hour{1}.".format(str(delay), 's' * (delay is not 1))
            time.sleep(delay * 60 * 60)

        while not (naLink or euwLink):
            for i, link in enumerate(links):
                try:
                    header, content = httplib2.Http().request(link)
                except httplib2.ServerNotFoundError:
                    sys.exit(sWarning("Connection error."))

                print link + "..." + ' ' * ("//na" in link),

                if header.status != 200:
                    print sWarning(str(header.status))
                else:
                    print sSuccess("200")
                    naLink, euwLink = links[i % 2], links[(i % 2) + 2]
                    break
            else:
                if refresh:
                    print "Reloading every 15 seconds (c-C to force quit)..."
                    time.sleep(15)
                else:
                    sys.exit(sWarning("Terminating script."))

        print sSuccess("Post found!") + '\n'

    saleRegex = re.compile("<h4>(?:<a href.+?>)*\s*?(.+?)\s*?(?:<\/a>)*<\/h4>\s+?<strike.*?>(\d{3,4})<\/strike> (\d{3,4}) RP")
    skinRegex = re.compile("(http://riot-web-static\.s3\.amazonaws\.com/images/news/Skin_Sales/\S+?\.jpg)")
    infoRegex = re.compile("\"(http://gameinfo.na.leagueoflegends.com/en/game-info/champions/\S+?)\"")

    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    for i, sale in enumerate(saleArray):
        sale.saleName, sale.regularCost, sale.saleCost = re.findall(saleRegex, content)[i]

        if sale.isSkin:
            sale.splashArt = re.findall(skinRegex, content)[i * 4]
            sale.inGameArt = re.findall(skinRegex, content)[(i * 4) + 2]
        else:
            sale.infoPage = re.findall(infoRegex, content)[(i - 3) * 2]

    return naLink, euwLink, dateRange, saleArray

def saleOutput(sale):
    """Generates row of sale table for sale item"""
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

        mediaString = "**[Skin Spotlight]({0})**, [Splash Art]({1}), [In-Game]({2})".format(
            sale.spotlight, sale.splashArt, sale.inGameArt)
    else:
        sale.champName = sale.saleName
        mediaString = ("**[Champion Spotlight]({0})**, [Official Info Page]({1})".format(sale.spotlight, sale.infoPage))

    sale.wikiLink = "http://leagueoflegends.wikia.com/wiki/" + sale.champName.replace(" ", "_")

    # Remove spaces, periods, and apostrophes from name to generate champion icon
    sale.icon = "[](/{0})".format(re.sub('\ |\.|\'', '', sale.champName.lower()))

    return "|{0}|**[{1}]({2})**|{3} RP|~~{4} RP~~|{5}|".format(
        sale.icon, sale.saleName, sale.wikiLink, str(sale.saleCost), str(sale.regularCost), mediaString)


def makePost(saleArray, dateRange, naLink, euwLink):
    """Formats sale data into Reddit post"""
    rotationSchedule = ((975, 750, 520), (1350, 975, 520), (975, 750, 520), (975, 975, 520))
    nextRotation = rotationSchedule[lastrun.rotation % 4]

    postArguments = (
        ''.join(saleOutput(sale) + "\n" for sale in saleArray), # Sale rows
        nextRotation[0], nextRotation[1], nextRotation[2], naLink, euwLink, # Miscellaneous variables
        ''.join("> **{0}**\n\n{1}\n\n".format(*qa) for qa in settings.faqArray) # FAQ
    )

    return textwrap.dedent('''
        | Icon | Skin/Champion | Sale Price | Regular Price | Media |
        |:----:|:-------------:|:----------:|:-------------:|:-----:|
        {0}
        Next skin sale: **{1} RP, {2} RP, {3} RP**. Link to sale pages ([NA]({4}), [EUW]({5})).

        ----

        ## Frequently Asked Questions

        {6}
        ----
        ^Coded ^by ^/u/Pewqazz. ^Feedback, ^suggestions, ^and ^bug ^reports ^are ^welcomed ^in ^/r/LeagueSalesBot.
        ''').format(*postArguments)


def getSpotlight(name, isSkin):
    """Finds appropriate champion or skin spotlight video for sale"""
    if isSkin:
        channel = "SkinSpotlights"
        suffix = "+skin+spotlight"
    else:
        channel = "RiotGamesInc"
        suffix = "+champion+spotlight"

    try:
        header, content = httplib2.Http().request(
            "https://www.youtube.com/user/" + channel + "/search?query=" + name.replace(" ", "+") + suffix)
    except httplib2.ServerNotFoundError:
        sys.exit(sWarning("Connection error."))

    try:
        slug, spotlightName = re.findall("<h3 class=\"yt-lockup-title\"><a .* href=\"(\S*)\">(.*)<\/a><\/h3>", content)[0]
    except IndexError:
        return "/#", None
    else:
        return "https://www.youtube.com" + slug, spotlightName


def submitPost(postTitle, postBody):
    """Post to subreddits defined in settings.py and updates lastrun.py"""
    r = praw.Reddit(user_agent=settings.userAgent)
    r.login(settings.username, settings.password)
    for subreddit in settings.subreddits:
        r.submit(subreddit, postTitle, text=postBody)

    print sSuccess("Post successfully submitted to " + ", ".join(settings.subreddits) + ".")

    saleEndText = (datetime.datetime.now() + datetime.timedelta(4)).strftime("%Y-%m-%d")
    directory = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(directory, 'lastrun.py')
    with open(path, 'r+') as f:
        f.write("lastSaleEnd = \"{0}\"\nrotation = {1}\n".format(saleEndText, str((lastrun.rotation + 5) % 4)))

    print sSuccess("Updated lastrun.py.")


def manualPost():
    """Manually enter sale data from the CLI"""
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    inputDate = str(datetime.datetime.now().year) + click.prompt('Enter sale start date [MMDD]', type=str)
    saleStart = datetime.datetime.strptime(inputDate, "%Y%m%d")
    saleEnd = saleStart + datetime.timedelta(3)

    dateRange = formatRange(saleStart, saleEnd)

    mdStart, mdEnd = datetime.datetime.strftime(saleStart, "%m%d"), datetime.datetime.strftime(saleEnd, "%m%d")
    dmStart, dmEnd = datetime.datetime.strftime(saleStart, "%d%m"), datetime.datetime.strftime(saleEnd, "%d%m")
    naLink = "http://na.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(mdStart, mdEnd)
    euwLink = "http://euw.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{0}-{1}".format(dmStart, dmEnd)

    for i, sale in enumerate(saleArray):
        print "\nSkin #{}".format(i + 1) if sale.isSkin else "\nChampion #{}".format(i - 2)

        sale.saleName = str(click.prompt('Enter sale name', type=str))
        sale.regularPrice = click.prompt('Enter regular cost', type=str)
        sale.salePrice = str(math.floor(int(sale.regularPrice)))

        if sale.isSkin:
            sale.splashArt = str(click.prompt('Splash art URL', type=str))
            sale.inGameArt = str(click.prompt('In-game art URL', type=str))

    return naLink, euwLink, dateRange, saleArray


@click.command()
@click.argument('testLink', required=False)
@click.option('--delay', '-d', 'delay', default=0, metavar='<hours>', help='Delay before running script.')
@click.option('--manual', '-m', 'manual', is_flag=True, help='Manually create post.')
@click.option('--refresh', '-r', 'refresh', is_flag=True, help='Automatically refresh sale pages.')
@click.option('--verbose', '-v', 'verbose', is_flag=True, help='Output entire post body (for piping to pbcopy).')

def main(testLink, delay, manual, refresh, verbose):
    """
    Python script that generates Reddit post summarizing the biweekly League of
    Legends champion and skin sales. Uses the httplib2 and PRAW libraries.
    """

    naLink, euwLink, dateRange, saleArray = manualPost() if manual else getContent(testLink, delay, refresh, verbose)

    # Generate post title
    postTitle = "[Skin Sale] " + ", ".join(sale.saleName for sale in saleArray if sale.isSkin) + " (" + dateRange + ")"

    if not verbose:
        print sSpecial(postTitle)

    # Get spotlights and print to terminal
    for sale in saleArray:
        sale.spotlight, sale.spotlightName = getSpotlight(sale.saleName, sale.isSkin)
        if not verbose:
            print '{: <30}'.format(sale.saleName) + sale.saleCost + " RP\t" + sale.spotlightName

    postBody = makePost(saleArray, dateRange, naLink, euwLink)

    if verbose:
        print postBody

    if not testLink:
        if manual and not click.confirm('Post to Reddit?'):
            sys.exit(sWarning("Did not post."))
        else:
            submitPost(postTitle, postBody)

    sys.exit(0)

if __name__ == "__main__":
    main()
