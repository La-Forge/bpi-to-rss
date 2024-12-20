import requests
import pprint
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from sentry_sdk import capture_exception
import sentry_sdk
import os

sentry_sdk.init(
    "https://050cb1f4aff04d22af23721245c4ae35@o1031661.ingest.sentry.io/5998395",
    traces_sample_rate=1.0,
)


class BaseScrapper:
    def __init__(self, base_url, host, feed_title, feed_author, feed_link):
        self.base_url = base_url
        self.host = host
        self.feed_title = feed_title
        self.feed_author = feed_author
        self.feed_link = feed_link

    def scrapPages(self, verbose=False):
        raise NotImplementedError("This method should be overridden by subclasses")

    def print_data(self, verbose=False):
        posts = self.scrapPages()
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(posts)
        print(f"{len(posts)} extracted")

    def write_feed_to_file(self, feed, filename):
        # ensure path to filename exists
        path = os.path.dirname(filename)
        os.makedirs(path, exist_ok=True)

        with open(filename, "wb") as file:
            file.write(feed)

    def generate_feed(self, verbose=True):
        raise NotImplementedError("This method should be overridden by subclasses")

    def update_feed_file(self, filename="feed.xml", verbose=False):
        feed = self.generate_feed(verbose=verbose)
        self.write_feed_to_file(feed, filename)
        return feed