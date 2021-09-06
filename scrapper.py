


#from scrappers.gnius import GniusScrapper
from scrappers.bpi import BpiScrapper
import sys


def main(hostPort):
    print("*** SCRAPPER ***")
    bpi = BpiScrapper()
    #bpi.print_data(verbose=True)
    #print(bpi.generate_feed(verbose=False))
    bpi.start_server(hostPort)


if __name__ == "__main__":
    main(int(sys.argv[1]))
    