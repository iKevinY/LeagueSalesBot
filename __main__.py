import LeagueSalesBot
import sys

if __name__ == "__main__":
    try:
        sys.argv[1]
    except IndexError:
        LeagueSalesBot.main()
    else:
        if sys.argv[1] == "-m":
            LeagueSalesBot.manualPost()
        elif sys.argv[1] == "-b":
            try:
                sys.argv[2]
            except IndexError:
                LeagueSalesBot.openBanner()
            else:
                LeagueSalesBot.openBanner(sys.argv[2])
        else:
            LeagueSalesBot.main(sys.argv[1])
