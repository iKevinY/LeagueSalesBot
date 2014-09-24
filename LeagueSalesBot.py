#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import re
import datetime
import time

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

    return ', '.join('[{0}]({1})'.format(text, link)
        for link, text in resources if link is not None
    )


def get_sale_page(link, delay):
    """Loads appropriate content based on most recent sale or supplied test link"""
    if link:
        if requests.get(link).status_code != 200:
            sys.exit("Terminating script.")
        else:
            try:
                start, end = re.findall('.*(\d{4})-(\d{4})', link)[0]
            except IndexError:
                sys.exit("Invalid sale page URL.")

            for dateFormat in ('%m%d', '%d%m'):
                try:
                    saleStart = datetime.datetime.strptime(start, dateFormat)
                    saleEnd = datetime.datetime.strptime(end, dateFormat)
                    dateRange = format_range(saleStart, saleEnd)
                    break
                except ValueError:
                    # Pass to try other date formats; for loop will catch the exception
                    pass
            else:
                sys.exit("Date range could not be determined from sale URL.")

            saleLink = link
    else:
        try:
            # Use value of lastRotation to differentiate between Monday and Thursday
            # sales (which have different offsets before the next sale)
            lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, '%Y-%m-%d')
            saleStart = lastSaleEnd + datetime.timedelta((lastrun.lastRotation + 1) % 2)
            saleEnd = saleStart + datetime.timedelta(3) # Four-day sales
        except AttributeError:
            print "Invalid data in lastrun.py. Attemping to repair."
            repair_lastrun()

        dateRange = format_range(saleStart, saleEnd)

        regions = ('na', 'euw')
        dateFormats = ('%m%d', '%d%m')
        linkPermutations = ((region, saleStart.strftime(format), saleEnd.strftime(format))
            for region in regions for format in dateFormats)

        links = [settings.baseLink.format(*permutation) for permutation in linkPermutations]

        print "Last sale ended on {0}. Requesting {1} sale pages.".format(
            lastSaleEnd.strftime("%B %-d"), dateRange
        )

        if delay:
            delay = int(delay) if delay.is_integer() else delay
            print "Sleeping for {0} {1}.".format(delay, "hour" if delay == 1 else "hours")
            time.sleep(delay * 60 * 60)

        saleLink = None

        refreshDelay = settings.refresh
        print "Refreshing every {0} seconds (c-C to force quit)...".format(refreshDelay)

        while not saleLink:
            for link in links:
                if requests.get(link).status_code == 200:
                    saleLink = link
                    break
            else:
                time.sleep(refreshDelay)

    return saleLink, dateRange


def get_sales(saleLink):
    """Parses sale page for sale data"""
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

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

    return ('|{icon}|**[{saleName}]({wikiLink})**|'
            '{salePrice} RP|~~{regularPrice} RP~~|{resources}|'.format(**sale.__dict__))


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


def get_spotlight(sale):
    """Finds appropriate champion or skin spotlight video for sale"""
    channel = 'SkinSpotlights' if sale.isSkin else 'RiotGamesInc'
    searchTerm = '{0} {1} Spotlight'.format(
        sale.saleName, 'Skin' if sale.isSkin else 'Champion').replace(' ', '+')

    videoPage = 'https://www.youtube.com/user/{0}/search?query={1}'.format(channel, searchTerm)
    pageContent = requests.get(videoPage).text

    try:
        searchResult = '<h3 class="yt-lockup-title"><a.*?href="(\S*)">(.*)</a></h3>'
        slug, spotlightName = re.findall(searchResult, pageContent)[0]
        spotlightName = spotlightName.replace('&#39;', "'") # patch for apostrophe
        spotlightURL = 'https://www.youtube.com' + slug
    except IndexError:
        spotlightURL = None
        spotlightName = "Error parsing spotlight."

    # Handle cases where no spotlight exists, ie. Janna (Forecast Janna is top result)
    if not sale.isSkin:
        if ("Spotlight" not in spotlightName) or (sale.saleName not in spotlightName):
            spotlightURL = None
            spotlightName = click.style(spotlightName, fg='red')

    return spotlightURL, spotlightName


