import re
import lastrun

wikiLink = "http://leagueoflegends.wikia.com/wiki/"

tableHeader  = "| Icon | Skin/Champion  | Sale Price | Regular Price | Images |"
tableDivider = "|:----:|:--------------:|:----------:|:-------------:|:------:|"

rotation = [[975, 750, 520], [1350, 975, 520], [975, 750, 520], [975, 975, 520]]

r = lastrun.rotation

# Automate rotation of sale rotation
nextRotation = "Next skin sale: **{0} RP, {1} RP, {2} RP**.".format(rotation[r%4][0], rotation[r%4][1], rotation[r%4][2])

messageFooter = "^This ^bot ^was ^written ^by ^/u/Pewqazz. ^Feedback ^and ^suggestions ^are ^welcomed ^in ^/r/LeagueSalesBot."

def saleOutput(sale):
    champName = ""
    champLink = ""

    if sale.isSkin == True:
        # Try all exception skins (reference: http://leagueoflegends.wikia.com/wiki/Champion_skin)
        if sale.name == "Emumu":
            champName = "Amumu"
        elif sale.name == "Annie In Wonderland":
            champName = "Annie"
        elif sale.name == "Definitely Not Blitzcrank":
            champName = "Blitzcrank"
        elif sale.name == "iBlitzcrank":
            champName = "Blitzcrank"
        elif re.compile(".*? Mundo").match(sale.name):
            champName = "Dr. Mundo"
        elif sale.name == "Mr. Mundoverse":
            champName = "Dr. Mundo"
        elif sale.name == "Gragas, Esq":
            champName = "Gragas"
        elif sale.name == "Snowmerdinger":
            champName = "Heimerdinger"
        elif re.compile(".*? Jarvan IV").match(sale.name):
            champName = "Jarvan IV"
        elif sale.name == "Jaximus":
            champName = "Jax"
        elif sale.name == "Kennen M.D.":
            champName = "Kennen"
        elif re.compile(".*? Lee Sin").match(sale.name):
            champName = "Lee Sin"
        elif re.compile(".*? Master Yi").match(sale.name):
            champName = "Master Yi"
        elif sale.name == "Samurai Yi":
            champName = "Master Yi"
        elif re.compile(".*? Miss Fortune").match(sale.name):
            champName = "Miss Fortune"
        elif sale.name == "AstroNautilus":
            champName = "Nautilus"
        elif sale.name == "Nunu Bot":
            champName = "Nunu"
        elif sale.name == "Brolaf":
            champName = "Olaf"
        elif sale.name == "Lollipoppy":
            champName = "Poppy"
        elif sale.name == "Rumble in the Jungle":
            champName = "Rumble"
        elif sale.name == "Nutcracko":
            champName = "Shaco"
        elif re.compile(".*? Twisted Fate").match(sale.name):
            champName = "Twisted Fate"
        elif sale.name == "Jack of Hearts":
            champName = "Twisted Fate"
        elif sale.name == "Giant Enemy Crabgot":
            champName = "Urgot"
        elif sale.name == "Urf the Manatee":
            champName = "Warwick"
        elif re.compile(".*? Xin Zhao").match(sale.name):
            champName = "Xin Zhao"
        else:
            champName = sale.name.rsplit(' ', 1)[1]
        
        imageString = "[Splash](" + sale.splash + "), [In-Game](" + sale.inGame + ")"
    else: # It's a champion
        champName = sale.name
        imageString = "[Splash](" + sale.splash + ")"

    champLink = wikiLink + champName.replace(" ", "_")
    icon = "[](/" + champName.lower().replace(" ", "").replace(".", "").replace("'", "") + ")"

    regularPrice = 0
    # Calculate regular price of item
    if sale.cost == 487:
        regularPrice = 975
    elif sale.cost == 292:
        regularPrice = 585
    else:
        regularPrice = str(int(sale.cost) * 2)

    return "|" + icon + "|**[" + sale.name + "](" + champLink + ")**|" + str(sale.cost) + " RP|" + str(regularPrice) + " RP|" + imageString + "|"

def postBody(saleArray, bannerLink, articleLink):
    sourcePost = "Link to [source post]({0})".format(articleLink)
    sales = ""
    for sale in saleArray:
        sales = sales + saleOutput(sale) + "\n"

    saleBanner = "[sale banner]({0}).".format(bannerLink)

    return tableHeader + "\n" + tableDivider + "\n" + sales + nextRotation + " " + sourcePost + " and " + saleBanner + "\n\n----\n" + messageFooter
