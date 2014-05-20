#! /usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, re, datetime, time

import httplib2
import praw
import click

import settings
import lastrun

"""Create classes for sale types (skins and champions)"""
class Sale():
    saleName = ''
    salePrice = ''
    regularPrice = ''
    spotlight = None

class Skin(Sale):
    isSkin = True
    splashArt = None
    inGameArt = None

class Champ(Sale):
    isSkin = False
    infoPage = None


"""Define functions for printing ANSI-coloured terminal messages"""
def sSpecial(s): return '\033[1;36m' + s + '\033[0m'
def sSuccess(s): return '\033[32m' + s + '\033[0m'
def sWarning(s): return '\033[31m' + s + '\033[0m'


def load_page(link):
    try:
        resp, content = httplib2.Http().request(link)
        return resp, content
    except httplib2.ServerNotFoundError:
        sys.exit(sWarning("Connection error."))


def format_range(saleStart, saleEnd):
    """Returns properly formatted date range for sale start and end"""
    if saleStart.month == saleEnd.month:
        return '{0}–{1}'.format(saleStart.strftime('%B %-d'), saleEnd.strftime('%-d'))
    else:
        return '{0} – {1}'.format(saleStart.strftime('%B %-d'), saleEnd.strftime('%B %-d'))


def format_resources(sale):
    """Formats sale resources into string if value is not None"""
    if sale.isSkin:
        resources = (
            (sale.spotlight, 'Skin Spotlight'),
            (sale.splashArt, 'Splash Art'),
            (sale.inGameArt, 'In-Game'),
        )

    else:
        resources = (
            (sale.spotlight, 'Champion Spotlight'),
            (sale.infoPage, 'Official Info Page'),
        )

    return ', '.join(
        ['[{0}]({1})'.format(text, link) for link, text in resources if link is not None])