def post_to_reddit(subreddit, postTitle, content):
    """Posts self or link posts to subreddits as defined in settings.py"""
    # Handle Reddit's automatic rate limiting
    def rate_limited(func, *args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except praw.errors.RateLimitExceeded as error:
                sleepTime = int(error.sleep_time + 1)
                print 'Rate limit exceeded. Sleeping for {0} seconds.'.format(sleepTime)
                time.sleep(sleepTime)

    postContent = {'url' if content.startswith('http') else 'text': content}

    r = praw.Reddit(user_agent=settings.userAgent)
    r.login(settings.username, settings.password)
    submission = rate_limited(r.submit, subreddit, postTitle, **postContent)

    click.secho("Submitted {0} post at {1}/".format(
        "link" if content.startswith('http') else "self",
        submission.permalink.rsplit('/', 2)[0]),
        fg='green'
    )


def update_lastrun(saleEndText, rotationIndex=None):
    """Updates lastrun.py with sale date and rotation information"""
    try:
        lastSaleEnd, lastRotation = lastrun.lastSaleEnd, lastrun.lastRotation
    except AttributeError:
        lastSaleEnd, lastRotation = None, None

    if rotationIndex is None:
        try:
            rotationIndex = (lastRotation + 1) % 4
        except AttributeError:
            pass

    directory = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(directory, 'lastrun.py')

    print "Modified lastrun.py from ({0}, {1}) to".format(lastSaleEnd, lastRotation),
    sys.stdout.flush()

    with open(path, 'w+') as f:
        f.write('lastSaleEnd = "{0}"\nlastRotation = {1}\n'.format(saleEndText, rotationIndex))

    print "({0}, {1}).".format(saleEndText, rotationIndex)


def extrapolate_link(lastSaleEnd, region='na'):
    """Used to extrapolate sale link from end sale date"""
    lastSaleStart = lastSaleEnd - datetime.timedelta(3)
    return settings.baseLink.format(
        region,
        datetime.datetime.strftime(lastSaleStart, '%m%d'),
        datetime.datetime.strftime(lastSaleEnd, '%m%d')
    )


def repair_lastrun():
    """Called from the CLI to ensure correct data in lastrun.py"""
    # Run through five possible sale pages starting from datetime.now()
    print "Determining most recent sale page."
    for delta in range(-4, 1):
        endDate = datetime.datetime.now() - datetime.timedelta(delta)
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
            twoSaleEnd = lastSaleEnd - datetime.timedelta(delta)
            twoLink = extrapolate_link(twoSaleEnd)
            if requests.get(twoLink).status_code == 200:
                twoRotation = get_rotation(twoLink)
                break
        else:
            sys.exit("Could not determine rotation.")

        lastRotationIndex = (rotation.index(twoRotation) + 1) % 4
    else:
        lastRotationIndex = rotation.index(lastRotation)

    lastSaleEndText = datetime.datetime.strftime(lastSaleEnd, '%Y-%m-%d')
    update_lastrun(lastSaleEndText, rotationIndex=lastRotationIndex)

    sys.exit("lastrun.py repaired successfully. Upcoming sale: {0}, {1}, {2} RP").format(
        *rotation[(lastRotationIndex + 1) % 4])


@click.command()
@click.option('--delay', '-d', default=0.0, help="Delay before running script.", metavar='<hours>')
@click.option('--last', '-l', is_flag=True, help="Crawls most recent sale data.")
@click.option('--repair', is_flag=True, help="Attemps to repair data in lastrun.py.")
@click.option('--link', default=None, help="Link to sale page.", metavar='<link>')
@click.argument('subreddits', nargs=-1)

def main(delay, last, link, repair, subreddits):
    """
    Python script that generates Reddit-formatted summaries of the biweekly
    League of Legends champion and skin sales.
    """

    if repair:
        repair_lastrun()
    elif last:
        lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, '%Y-%m-%d')
        link = extrapolate_link(lastSaleEnd)

    saleLink, dateRange = get_sale_page(link, delay)
    saleArray = get_sales(saleLink)

    # Post link post if sale parsing failed (fallback to ensure a post gets made)
    if saleArray is None:
        if subreddits:
            postTitle = 'Champion & Skin Sale — {0}'.format(dateRange)
            post_to_reddit(subreddits[0], postTitle, saleLink)

        sys.exit()

    postTitle = settings.baseTitle.format(
        ', '.join(sale.saleName for sale in saleArray if sale.isSkin),
        dateRange
    )

    click.secho(postTitle, fg='cyan', bold=True)

    # Get spotlights and print to terminal
    for sale in saleArray:
        sale.spotlight, sale.spotlightName = get_spotlight(sale)
        print '{saleName: <30}{salePrice} RP\t{spotlightName}'.format(**sale.__dict__)

    postBody = make_post(saleArray, saleLink)
    print '\n\n' + postBody + '\n\n'

    # Post to Reddit and update lastrun.py with correct information if link was not supplied
    if not link:
        if not subreddits:
            sys.exit("There were no subreddit arguments given.")
        else:
            for subreddit in subreddits:
                post_to_reddit(subreddit, postTitle, postBody)

        endOfSale = (datetime.datetime.now() + datetime.timedelta(4)).strftime('%Y-%m-%d')
        update_lastrun(endOfSale)


if __name__ == "__main__":
    main()
