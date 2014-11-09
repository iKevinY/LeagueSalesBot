# -*- coding: utf-8 -*-

import os
import sys
import re
import time

from datetime import datetime, timedelta

import requests
import praw
import click

import lastrun
import settings
import skins

class Sale(object):
    def __init__(self):
        self.saleName = ''
        self.salePrice = ''
        self.regularPrice = ''
        self.spotlight = None

class Skin(Sale):
    def __init__(self):
        self.isSkin = True
        self.splashArt = None
        self.inGameArt = None

class Champ(Sale):
    def __init__(self):
        self.isSkin = False
        self.infoPage = None


def format_range(saleStart, saleEnd):
    """Returns properly formatted date range for sale start and end"""
    if saleStart.month == saleEnd.month:
        dateString = '{0}–{1}'
        start, end = '%B %-d', '%-d'
    else:
        dateString = '{0} – {1}'
        start, end = '%B %-d', '%B %-d'

    return dateString.format(saleStart.strftime(start), saleEnd.strftime(end))


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

    return ', '.join('[{0}]({1})'.format(text, link)
        for link, text in resources if link is not None)


def get_date_range(link):
    """Determines date range string for a given sale link"""
    if requests.get(link).status_code != 200:
        sys.exit("Terminating script. ({0} not found)".format(link))

    try:
        start, end = re.findall('.*(\d{4})-(\d{4})', link)[0]
    except IndexError:
        sys.exit("Invalid sale page URL.")

    for dateFormat in ('%m%d', '%d%m'):
        try:
            saleStart = datetime.strptime(start, dateFormat)
            saleEnd = datetime.strptime(end, dateFormat)
            dateRange = format_range(saleStart, saleEnd)
            return link, dateRange
        except ValueError:
            pass # try other date formats
    else:
        sys.exit("Date range could not be determined from sale URL.")


def get_sale_page(link):
    """Loads appropriate content based on most recent sale or given link"""
    try:
        # Use value of lastRotation to differentiate between Monday and
        # Thursday sales (which have different date offsets)
        lastSaleEnd = datetime.strptime(lastrun.lastSaleEnd, '%Y-%m-%d')
        saleStart = lastSaleEnd + timedelta((lastrun.lastRotation + 1) % 2)
        saleEnd = saleStart + timedelta(3) # Four-day sales
    except AttributeError:
        print "Invalid data in lastrun.py. Attemping to repair."
        repair_lastrun()

    dateRange = format_range(saleStart, saleEnd)

    regions = ('na', 'euw')
    dateFormats = ('%m%d', '%d%m')
    permutations = ((region, saleStart.strftime(form), saleEnd.strftime(form))
        for region in regions for form in dateFormats)

    links = [settings.baseLink.format(*permutation) for permutation in permutations]

    searchString = "Last sale ended on {0}. Searching for {1} sale."
    print searchString.format(lastSaleEnd.strftime("%B %-d"), dateRange)

    refreshRate = settings.refresh
    print "Refreshing every {0} seconds (c-C to force quit)...".format(refreshRate)

    while True:
        for link in links:
            if requests.get(link).status_code == 200:
                return link, dateRange
        else:
            time.sleep(refreshRate)


def get_sales(saleLink):
    """Parses sale page for sale data"""

    # Riot Please...
    skinsFirst = False

    if skinsFirst:
        saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]
    else:
        saleArray = [Champ(), Champ(), Champ(), Skin(), Skin(), Skin()]

    # Define regexes for sales, skin art, and champion info pages
    regexes = (
        '<h4>(?:<a .+?>)*\s*?(.+?)\s*?(?:<\/a>)*<\/h4>\s+?<strike.*?>(\d+?)<\/strike> (\d+?) RP',
        '<a class="lightbox.*?" href="(\S+?)">\n<img .*></a>',
        '<a href="(http://gameinfo.(?:na|euw).leagueoflegends.com/en/game-info/champions/\S+?)"',
    )

    pageContent = requests.get(saleLink).text
    saleList, skinList, infoList = (re.findall(regex, pageContent) for regex in regexes)

    for i, sale in enumerate(saleArray):
        try:
            sale.saleName, sale.regularPrice, sale.salePrice = saleList[i]
        except IndexError:
            print "Sale data could not be parsed by regexes."
            return None

        if skinsFirst:
            if sale.isSkin:
                try:
                    sale.splashArt = skinList[i*2]
                    sale.inGameArt = skinList[i*2 + 1]
                except IndexError:
                    print "Art for %s not parsed." % sale.saleName
                    sale.splashArt, sale.inGameArt = None, None
            else:
                try:
                    sale.infoPage = infoList[(i - 3) * 2]
                except IndexError:
                    print "Info page for %s not parsed." % sale.saleName
                    sale.infoPage = None

        else:
            if not sale.isSkin:
                try:
                    sale.infoPage = infoList[i*2]
                except IndexError:
                    print "Info page for %s not parsed." % sale.saleName
                    sale.infoPage = None

            else:
                try:
                    sale.splashArt = skinList[(3 - i) * 2]
                    sale.inGameArt = skinList[(3 - i) * 2 + 1]
                except IndexError:
                    print "Art for %s not parsed." % sale.saleName
                    sale.splashArt, sale.inGameArt = None, None


    # Safeguard against Riot accidentally putting the prices in the wrong spot
    # by checking the price of the last skin sale (which should be 520 -> 260)
    if saleArray[2].regularPrice == '260' and saleArray[2].salePrice == '130':
        for sale in saleArray:
            # Scraped "regular price" is *actually* the sale price,
            # so determine the real sale price from that value
            sale.salePrice = sale.regularPrice
            sale.regularPrice = int(sale.salePrice) * 2

            if sale.regularPrice % 5 != 0:
                sale.regularPrice = str(sale.regularPrice + 1)
            else:
                sale.regularPrice = str(sale.regularPrice)

    # Sorts sale array by skins > champions and then by price (in reverse)
    return sorted(saleArray, key=lambda sale: (sale.isSkin, sale.salePrice), reverse=True)


