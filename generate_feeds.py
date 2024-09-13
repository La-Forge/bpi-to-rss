from scrappers.GniusScrapper import GniusScrapper, FEED_PATH as GNIUS_FEED_PATH
from scrappers.BpifranceScrapper import BpifranceScrapper, FEED_PATH as BPI_FEED_PATH

import os
import argparse


def main(verbose, update_bpi, update_gnius):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    feeds_dir = os.path.join(script_dir, "feeds")
    os.makedirs(feeds_dir, exist_ok=True)

    bpi_scrapper = BpifranceScrapper()
    gnius_scrapper = GniusScrapper()

    bpi_feed_file = BPI_FEED_PATH  # os.path.join(feeds_dir, BPI_FEED_PATH)
    gnius_feed_file = GNIUS_FEED_PATH  # os.path.join(feeds_dir, 'gnius_feed.xml')

    if update_bpi:
        print(f"Updating {bpi_feed_file}...")
        bpi_scrapper.update_feed_file(bpi_feed_file, verbose=verbose)
        print(f"{bpi_feed_file} updated.")

    if update_gnius:
        print(f"Updating {gnius_feed_file}...")
        gnius_scrapper.update_feed_file(gnius_feed_file, verbose=verbose)
        print(f"{gnius_feed_file} updated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update feeds with optional verbosity."
    )
    parser.add_argument(
        "--bpifrance", action="store_true", help="Update only bpifrance feed"
    )
    parser.add_argument("--gnius", action="store_true", help="Update only gnius feed")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    args = parser.parse_args()

    # Si ni bpifrance ni gnius n'est spécifié, on met à jour les deux
    update_bpi = args.bpifrance or (not args.bpifrance and not args.gnius)
    update_gnius = args.gnius or (not args.bpifrance and not args.gnius)

    main(args.verbose, update_bpi, update_gnius)
