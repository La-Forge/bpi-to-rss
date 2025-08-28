from scrappers.GniusScrapper import GniusScrapper, FEED_PATH as GNIUS_FEED_PATH
from scrappers.BpifranceScrapper import BpifranceScrapper, FEED_PATH as BPI_FEED_PATH
from scrappers.IleDeFranceScrapper import IleDeFranceScrapper, FEED_PATH as IDF_FEED_PATH
from scrappers.ProjetAchatPublicScrapper import ProjetsAchatScrapper, FEED_PATH as PROJET_ACHAT_FEED_PATH

import os
import argparse


def main(verbose, update_bpi, update_gnius, update_idf, update_achat):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    feeds_dir = os.path.join(script_dir, "feeds")
    os.makedirs(feeds_dir, exist_ok=True)

    bpi_scrapper = BpifranceScrapper()
    gnius_scrapper = GniusScrapper()
    idf_scrapper = IleDeFranceScrapper()
    projetachat_scrapper = ProjetsAchatScrapper()

    bpi_feed_file = BPI_FEED_PATH  # os.path.join(feeds_dir, BPI_FEED_PATH)
    gnius_feed_file = GNIUS_FEED_PATH  # os.path.join(feeds_dir, 'gnius_feed.xml')
    idf_feed_file = IDF_FEED_PATH  # os.path.join(feeds_dir, 'idf_feed.xml')
    achat_feed_file = PROJET_ACHAT_FEED_PATH  # os.path.join(feeds_dir, 'achat_feed.xml')

    if update_bpi:
        print(f"Updating {bpi_feed_file}...")
        bpi_scrapper.update_feed_file(bpi_feed_file, verbose=verbose)
        print(f"{bpi_feed_file} updated.")

    if update_gnius:
        print(f"Updating {gnius_feed_file}...")
        gnius_scrapper.update_feed_file(gnius_feed_file, verbose=verbose)
        print(f"{gnius_feed_file} updated.")

    if update_idf:
        print(f"Updating {idf_feed_file}...")
        idf_scrapper.update_feed_file(idf_feed_file, verbose=verbose)
        print(f"{idf_feed_file} updated.")
        
    if update_achat:
        print(f"Updating {achat_feed_file}...")
        projetachat_scrapper.update_feed_file(achat_feed_file, verbose=verbose)
        print(f"{achat_feed_file} updated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update feeds with optional verbosity."
    )
    parser.add_argument(
        "--bpifrance", action="store_true", help="Update only Bpifrance feed"
    )
    parser.add_argument("--gnius", action="store_true", help="Update only Gnius feed")
    parser.add_argument("--idf", action="store_true", help="Update only IDF feed")
    parser.add_argument("--achat", action="store_true", help="Update only Projet Achat feed")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    args = parser.parse_args()

    # Si aucune option n'est spécifiée, on met à jour tous les feeds
    update_bpi = args.bpifrance or (not args.bpifrance and not args.gnius and not args.idf and not args.achat)
    update_gnius = args.gnius or (not args.bpifrance and not args.gnius and not args.idf and not args.achat)
    update_idf = args.idf or (not args.bpifrance and not args.gnius and not args.idf and not args.achat)
    update_achat = args.achat or (not args.bpifrance and not args.gnius and not args.idf and not args.achat)

    main(args.verbose, update_bpi, update_gnius, update_idf, update_achat)