def get_content(testLink, delay=None, refresh=None, verbose=None):
    """Loads appropriate content based on most recent sale or supplied test link"""
    if testLink:
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
                start, end = re.findall('.*(\d{4})-(\d{4})', testLink)[0]
            except IndexError:
                sys.exit(sWarning("Invalid sale page URL."))

            for dateFormat in ('%m%d', '%d%m'):
                try:
                    saleStart = datetime.datetime.strptime(start, dateFormat)
                    saleEnd = datetime.datetime.strptime(end, dateFormat)
                    dateRange = format_range(saleStart, saleEnd)
                    break
                except ValueError:
                    pass
            else:
                sys.exit(sWarning("Date range could not be determined from sale URL."))

            saleLink = testLink

    else:
        """
        If lastrun.rotation is an even value, the last sale was posted on a Thursday
        so the next sale will start a day after the end date of the previous sale.
        Otherwise, the next sale will start on the same day that the last sale ended on.
        """
        lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, '%Y-%m-%d')
        saleStart = lastSaleEnd + datetime.timedelta((lastrun.lastRotation + 1) % 2)
        saleEnd = saleStart + datetime.timedelta(3) # Four-day sales

        dateRange = format_range(saleStart, saleEnd)

        regions = ('na', 'euw')
        dateFormats = ('%m%d', '%d%m')
        linkPerms = ((region, saleStart.strftime(format), saleEnd.strftime(format))
            for region in regions for format in dateFormats)

        baseLink = 'http://{0}.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{1}-{2}'
        links = [baseLink.format(*perm) for perm in linkPerms]

        print "Last sale ended on {0}. Requesting {1} sale pages.".format(
            sSpecial(lastSaleEnd.strftime("%B %-d")), sSpecial(dateRange))

        if delay:
            print "Sleeping for {0} hour{1}.".format(str(delay), "s" * (delay != 1))
            time.sleep(delay * 60 * 60)

        saleLink = None

        while not saleLink:
            for link in links:
                resp, content = load_page(link)
                print link + "...\t",

                if resp.status != 200:
                    print sWarning(str(resp.status))
                else:
                    print sSuccess(str(resp.status))
                    saleLink = link
                    break
            else:
                if refresh:
                    refreshDelay = 15
                    print "Reloading every {0} seconds (c-C to force quit)...".format(refreshDelay)
                    time.sleep(refreshDelay)
                else:
                    sys.exit(sWarning("Terminating script."))

    # Define regexes for sales, skin art, and champion info pages
    regexes = (
        '<h4>(?:<a .+?>)*\s*?(.+?)\s*?(?:<\/a>)*<\/h4>\s+?<strike.*?>(\d+?)<\/strike> (\d+?) RP',
        '<a class="lightbox.*?" href="(\S+?)">\n<img .*></a>',
        '<a href="(http://gameinfo.(?:na|euw).leagueoflegends.com/en/game-info/champions/\S+?)"',
    )

    saleList, skinList, infoList = (re.findall(regex, content) for regex in regexes)

    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    for i, sale in enumerate(saleArray):
        try:
            sale.saleName, sale.regularPrice, sale.salePrice = saleList[i]
        except IndexError:
            sys.exit(sWarning("Sale data could not be parsed by regexes."))

        if sale.isSkin:
            try:
                sale.splashArt = skinList[i*2]
                sale.inGameArt = skinList[i*2 + 1]
            except IndexError:
                sWarning("Art for " + sale.saleName + " not parsed.")
                sale.splashArt, sale.inGameArt = None, None
        else:
            try:
                # Force NA champion info page
                sale.infoPage = infoList[(i - 3) * 2].replace('.euw.', '.na.')
            except IndexError:
                sWarning("Info page for " + sale.saleName + " not parsed.")
                sale.infoPage = None

    # Sorts sale array by skins > champions and then by price (in reverse)
    saleArray.sort(key=lambda sale: (sale.isSkin, sale.salePrice), reverse=True)

    return saleLink, dateRange, saleArray


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
    else:
        sale.champName = sale.saleName

    sale.wikiLink = 'http://leagueoflegends.wikia.com/wiki/' + sale.champName.replace(' ', '_')

    # Remove spaces, periods, and apostrophes from champion name to generate icon string
    sale.icon = '[](/{0})'.format(re.sub('\ |\.|\'', '', sale.champName.lower()))

    return '|{0}|**[{1}]({2})**|{3} RP|~~{4} RP~~|{5}|'.format(
        sale.icon, sale.saleName, sale.wikiLink, sale.salePrice,
        sale.regularPrice, format_resources(sale))


def make_post(saleArray, saleLink):
    """Formats sale data into Reddit post"""
    # Determine prices of next sale skins given the previous sale (stored in lastrun.py)
    rotation = [(975, 750, 520), (1350, 975, 520), (975, 750, 520), (975, 975, 520)]
    nextRotation = rotation[(lastrun.lastRotation + 2) % 4]

    return (
        '| Icon | Skin/Champion | Sale Price | Regular Price | Resources |\n' +
        '|:----:|:-------------:|:----------:|:-------------:|:---------:|\n' +
        '\n'.join(sale_output(sale) for sale in saleArray) + '\n\n' +
        'Next skin sale: **{0} RP, {1} RP, {2} RP**. '.format(*nextRotation) +
        '[Link to sale page]({0}).'.format(saleLink) +
        '\n\n----\n\n' +
        '## Frequently Asked Questions\n\n' +
        '\n\n'.join('> **{0}**\n\n{1}'.format(*qa) for qa in settings.faqArray) +
        '\n\n----\n\n' +
        '^Coded ^by ^/u/Pewqazz. ^Feedback, ^suggestions, ^and ^bug ^reports '
        '^are ^welcomed ^in ^/r/LeagueSalesBot.'
    )


