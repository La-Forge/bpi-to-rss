from scrappers.BaseScrapper import BaseScrapper
from html import unescape
import requests
from bs4 import BeautifulSoup
import dateparser
from feedgen.feed import FeedGenerator
from sentry_sdk import capture_exception

class WebScrapper(BaseScrapper):

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
            count_for_current_page = len(posts_on_current_page)
            posts.extend(posts_on_current_page)
            page += 1

        return posts
    
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
                full_content = self.get_full_article_content(
                    article["link"], article.get("content_class")
                )
                if full_content:
                    fe.content(full_content, type="CDATA")
        except Exception as e:
            print(e)
            capture_exception(e)

        atomfeed = fg.atom_str(pretty=True)
        return atomfeed