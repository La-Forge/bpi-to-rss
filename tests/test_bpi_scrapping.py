"""
2024.04.02 - v0.1 - Initial version

These are live tests that hit the real Bpifrance website and write to a file.
They are intentionally excluded from the default test run (marker: live).
"""

import xml.etree.ElementTree as ET

import pytest

from scrappers.BpifranceScrapper import FEED_PATH as BPI_FEED_PATH
from scrappers.BpifranceScrapper import BpifranceScrapper
from serve_feeds import get_rss_bpifrance_feed_content


@pytest.mark.live
def test_get_articles_from_scrapping_Bpifrance():
    bpi_scrapper = BpifranceScrapper()
    xml_data = bpi_scrapper.update_feed_file(filename=BPI_FEED_PATH, verbose=False)
    root = ET.fromstring(xml_data)
    assert root is not None


@pytest.mark.live
def test_get_articles_from_feed():
    articles = get_rss_bpifrance_feed_content()
    assert articles is not None and len(articles) > 0
