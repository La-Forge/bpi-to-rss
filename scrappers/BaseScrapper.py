from html import unescape
import requests
import pprint
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import dateparser
from sentry_sdk import capture_exception
import sentry_sdk

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
        posts = []
        page = 0
        count_for_current_page = -1
        while count_for_current_page != 0:
            posts_on_current_page = self.scrapPage(pageNumber=page, verbose=verbose)
            posts.extend(posts_on_current_page)
            count_for_current_page = len(posts_on_current_page)
            page = page + 1
        return posts

    def scrapPage(self, pageNumber, verbose=False):
        raise NotImplementedError("This method should be overridden by subclasses")

    def print_data(self, verbose=False):
        posts = self.scrapPages()
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(posts)
        print(f"{len(posts)} extracted")

    def write_feed_to_file(self, feed, filename):
        with open(filename, 'wb') as file:
            file.write(feed)

    def get_full_article_content(self, article_url, content_class):
        response = requests.get(article_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            article_content = soup.find(class_=content_class).get_text()
            return article_content
        else:
            print(f"Failed to fetch article content from URL: {article_url}")
            return ""

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
                full_content = self.get_full_article_content(article["link"], article.get('content_class'))
                if full_content:
                    fe.content(full_content, type="CDATA")
        except Exception as e:
            print(e)
            capture_exception(e)

        atomfeed = fg.atom_str(pretty=True)
        return atomfeed

    def update_feed_file(self, filename='feed.xml', verbose=False):
        feed = self.generate_feed(verbose=verbose)
        self.write_feed_to_file(feed, filename)
