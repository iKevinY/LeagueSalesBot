#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import re
import datetime
import time
import math

import httplib2
import praw
import click

import settings
import lastrun

"""Create classes for sale types (skins and champions)"""
class Sale():
    icon = ""
    saleName = ""
    wikiLink = ""
    salePrice = ""
    regularPrice = ""
    champName = ""

class Skin(Sale):
    isSkin = True
    splashArt = ""
    inGameArt = ""

class Champ(Sale):
    isSkin = False
    infoPage = ""


"""Define functions for printing ANSI-coloured terminal messages"""
def sSpecial(s): return '\033[36m' + s + '\033[0m'
def sSuccess(s): return '\033[32m' + s + '\033[0m'
def sWarning(s): return '\033[31m' + s + '\033[0m'


def load_page(link):
    try:
        resp, content = httplib2.Http().request(link)
    except httplib2.ServerNotFoundError:
        sys.exit(sWarning("Connection error."))
    else:
        return resp, content


def format_range(saleStart, saleEnd):
    """Returns properly formatted date range for sale start and end"""
    if saleStart.month == saleEnd.month:
        return "{0}–{1}".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%-d"))
    else:
        return"{0} – {1}".format(saleStart.strftime("%B %-d"), saleEnd.strftime("%B %-d"))


def get_content(testLink, delay, refresh, verbose):
    """Loads appropriate content based on most recent sale or supplied test link"""
    if testLink:
        naLink = testLink if "//na" in testLink else "/#"
        euwLink = testLink if "//euw" in testLink else "/#"

        if not verbose:
            print testLink + "...",

        resp, content = load_page(testLink)

        if resp.status != 200:
            print (sWarning(str(resp.status)))
            sys.exit(sWarning("Terminating script."))
        else:
            if not verbose:
                print sSuccess(str(resp.status))

            try:
                start, end = re.findall(".*(\d{4})-(\d{4})", testLink)[0]
            except IndexError:
                sys.exit(sWarning("Invalid sale page URL."))

            saleStart = datetime.datetime.strptime(start, "%m%d")
            saleEnd = datetime.datetime.strptime(end, "%m%d")
            dateRange = format_range(saleStart, saleEnd)

    else:
        """
        If lastrun.rotation is an even value, the last sale was posted on a Thursday
        so the next sale will start a day after the end date of the previous sale.
        Otherwise, the next sale will start on the same day that the last sale ended on.
        """
        lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, "%Y-%m-%d")
        saleStart = lastSaleEnd + datetime.timedelta((lastrun.rotation + 1) % 2)
        saleEnd = saleStart + datetime.timedelta(3) # Four-day sales

        dateRange = format_range(saleStart, saleEnd)

        monthDate = saleStart.strftime("%m%d"), saleEnd.strftime("%m%d")
        dateMonth = saleStart.strftime("%d%m"), saleEnd.strftime("%d%m")

        links = ["http://{0}.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{1}-{2}".format(
            l[0], *l[1]) for l in (("na", monthDate), ("na", dateMonth), ("euw", dateMonth), ("euw", monthDate))]

        naLink, euwLink = None, None

        print "Last sale ended on {0}. Requesting {1} sale.".format(
            sSpecial(lastSaleEnd.strftime("%B %-d")), sSpecial(dateRange))

        if delay:
            print "Sleeping for {0} hour{1}.".format(str(delay), 's' * (delay is not 1))
            time.sleep(delay * 60 * 60)

        while not (naLink or euwLink):
            for i, link in enumerate(links):
                resp, content = load_page(link)
                print link + "..." + ' ' * ("//na" in link),

                if resp.status != 200:
                    print sWarning(str(resp.status))
                else:
                    print sSuccess(str(resp.status))
                    naLink, euwLink = links[i % 2], links[(i % 2) + 2]
                    break
            else:
                if refresh:
                    print "Reloading every 15 seconds (c-C to force quit)..."
                    time.sleep(15)
                else:
                    sys.exit(sWarning("Terminating script."))

        print sSuccess("Post found!") + '\n'

    saleList = re.findall("<h4>(?:<a .+?>)*\s*?(.+?)\s*?(?:<\/a>)*<\/h4>\s+?<strike.*?>(\d+?)<\/strike> (\d+?) RP", content)
    skinList = re.findall("(http://riot-web-static\.s3\.amazonaws\.com/images/news/Skin_Sales/\S+?\.jpg)", content)
    infoList = re.findall("\"(http://gameinfo.(?:na|euw).leagueoflegends.com/en/game-info/champions/\S+?)\"", content)

    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    for i, sale in enumerate(saleArray):
        try:
            sale.saleName, sale.regularPrice, sale.salePrice = saleList[i]
        except IndexError:
            sys.exit(sWarning("Sale data could not be parsed by regexes."))

        if sale.isSkin:
            sale.splashArt = skinList[i * 4]
            sale.inGameArt = skinList[(i * 4) + 2]
        else:
            sale.infoPage = infoList[(i - 3) * 2].replace(".euw.", ".na.")

    # Sorts sale array by skins > champions and then by price
    saleArray.sort(key=lambda sale: (sale.isSkin, sale.salePrice), reverse=True)

    return naLink, euwLink, dateRange, saleArray


