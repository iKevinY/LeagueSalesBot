import __init__
import sys

if __name__ == "__main__":
    try:
        sys.argv[1]
    except IndexError:
        __init__.main(False)
    else:
        __init__.main(True)