def sale_output(sale):
    """Generates row of sale table for sale item"""
    if sale.isSkin:
        # Champions with two-part names
        for regex, champion in skins.twoParts.iteritems():
            if re.match(regex, sale.saleName):
                sale.champName = champion
                break
        else:
            # Try all exception skins
            if sale.saleName in skins.exceptSkins:
                sale.champName = skins.exceptSkins[sale.saleName]
            else:
                sale.champName = sale.saleName.split()[-1]
    else:
        sale.champName = sale.saleName

    sale.icon = '[](/{0})'.format(re.sub('\ |\.|\'', '', sale.champName.lower()))
    sale.wikiLink = 'http://leagueoflegends.wikia.com/wiki/' + sale.champName.replace(' ', '_')
    sale.resources = format_resources(sale)

    row = '|{icon}|**[{saleName}]({wikiLink})**|{salePrice} RP|~~{regularPrice} RP~~|{resources}|'

    return (row.format(**sale.__dict__))


def make_post(saleArray, saleLink):
    """Formats sale data into Reddit post"""
    # Determine prices of next sale skins given the previous sale
    rotation = [(975, 750, 520), (1350, 975, 520),
                (975, 750, 520), (975, 975, 520)]

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


def get_spotlight(sale):
    """Finds appropriate champion or skin spotlight video for sale"""
    channel = 'SkinSpotlights' if sale.isSkin else 'RiotGamesInc'
    searchTerm = '{0} {1} Spotlight'.format(
        sale.saleName, 'Skin' if sale.isSkin else 'Champion').replace(' ', '+')

    videoBase = 'https://www.youtube.com/user/{0}/search?query={1}'
    videoPage = videoBase.format(channel, searchTerm)
    pageContent = requests.get(videoPage).text

    try:
        searchResult = '<h3 class="yt-lockup-title"><a.*?href="(\S*)">(.*)<\/a>'
        slug, spotlightName = re.findall(searchResult, pageContent)[0]
        spotlightName = spotlightName.replace('&#39;', "'") # patch for apostrophe
        spotlightLink = 'https://www.youtube.com' + slug
    except IndexError:
        spotlightLink = None
        spotlightName = "Error parsing spotlight."

    # Handle cases where no spotlight exists, ie. Janna (Forecast Janna is top result)
    if not sale.isSkin:
        if ("Spotlight" not in spotlightName) or (sale.saleName not in spotlightName):
            spotlightLink = None
            spotlightName = click.style(spotlightName, fg='red')

    return spotlightLink, spotlightName


def post_to_reddit(subreddit, postTitle, content):
    """Posts self or link posts to subreddits as defined in settings.py"""
    isLink = content.startswith('http')
    postContent = {'url' if isLink else 'text': content}

    r = praw.Reddit(user_agent=settings.userAgent)
    r.login(settings.username, settings.password)

    while True:
        try:
            submission = r.submit(subreddit, postTitle, **postContent)
        except praw.errors.RateLimitExceeded as error:
            sleepTime = int(error.sleep_time + 1)
            print 'Sleeping for {0} seconds (rate limited).'.format(sleepTime)
            time.sleep(sleepTime)
        else:
            postType = 'link' if isLink else 'self'
            click.secho("Submitted {0} post.".format(postType), fg='green')
            click.echo(submission.permalink.rsplit('/', 2)[0] + '/')

            return submission