def sale_output(sale):
    """Generates row of sale table for sale item"""
    if sale.isSkin:
        # Champions with two-part names
        for regex, champion in settings.twoParts.iteritems():
            if re.match(regex, sale.saleName):
                sale.champName = champion
                break
        else:
            # Try all exception skins
            if sale.saleName in settings.exceptSkins:
                sale.champName = settings.exceptSkins[sale.saleName]
            else:
                sale.champName = sale.saleName.split()[-1]

        resourceString = "**[Skin Spotlight]({0})**, [Splash Art]({1}), [In-Game]({2})".format(
            sale.spotlight, sale.splashArt, sale.inGameArt)
    else:
        sale.champName = sale.saleName
        resourceString = ("**[Champion Spotlight]({0})**, [Official Info Page]({1})".format(sale.spotlight, sale.infoPage))

    sale.wikiLink = "http://leagueoflegends.wikia.com/wiki/" + sale.champName.replace(" ", "_")

    # Remove spaces, periods, and apostrophes from champion name to generate icon string
    sale.icon = "[](/{0})".format(re.sub('\ |\.|\'', '', sale.champName.lower()))

    return "|{0}|**[{1}]({2})**|{3} RP|~~{4} RP~~|{5}|".format(
        sale.icon, sale.saleName, sale.wikiLink, sale.salePrice, sale.regularPrice, resourceString)


def make_post(saleArray, dateRange, naLink, euwLink):
    """Formats sale data into Reddit post"""

    # Determine prices of next sale skins given the previous sale (stored in lastrun.py)
    nextRotation = ((975, 750, 520), (1350, 975, 520), (975, 750, 520), (975, 975, 520))[lastrun.rotation % 4]

    return (
        "| Icon | Skin/Champion | Sale Price | Regular Price | Resources |\n" +
        "|:----:|:-------------:|:----------:|:-------------:|:---------:|\n" +
        ''.join(sale_output(sale) + "\n" for sale in saleArray) +
        "Next skin sale: **{0} RP, {1} RP, {2} RP**. ".format(*nextRotation) +
        "Link to sale pages ([NA]({0}), [EUW]({1})).".format(naLink, euwLink) +
        "\n\n----\n\n" +
        "## Frequently Asked Questions\n\n" +
        '\n\n'.join("> **{0}**\n\n{1}".format(*qa) for qa in settings.faqArray) +
        "\n\n----\n" +
        "^Coded ^by ^/u/Pewqazz. ^Feedback, ^suggestions, ^and ^bug ^reports ^are ^welcomed ^in ^/r/LeagueSalesBot."
    )


