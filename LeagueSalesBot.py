#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import re
import datetime
import time

import httplib2
import praw
import click

import lastrun
import settings
import skins

class Sale(object):
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
def sSpecial(s): return click.style(str(s), fg='cyan', bold=True)
def sSuccess(s): return click.style(str(s), fg='green')
def sWarning(s): return click.style(str(s), fg='red')


def load_page(link, verbose=False, responseStatus=False):
    try:
        if responseStatus:
            if not verbose:
                print link + "...\t",
                sys.stdout.flush()
            response = httplib2.Http().request(link, "HEAD")[0]
            if not verbose:
                if (response.status == 200):
                    print sSuccess(response.status)
                else:
                    print sWarning(response.status)

            return response.status
        else:
            return httplib2.Http().request(link)
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


def get_sale_page(testlink=None, delay=None, refresh=None, verbose=False):
    """Loads appropriate content based on most recent sale or supplied test link"""
    if testlink:
        if load_page(testlink, verbose, responseStatus=True) != 200:
            sys.exit(sWarning("Terminating script."))
        else:
            try:
                start, end = re.findall('.*(\d{4})-(\d{4})', testlink)[0]
            except IndexError:
                sys.exit(sWarning("Invalid sale page URL."))

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
                sys.exit(sWarning("Date range could not be determined from sale URL."))

            saleLink = testlink
    else:
        try:
            # Uses lastRotation value to differentiate between Mon/Thurs date deltas
            lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, '%Y-%m-%d')
            saleStart = lastSaleEnd + datetime.timedelta((lastrun.lastRotation + 1) % 2)
            saleEnd = saleStart + datetime.timedelta(3) # Four-day sales
        except AttributeError:
            print sWarning("Invalid data in lastrun.py. Attemping to repair.")
            repair_lastrun()

        dateRange = format_range(saleStart, saleEnd)

        regions = ('na', 'euw')
        dateFormats = ('%m%d', '%d%m')
        linkPermutations = ((region, saleStart.strftime(format), saleEnd.strftime(format))
            for region in regions for format in dateFormats)

        links = [settings.baseLink.format(*permutation) for permutation in linkPermutations]

        print "Last sale ended on {0}. Requesting {1} sale pages.".format(
            sSpecial(lastSaleEnd.strftime("%B %-d")), sSpecial(dateRange))

        if delay:
            delay = int(delay) if delay.is_integer() else delay
            print "Sleeping for {0} hour{1}.".format(delay, "s" * (delay != 1))
            time.sleep(delay * 60 * 60)

        saleLink = None

        while not saleLink:
            for link in links:
                if load_page(link, verbose, responseStatus=True) == 200:
                    saleLink = link
                    break
            else:
                if refresh:
                    refreshDelay = 20
                    print "Reloading in {0} seconds (c-C to force quit)...".format(refreshDelay)
                    time.sleep(refreshDelay)
                else:
                    sys.exit(sWarning("Terminating script."))

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

    pageContent = load_page(saleLink)[1]
    saleList, skinList, infoList = (re.findall(regex, pageContent) for regex in regexes)

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
    saleSearch = sale.saleName.replace(' ', '+')

    if sale.isSkin:
        channel, searchTerm = ('SkinSpotlights', saleSearch + '+Skin+Spotlight')
    else:
        channel, searchTerm = ('RiotGamesInc', saleSearch + '+Champion+Spotlight')

    videoPage = 'https://www.youtube.com/user/{0}/search?query={1}'.format(channel, searchTerm)
    pageContent = load_page(videoPage)[1]

    try:
        searchResult = '<h3 class="yt-lockup-title"><a.*?href="(\S*)">(.*)</a></h3>'
        slug, spotlightName = re.findall(searchResult, pageContent)[0]
        spotlightName = spotlightName.replace('&#39;', "'")
        spotlightURL = 'https://www.youtube.com' + slug
    except IndexError:
        spotlightURL = None
        spotlightName = "No spotlight found (parsing error)."

    # Handle cases where no spotlight exists, ie. Janna (Forecast Janna is top result)
    if not sale.isSkin:
        if ("Spotlight" not in spotlightName) or (sale.saleName not in spotlightName):
            spotlightURL = None
            spotlightName = sWarning(spotlightName)

    return spotlightURL, spotlightName