def update_lastrun(saleEnd, rotationIndex=None):
    """Updates lastrun.py with sale date and rotation information"""
    try:
        lastSaleEnd, lastRotation = lastrun.lastSaleEnd, lastrun.lastRotation
    except AttributeError:
        lastSaleEnd, lastRotation, rotationIndex = None, None, None
    else:
        if rotationIndex is None:
            rotationIndex = (lastRotation + 1 % 4)

    directory = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(directory, 'lastrun.py')

    with open(path, 'w+') as f:
        f.write('lastSaleEnd = "{0}"\nlastRotation = {1}\n'.format(saleEnd, rotationIndex))

    modifyString = "Modified lastrun.py from ({0}, {1}) to ({2}, {3})."
    print modifyString.format(lastSaleEnd, lastRotation, saleEnd, rotationIndex)


def extrapolate_link(lastSaleEnd, region='na'):
    """Used to extrapolate sale link from end sale date"""
    lastSaleStart = lastSaleEnd - timedelta(3)
    start = datetime.strftime(lastSaleStart, '%m%d')
    end = datetime.strftime(lastSaleEnd, '%m%d')

    return settings.baseLink.format(region, start, end)


def repair_lastrun():
    """Called from the CLI to ensure correct data in lastrun.py"""
    # Run through five possible sale pages starting from datetime.now()
    print "Determining most recent sale page."
    for delta in range(-4, 1):
        endDate = datetime.now() - timedelta(delta)
        link = extrapolate_link(endDate)

        if requests.get(link).status_code == 200:
            lastSaleEnd, lastSaleLink = endDate, link
            break
    else:
        sys.exit("Could not repair sale date data.")

    def get_rotation(link):
        return tuple(sale.regularPrice for sale in get_sales(link) if sale.isSkin)

    cycle = [(975, 750, 520), (1350, 975, 520), (975, 750, 520), (975, 975, 520)]
    rotation = [tuple(str(num) for num in x) for x in cycle]

    lastRotation = get_rotation(lastSaleLink)

    if lastRotation == ('975', '750', '520'):
        print "Extrapolating two sales back for correct rotation (ambiguous case)."
        for delta in (3, 4):
            twoSaleEnd = lastSaleEnd - timedelta(delta)
            twoLink = extrapolate_link(twoSaleEnd)
            if requests.get(twoLink).status_code == 200:
                twoRotation = get_rotation(twoLink)
                break
        else:
            sys.exit("Could not determine rotation.")

        lastRotationIndex = (rotation.index(twoRotation) + 1) % 4
    else:
        lastRotationIndex = rotation.index(lastRotation)

    lastSaleEndText = datetime.strftime(lastSaleEnd, '%Y-%m-%d')
    update_lastrun(lastSaleEndText, rotationIndex=lastRotationIndex)

    click.secho('lastrun.py repaired successfully.', fg='green')
    sys.exit()


@click.command()
@click.option('--last', '-l', is_flag=True, help="Crawls most recent sale data.")
@click.option('--link', default=None, help="Link to sale page.")
@click.option('--output', '-o', default=None, help="Post output path.", type=click.File('a'))
@click.option('--repair', is_flag=True, help="Repair data in lastrun.py.")
@click.argument('subreddits', nargs=-1)
def main(last, link, output, repair, subreddits):
    """
    Python script that generates Reddit-formatted summaries of the biweekly
    League of Legends champion and skin sales.
    """

    if repair:
        repair_lastrun()
    elif last:
        lastSaleEnd = datetime.strptime(lastrun.lastSaleEnd, '%Y-%m-%d')
        link = extrapolate_link(lastSaleEnd)

    linkFunction = get_date_range if link else get_sale_page
    saleLink, dateRange = linkFunction(link)

    saleArray = get_sales(saleLink)

    # Post link post if sale parsing failed
    if saleArray is None:
        if subreddits:
            postTitle = 'Champion & Skin Sale — {0}'.format(dateRange)
            post_to_reddit(subreddits[0], postTitle, saleLink)

        sys.exit()

    skinSales = ', '.join(sale.saleName for sale in saleArray if sale.isSkin)
    postTitle = settings.baseTitle.format(skinSales, dateRange)

    click.secho(postTitle, fg='cyan', bold=True)

    # Get spotlights and print to terminal
    for sale in saleArray:
        sale.spotlight, sale.spotlightName = get_spotlight(sale)
        tableArgs = sale.saleName, sale.salePrice, sale.spotlightName
        print '{0: <30}{1} RP\t{2}'.format(*tableArgs)

    postBody = make_post(saleArray, saleLink)

    # Write post body to output file if given
    if output:
        output.write(postBody + '\n')

    # Post to Reddit and update lastrun.py if link was not given
    if not link:
        if not subreddits:
            sys.exit("There were no subreddit arguments given.")

        for subreddit in subreddits:
            post_to_reddit(subreddit, postTitle, postBody)

        endOfSale = (datetime.now() + timedelta(4)).strftime('%Y-%m-%d')
        update_lastrun(endOfSale)


if __name__ == "__main__":
    main()
