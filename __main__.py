import LeagueSalesBot
import sys

if __name__ == "__main__":
    try:
        sys.argv[1]
    except IndexError:
        LeagueSalesBot.main(False)
    else:
        LeagueSalesBot.main(True)