def post_to_reddit(postTitle, postBody, saleLink):
    """Posts self or link posts to subreddits as defined in settings.py"""
    # Handle Reddit's automatic rate limiting
    def handle_rate_limit(func, *args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except praw.errors.RateLimitExceeded as error:
                print 'Rate limit exceeded. Sleeping for {0} seconds'.format(error.sleep_time)
                time.sleep(error.sleep_time)

    r = praw.Reddit(user_agent=settings.userAgent)
    r.login(settings.username, settings.password)

    for subreddit, isLinkPost in settings.subreddits:
        if isLinkPost:
            submission = handle_rate_limit(r.submit, subreddit, postTitle, url=saleLink)
        else:
            submission = handle_rate_limit(r.submit, subreddit, postTitle, text=postBody)

        print sSuccess("Submitted {0} post at {1}/".format(
            "link" if isLinkPost else "self",
            submission.permalink.rsplit('/', 2)[0])
        )

        if isLinkPost:
            handle_rate_limit(submission.add_comment, postBody)
            print sSuccess("Commented on link post at /r/{0}.".format(subreddit))


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

    print sSuccess("Modified lastrun.py from ({0}, {1}) to".format(lastSaleEnd, lastRotation)),
    sys.stdout.flush()

    with open(path, 'w+') as f:
        f.write('lastSaleEnd = "{0}"\nlastRotation = {1}\n'.format(saleEndText, rotationIndex))

    print sSuccess("({0}, {1}).".format(saleEndText, rotationIndex))


def manual_post():
    """Manually enter sale data from the CLI"""
    saleArray = [Skin(), Skin(), Skin(), Champ(), Champ(), Champ()]

    inputDate = click.prompt("Enter sale start date [YYMMDD]", type=str)
    saleStart = datetime.datetime.strptime(inputDate, '%y%m%d')
    saleEnd = saleStart + datetime.timedelta(3)

    dateRange = format_range(saleStart, saleEnd)

    dateFormat = tuple(datetime.datetime.strftime(date, '%m%d') for date in (saleStart, saleEnd))
    saleLink = (settings.baseLink.format('na', dateFormat[0], dateFormat[1]))

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

        if load_page(link, responseStatus=True) == 200:
            lastSaleEnd, lastSaleLink = endDate, link
            break
    else:
        sys.exit(sWarning("Could not repair sale date data."))

    def get_rotation(link):
        return tuple(sale.regularPrice for sale in get_sales(link) if sale.isSkin)

    cycle = [(975, 750, 520), (1350, 975, 520), (975, 750, 520), (975, 975, 520)]
    rotation = [tuple(str(num) for num in x) for x in cycle]

    lastRotation = get_rotation(lastSaleLink)

    if lastRotation == ('975', '750', '520'):
        print "Extrapolating two sales back for rotation."
        for delta in (3, 4):
            twoSaleEnd = lastSaleEnd - datetime.timedelta(delta)
            twoLink = extrapolate_link(twoSaleEnd)
            if load_page(twoLink, responseStatus=True) == 200:
                twoRotation = get_rotation(twoLink)
                break
        else:
            sys.exit(sWarning("Could not determine rotation."))

        lastRotationIndex = (rotation.index(twoRotation) + 1) % 4
    else:
        lastRotationIndex = rotation.index(lastRotation)

    lastSaleEndText = datetime.datetime.strftime(lastSaleEnd, '%Y-%m-%d')
    update_lastrun(lastSaleEndText, rotationIndex=lastRotationIndex)

    sys.exit(sSuccess("lastrun.py repaired successfully. Upcoming sale: {0}, {1}, {2} RP").format(
        *rotation[(lastRotationIndex + 1) % 4]))


@click.command(add_help_option=False)
@click.argument('testlink', required=False)
@click.help_option('-h', '--help')
@click.option('--delay', '-d', default=0.0, help="Delay before running script.", metavar='<hours>')
@click.option('--last', '-l', is_flag=True, help="Crawls most recent sale data.")
@click.option('--manual', '-m', is_flag=True, help="Manually create post.")
@click.option('--refresh', '-r', is_flag=True, help="Automatically refresh sale pages.")
@click.option('--verbose', '-v', is_flag=True, help="Output entire post body.")
@click.option('--repair', is_flag=True, help="Attemps to repair data in lastrun.py.")

def main(testlink, delay, last, manual, refresh, verbose, repair):
    """
    Python script that generates Reddit post summarizing the biweekly League
    of Legends champion and skin sales. Uses the httplib2 and PRAW libraries.
    """

    if repair:
        repair_lastrun()
    elif manual:
        saleLink, dateRange = manual_post()
    else:
        if last:
            lastSaleEnd = datetime.datetime.strptime(lastrun.lastSaleEnd, '%Y-%m-%d')
            testlink = extrapolate_link(lastSaleEnd)

        saleLink, dateRange = get_sale_page(testlink, delay, refresh, verbose)

    saleArray = get_sales(saleLink)

    postTitle = '[Champion & Skin Sale] {0} ({1})'.format(
        ', '.join(sale.saleName for sale in saleArray if sale.isSkin), dateRange
    )

    if not verbose:
        print sSpecial(postTitle)

    # Get spotlights and print to terminal
    for sale in saleArray:
        sale.spotlight, sale.spotlightName = get_spotlight(sale)
        if not verbose:
            print '{saleName: <30}{salePrice} RP\t{spotlightName}'.format(**sale.__dict__)

    # Format post body and print appropriately depending on verbosity
    postBody = make_post(saleArray, saleLink)
    print postBody if verbose else sSuccess("Post formatted successfully.")

    # Post to Reddit and update lastrun.py with correct information
    if not testlink:
        if manual and not click.confirm("Post to Reddit?"):
            sys.exit(sWarning("Did not post."))
        else:
            post_to_reddit(postTitle, postBody, saleLink)
            endOfSale = (datetime.datetime.now() + datetime.timedelta(4)).strftime('%Y-%m-%d')
            update_lastrun(endOfSale)

    sys.exit()


if __name__ == "__main__":
    main()