def get_spotlight(name, isSkin):
    """Finds appropriate champion or skin spotlight video for sale"""
    channel, suffix = ("SkinSpotlights", "+Skin+Spotlight") if isSkin else ("RiotGamesInc", "+Champion+Spotlight")
    resp, content = load_page("https://www.youtube.com/user/{0}/search?query={1}".format(
        channel, name.replace(" ", "+"), suffix))

    try:
        slug, spotlightName = re.findall("<h3 class=\"yt-lockup-title\"><a .* href=\"(\S*)\">(.*)<\/a><\/h3>", content)[0]
    except IndexError:
        return "/#", "No spotlight found."
    else:
        return "https://www.youtube.com" + slug, spotlightName


def submit_post(postTitle, postBody):
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


def manual_post():
    """Manually enter sale data from the CLI"""
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    inputDate = str(datetime.datetime.now().year) + click.prompt('Enter sale start date [MMDD]', type=str)
    saleStart = datetime.datetime.strptime(inputDate, "%Y%m%d")
    saleEnd = saleStart + datetime.timedelta(3)

    dateRange = format_range(saleStart, saleEnd)

    monthDate = datetime.datetime.strftime(saleStart, "%m%d"), datetime.datetime.strftime(saleEnd, "%m%d")
    dateMonth = datetime.datetime.strftime(saleStart, "%d%m"), datetime.datetime.strftime(saleEnd, "%d%m")
    naLink, euwLink = ("http://{0}.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{1}-{2}".format(
        l[0], *l[1]) for l in (("na", monthDate), ("euw", dateMonth)))

    for i, sale in enumerate(saleArray):
        print "\nSkin #{}".format(i + 1) if sale.isSkin else "\nChampion #{}".format(i - 2)

        sale.saleName = click.prompt('Enter sale name', value_proc=str)
        sale.regularPrice = click.prompt('Enter regular cost', value_proc=str)
        sale.salePrice = str(math.floor(int(sale.regularPrice)))

        if sale.isSkin:
            sale.splashArt = click.prompt('Splash art URL', value_proc=str, default="/#")
            sale.inGameArt = click.prompt('In-game art URL', value_proc=str, default="/#")
        else:
            sale.infoPage = click.prompt('Info page URL', value_proc=str, default="/#")

    return naLink, euwLink, dateRange, saleArray


@click.command()
@click.argument('testLink', required=False)
@click.option('--delay', '-d', 'delay', default=0, help='Delay before running script.', metavar='<hours>')
@click.option('--manual', '-m', 'manual', is_flag=True, help='Manually create post.')
@click.option('--refresh', '-r', 'refresh', is_flag=True, help='Automatically refresh sale pages.')
@click.option('--verbose', '-v', 'verbose', is_flag=True, help='Output entire post body (for piping to pbcopy).')

def main(testLink, delay, manual, refresh, verbose):
    """
    Python script that generates Reddit post summarizing the biweekly League of
    Legends champion and skin sales. Uses the httplib2 and PRAW libraries.
    """

    naLink, euwLink, dateRange, saleArray = manual_post() if manual else get_content(testLink, delay, refresh, verbose)

    postTitle = "[Skin Sale] " + ", ".join(sale.saleName for sale in saleArray if sale.isSkin) + " (" + dateRange + ")"

    if not verbose:
        print sSpecial(postTitle)

    # Get spotlights and print to terminal
    for sale in saleArray:
        sale.spotlight, sale.spotlightName = get_spotlight(sale.saleName, sale.isSkin)
        if not verbose:
            print '{: <30}'.format(sale.saleName) + sale.salePrice + " RP\t" + sale.spotlightName

    postBody = make_post(saleArray, dateRange, naLink, euwLink)

    if verbose:
        print postBody

    if not testLink:
        if manual and not click.confirm('Post to Reddit?'):
            sys.exit(sWarning("Did not post."))
        else:
            submit_post(postTitle, postBody)
            pass

    sys.exit(0)


if __name__ == "__main__":
    main()
