from scrappers.gnius import GniusScrapper
from scrappers.bpi import BpiScrapper
import os
import argparse

def main(verbose):
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    feeds_dir = os.path.join(script_dir, 'feeds')
    os.makedirs(feeds_dir, exist_ok=True)

    bpi_scrapper = BpiScrapper()
    gnius_scrapper = GniusScrapper()

    bpi_feed_file = os.path.join(feeds_dir, 'bpi_feed.xml')
    gnius_feed_file = os.path.join(feeds_dir, 'gnius_feed.xml')

    print(f"Updating {bpi_feed_file}...")
    bpi_scrapper.update_feed_file(bpi_feed_file,verbose=verbose)
    print(f"{bpi_feed_file} updated.")

    print(f"Updating {gnius_feed_file}...")
    gnius_scrapper.update_feed_file(gnius_feed_file,verbose=verbose)
    print(f"{gnius_feed_file} updated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update feeds with optional verbosity.")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    main(args.verbose)