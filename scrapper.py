


from scrappers.gnius import GniusScrapper
from scrappers.bpi import BpiScrapper


def main():
    print("*** SCRAPPER ***")
    bpi = BpiScrapper()
    #bpi.print_data(verbose=True)
    print(bpi.generate_feed(verbose=False))


if __name__ == "__main__":
    main()