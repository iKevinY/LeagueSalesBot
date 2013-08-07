import getcontent
import format
import post

import os
import re

content = getcontent.content

class Sale:
    def processSale(self):
        # Strip HTML tags
        text = (re.sub('<.*?>', '', self.text))

        # Strip " ___ RP" from end of string
        self.name = text[:-7]

        cost = re.findall('\d+', text)
        self.cost = int(cost[0])

class Skin(Sale):
    isSkin = True
class Champ(Sale):
    isSkin = False

# Declare sale objects
skin1, skin2, skin3 = Skin(), Skin(), Skin()
champ1, champ2, champ3 = Champ(), Champ(), Champ()
saleArray = [ skin1, skin2, skin3, champ1, champ2, champ3 ]

saleRegex = re.compile("<ul><li>(.*?<strong>\d{3} RP</strong>)</li></ul>")
imageRegex = re.compile("<a href=\"(http://riot-web-static\.s3\.amazonaws\.com/images/news/\S*?\.jpg)\"")
bannerRegex = re.compile("<img .*? src=\"(http://beta\.na\.leagueoflegends\.com/\S*?articlebanner\S*?.jpg)?\S*?\"")

# Set sale text to .text attributes of saleArray elements
for i in range(len(saleArray)):
    saleArray[i].text = unicode(re.findall(saleRegex, content)[i], "utf-8")
    saleArray[i].processSale()

    # Skins have splash and in-game while champions only have splash art
    if saleArray[i].__class__ is Skin:
        saleArray[i].splash = re.findall(imageRegex, content)[(i*2)]
        saleArray[i].inGame = re.findall(imageRegex, content)[(i*2)+1]
    elif saleArray[i].__class__ is Champ:
        saleArray[i].splash = re.findall(imageRegex, content)[i+3]
    else:
        pass

bannerLink = re.findall(bannerRegex, content)[0]

def main():
    postBody = format.postBody(saleArray, bannerLink)
    post.post(getcontent.postTitle, postBody)

    # Make appropriate changes to lastrun.py if post succeeds
    directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(directory, 'lastrun.py')
    f = open(path, 'r+')
    f.write("articleLink = \"" + getcontent.articleLink + "\"\n" + "rotation = " + str(format.r + 1) + "\n")
    f.close()
