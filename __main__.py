import LeagueSalesBot
import sys

if __name__ == "__main__":
    try:
        sys.argv[1]
    except IndexError:
        LeagueSalesBot.main()
    else:
        LeagueSalesBot.main(sys.argv[1])
