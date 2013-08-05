# Local file imports
import getcontent
import format

# Other modules
import re

content = getcontent.content

class Sale:
    text = ""
    name = ""
    cost = ""

    def processSale(self):
        # Strip HTML tags
        text = (re.sub('<.*?>', '', self.text))

        # Strip " ___ RP" from end of string
        self.name = text[:-7]

        cost = re.findall('\d+', text)
        self.cost = cost[0]

class Skin(Sale):
    thumb1 = ""
    thumb2 = ""

class Champ(Sale):
    splash = ""

# Declare sale objects
skin1, skin2, skin3 = Skin(), Skin(), Skin()
champ1, champ2, champ3 = Champ(), Champ(), Champ()
saleArray = [ skin1, skin2, skin3, champ1, champ2, champ3 ]

titleRegex = re.compile("<title>(.*?)</title>")
saleRegex = re.compile("<ul><li>(.*?<strong>\d{3} RP</strong>)</li></ul>")
imageRegex = re.compile("<img src=\"(http://riot-web-static.s3.amazonaws.com/images/news/\S*.jpg)")

# Set sale text to .text attributes of saleArray elements
imageIndex = 0
for i in range(len(saleArray)):
    saleArray[i].text = unicode(re.findall(saleRegex, content)[i], "utf-8")
    saleArray[i].processSale()

    if saleArray[i].__class__ is Skin:
        saleArray[i].thumb1 = re.findall(imageRegex, content)[imageIndex]
        imageIndex += 1
        saleArray[i].thumb2 = re.findall(imageRegex, content)[imageIndex]
        imageIndex += 1
    elif saleArray[i].__class__ is Champ:
        saleArray[i].splash = re.findall(imageRegex, content)[imageIndex]
        imageIndex += 1
    else:
        pass
        # Something went wrong

def main():
    print format.tableHeader
    print format.tableDivider

    for sale in saleArray:
        print format.saleOutput(sale)

    print format.nextRotation
    print format.horizontalRule
    print format.messageFooter
