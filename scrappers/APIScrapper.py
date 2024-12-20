from scrappers.BaseScrapper import BaseScrapper
from html import unescape
import requests
from bs4 import BeautifulSoup
import dateparser
from feedgen.feed import FeedGenerator
from sentry_sdk import capture_exception

class APIScrapper(BaseScrapper):

    def __init__(self, base_url, host, feed_title, feed_author, feed_link):
        self.base_url = base_url
        self.host = host
        self.feed_title = feed_title
        self.feed_author = feed_author
        self.feed_link = feed_link

    def generate_feed(self, verbose=True):
        fg = FeedGenerator()
        fg.title(self.feed_title)
        fg.id(self.feed_link)
        fg.author({"name": self.feed_author})
        fg.link(href=self.feed_link, rel="alternate")
        fg.subtitle("Powered by www.la-forge.ai")
        fg.language("fr")

        try:
            articles = self.scrapPages(verbose=verbose)
            for article in articles:
                fe = fg.add_entry()
                fe.id(article["link"])
                fe.title(article["title"])
                fe.link(href=article["link"])
                fe.description(article["description"])
                fe.pubDate(article["date"])
        except Exception as e:
            print(e)
            capture_exception(e)

        atomfeed = fg.atom_str(pretty=True)
        return atomfeed