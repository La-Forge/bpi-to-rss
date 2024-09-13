"""
2024.04.02 - v0.1 - Initial version

"""
from serve_feeds import get_rss_bpifrance_feed_content
import xml.etree.ElementTree as ET

from scrappers.BpifranceScrapper import BpifranceScrapper, FEED_PATH as BPI_FEED_PATH


def test_get_articles_from_scrapping_Bpifrance():
    bpi_scrapper = BpifranceScrapper()
    xml_data = bpi_scrapper.update_feed_file(filename=BPI_FEED_PATH,verbose=False)
    root = ET.fromstring(xml_data)
    assert root is not None


def test_get_articles_from_feed():
    articles = get_rss_bpifrance_feed_content()
    assert articles is not None and len(articles) > 0



