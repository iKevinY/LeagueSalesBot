# Local file imports
import getcontent
import format
import post

# Other modules
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
    pass
class Champ(Sale):
    pass

# Declare sale objects
skin1, skin2, skin3 = Skin(), Skin(), Skin()
champ1, champ2, champ3 = Champ(), Champ(), Champ()
saleArray = [ skin1, skin2, skin3, champ1, champ2, champ3 ]

saleRegex = re.compile("<ul><li>(.*?<strong>\d{3} RP</strong>)</li></ul>")
imageRegex = re.compile("<img src=\"(http://riot-web-static.s3.amazonaws.com/images/news/\S*.jpg)")

# Set sale text to .text attributes of saleArray elements
imageIndex = 0
for i in range(len(saleArray)):
    saleArray[i].text = unicode(re.findall(saleRegex, content)[i], "utf-8")
    saleArray[i].processSale()

    # Skins have two thumbnails while champions only have splash art
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
    postBody = format.postBody(saleArray)
    post.post(getcontent.postTitle, postBody)
