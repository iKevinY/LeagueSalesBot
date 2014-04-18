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
