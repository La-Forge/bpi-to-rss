from scrappers.BaseScrapper import BaseScrapper
from html import unescape
import requests
from bs4 import BeautifulSoup
import dateparser
from feedgen.feed import FeedGenerator
from sentry_sdk import capture_exception
from urllib.parse import urljoin, urlparse
import re

class WebScrapper(BaseScrapper):

    def __init__(self, base_url, host, feed_title, feed_author, feed_link):
        self.base_url = base_url
        self.host = host
        self.feed_title = feed_title
        self.feed_author = feed_author
        self.feed_link = feed_link

    def _normalize_url(self, url: str) -> str:
        """Return a clean absolute URL built from base_url and a possibly malformed input.
        """
        if not url:
            return self.base_url
        s = url.strip()
        # If the string contains an embedded scheme, keep from the first one
        m = re.search(r"https?://", s)
        if m:
            s = s[m.start():]
        # If there's still no scheme, join with base_url
        if not urlparse(s).scheme:
            s = urljoin(self.base_url.rstrip('/') + '/', s.lstrip('/'))
        return s

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
        # Normalize the URL to avoid cases like 'www.bpifrance.frhttps'
        normalized_url = self._normalize_url(article_url)
        try:
            response = requests.get(normalized_url, timeout=15)
        except Exception as req_err:
            print(f"Failed to fetch article content (network error): {normalized_url} -> {req_err}")
            return ""

        if response.status_code == 200:
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.content, "html.parser")
            # Try by class if provided, else fallback to <article> or the whole body text
            node = None
            if content_class:
                node = soup.find(class_=content_class)
            if node is None:
                node = soup.find('article') or soup.find('main') or soup.body
            article_content = node.get_text(separator='\n', strip=True) if node else ""
            return article_content
        else:
            print(f"Failed to fetch article content (HTTP {response.status_code}): {normalized_url}")
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
                link = self._normalize_url(article["link"])
                fe.id(link)
                fe.title(article["title"])
                fe.link(href=link)
                fe.description(article["description"])
                fe.pubDate(article["date"])
                full_content = self.get_full_article_content(
                    link, article.get("content_class")
                )
                if full_content:
                    fe.content(full_content)
        except Exception as e:
            print(e)
            try:
                capture_exception(e)
            except Exception:
                # Avoid secondary crashes (e.g., TypeError: cannot pickle 'FrameLocalsProxy')
                pass

        atomfeed = fg.atom_str(pretty=True)
        return atomfeed
