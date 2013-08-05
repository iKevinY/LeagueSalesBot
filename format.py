""" Define static strings """

wikiLink = "http://leagueoflegends.wikia.com/wiki/"

tableHeader  = "| Icon | Skin/Champion  | Sale Price | Regular Price | Images |"
tableDivider = "|:----:|:--------------:|:----------:|:-------------:|:------:|"

# Automate rotation of sale rotation
nextRotation = """
Next skin sale: **1350 RP, 975 RP, 520 RP**  
Two sales from now: **975 RP, 750 RP, 520 RP**  
Three sales from now: **975 RP, 975 RP, 520 RP**  
"""

horizontalRule = "----"

messageFooter = "^Feedback ^and ^suggestions ^about ^this ^automated ^post ^can ^be ^submitted ^to ^/r/LeagueSalesBot."

def saleOutput(sale):

    champName = ""
    champLink = ""
    # Differentiate between skin and champion sales
    try:
        sale.splash
    except AttributeError: # It's a skin
        champName = sale.name.rsplit(' ', 1)[1]
        champLink = wikiLink + champName.replace(" ", "_")
        imageString = "[1](" + sale.thumb1 + "), [2](" + sale.thumb2 + ")"
    else: # It's a champion
        champName = sale.name
        champLink = wikiLink + champName.replace(" ", "_")
        imageString = "[1](" + sale.splash + ")"

    if champName == "Dr. Mundo":
        icon = "[](/mundo)"
    else:
        icon = "[](/" + champName.lower().replace(" ", "") + ")"

    regularPrice = ""
    # Calculate regular price of item
    if sale.cost == "487": # Oddball case for 50% off
        regularPrice = "975"
    else:
        regularPrice = str(int(sale.cost) * 2)

    return "|" + icon + "|" + "**[" + sale.name + "](" + champLink + ")**" + "|" + sale.cost + " RP" + "|" + regularPrice + " RP" + "|" + imageString + "|"