def get_spotlight(sale, verbose):
    """Finds appropriate champion or skin spotlight video for sale"""
    if sale.isSkin:
        channel, suffix = ('SkinSpotlights', '+Skin+Spotlight')
    else:
        channel, suffix = ('RiotGamesInc', '+Champion+Spotlight')

    searchTerm = sale.saleName.replace(' ', '+')
    videoPage = 'https://www.youtube.com/user/{0}/search?query={1}'.format(channel, searchTerm, suffix)
    resp, content = load_page(videoPage)

    try:
        searchResult = '<h3 class="yt-lockup-title"><a.*?href="(\S*)">(.*)</a></h3>'
        slug, spotlightName = re.findall(searchResult, content)[0]
        spotlightURL = 'https://www.youtube.com' + slug
    except IndexError:
        spotlightURL = None

    if not verbose:
        print '{: <30}'.format(sale.saleName) + sale.salePrice + ' RP\t' + spotlightName

    return spotlightURL


def post_to_reddit(postTitle, postBody, saleLink):
    """Posts self or link posts to subreddits as defined in settings.py"""
    r = praw.Reddit(user_agent=settings.userAgent)
    r.login(settings.username, settings.password)
    rateDelay = 10

    for subreddit, isLinkPost in settings.subreddits:
        if isLinkPost:
            submission = r.submit(subreddit, postTitle, url=saleLink)
            time.sleep(rateDelay)
        else:
            submission = r.submit(subreddit, postTitle, text=postBody)

        print sSuccess("Submitted {0} post at {1}/".format(
            "link" if isLinkPost else "self",
            submission.permalink.rsplit('/', 2)[0])
        )

        if isLinkPost:
            submission.add_comment(postBody)
            print sSuccess("Commented on link post at /r/{0}.".format(subreddit))

        time.sleep(rateDelay)


def update_lastrun(saleEnd=None, rotationIndex=None):
    """Updates lastrun.py with sale date and rotation information"""

    if saleEnd:
        saleEndText = saleEnd
    else:
        saleEndText = (datetime.datetime.now() + datetime.timedelta(4)).strftime('%Y-%m-%d')

    if rotationIndex:
        rotationText = rotationIndex
    else:
        rotationText = str((lastrun.lastRotation + 1) % 4)

    directory = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(directory, 'lastrun.py')

    print sSuccess("Modified lastrun.py from ({0}, {1})".format(
        lastrun.lastSaleEnd, lastrun.lastRotation)),

    with open(path, 'r+') as f:
        f.write('lastSaleEnd = "{0}"\nlastRotation = {1}\n'.format(saleEndText, rotationText))

    print sSuccess("to ({0}, {1}).".format(saleEndText, rotationText))


