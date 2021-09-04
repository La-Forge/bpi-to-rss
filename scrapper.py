


from scrappers.gnius import GniusScrapper
from scrappers.bpi import BpiScrapper


def main():
    print("*** SCRAPPER ***")
    bpi = BpiScrapper();
    bpi.scrapPage(1)

if __name__ == "__main__":
    main()