def manual_post():
    """Manually enter sale data from the CLI"""
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    inputDate = str(datetime.datetime.now().year) + click.prompt("Enter sale start date [MMDD]", type=str)
    saleStart = datetime.datetime.strptime(inputDate, '%Y%m%d')
    saleEnd = saleStart + datetime.timedelta(3)

    dateRange = format_range(saleStart, saleEnd)

    dateFormat = datetime.datetime.strftime(saleStart, '%m%d'), datetime.datetime.strftime(saleEnd, '%m%d')
    baseLink = 'http://{0}.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{1}-{2}'
    saleLink = (baseLink.format('na', dateFormat[0], dateFormat[1]))

    for i, sale in enumerate(saleArray):
        print "\nSkin #{}".format(i + 1) if sale.isSkin else "\nChampion #{}".format(i - 2)

        sale.saleName = click.prompt("Enter sale name", value_proc=str)
        sale.regularPrice = click.prompt("Enter regular cost", value_proc=str)
        sale.salePrice = str(int(sale.regularPrice) // 2)

        if sale.isSkin:
            sale.splashArt = click.prompt("Splash art URL", value_proc=str, default='/#')
            sale.inGameArt = click.prompt("In-game art URL", value_proc=str, default='/#')
        else:
            sale.infoPage = click.prompt("Info page URL", value_proc=str, default='/#')

    return saleLink, dateRange, saleArray


def extrapolate_link(lastSaleEnd, region='na'):
    """Used to extrapolate sale link from end sale date"""
    baseLink = 'http://{0}.leagueoflegends.com/en/news/store/sales/champion-and-skin-sale-{1}-{2}'
    lastSaleStart = lastSaleEnd - datetime.timedelta(3)
    return baseLink.format(
        region,
        datetime.datetime.strftime(lastSaleStart, '%m%d'),
        datetime.datetime.strftime(lastSaleEnd, '%m%d')
    )


def repair_lastrun():
    """Called from the CLI to ensure correct rotation data in lastrun.py"""
    rotation = [tuple(str(num) for num in x) for x in
        [(975, 750, 520), (1350, 975, 520), (975, 750, 520), (975, 975, 520)]
    ]

    def get_rotation(link):
        _, _, saleArray = get_content(link)
        return tuple(sale.regularPrice for sale in saleArray if sale.isSkin)

    lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, '%Y-%m-%d')
    lastRotation = get_rotation(extrapolate_link(lastSaleEnd))

    if lastRotation == (975, 750, 520):
        # Work two sales back to extrapolate rotation
        twoSaleEnd = lastSaleEnd - datetime.timedelta(3)
        twoLink = extrapolate_link(twoSaleEnd)
        resp, _ = load_page(twoLink)
        if resp.status == 200:
            twoRotation = get_rotation(twoLink)
        else:
            twoSaleEnd = lastSaleEnd - datetime.timedelta(4)
            twoLink = extrapolate_link(twoSaleEnd)
            resp, _ = load_page(twoLink)
            if resp.status == 200:
                twoRotation = get_rotation(twoLink)
            else:
                sys.exit(sWarning("Could not determine rotation."))

        twoRotationIndex = rotation.index(twoRotation)
        lastRotationIndex = (twoRotationIndex + 1) % 4
    else:
        lastRotationIndex = rotation.index(lastRotation)

    update_lastrun(lastrun.lastSaleEnd, lastRotationIndex)
    sys.exit()


@click.command()
@click.argument('testLink', required=False)
@click.option('--delay', '-d', 'delay', default=0, help="Delay before running script.", metavar='<hours>')
@click.option('--last', '-l', 'last', is_flag=True, help="Crawls most recent sale data.")
@click.option('--manual', '-m', 'manual', is_flag=True, help="Manually create post.")
@click.option('--refresh', '-r', 'refresh', is_flag=True, help="Automatically refresh sale pages.")
@click.option('--verbose', '-v', 'verbose', is_flag=True, help="Output entire post body.")
@click.option('--repair', is_flag=True, help="Attemps to repair data in lastrun.py.")

def main(testLink, delay, last, manual, refresh, verbose, repair):
    """
    Python script that generates Reddit post summarizing the biweekly League
    of Legends champion and skin sales. Uses the httplib2 and PRAW libraries.
    """

    if repair:
        repair_lastrun()
    elif manual:
        saleLink, dateRange, saleArray = manual_post()
    else:
        if last:
            lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, '%Y-%m-%d')
            testLink = extrapolate_link(lastSaleEnd)

        saleLink, dateRange, saleArray = get_content(testLink, delay, refresh, verbose)

    skinSales = ', '.join(sale.saleName for sale in saleArray if sale.isSkin)
    postTitle = '[Champion & Skin Sale] {0} ({1})'.format(skinSales, dateRange)

    if not verbose:
        print sSpecial(postTitle)

    # Get spotlights and print to terminal
    for sale in saleArray:
        sale.spotlight = get_spotlight(sale, verbose)

    # Format post body and print appropriately depending on verbosity
    postBody = make_post(saleArray, saleLink)
    print postBody if verbose else sSuccess("Post formatted successfully.")

    # Post to Reddit and update lastrun.py with correct information
    if not testLink:
        if manual and not click.confirm("Post to Reddit?"):
            sys.exit(sWarning("Did not post."))
        else:
            post_to_reddit(postTitle, postBody, saleLink)
            update_lastrun()

    sys.exit()


if __name__ == "__main__":
    main()
