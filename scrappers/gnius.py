from html import unescape
import requests
import pprint
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import sentry_sdk
from sentry_sdk import capture_exception
import dateparser
import feedparser
import os
import json
import xml.etree.ElementTree as ET

sentry_sdk.init(
    "https://050cb1f4aff04d22af23721245c4ae35@o1031661.ingest.sentry.io/5998395",
    traces_sample_rate=1.0,
)

class GniusScrapper:
    def __init__(self):
        self.GNIUS_URL = "https://gnius.esante.gouv.fr/fr/a-la-une/actualites?page=<page-number>"
        self.GNIUS_HOST = "https://gnius.esante.gouv.fr"

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
        page = requests.get(self.GNIUS_URL.replace("<page-number>", str(pageNumber)))
        soup = BeautifulSoup(page.content, "html.parser")
        articles = soup.find_all("article")
        scraps = []
        for article in articles:
            res = {}
            link = article.find("h3").find("a")
            res["title"] = unescape(article.find("h3").text.strip())
            res["description"] = unescape(article.select(".o-teaser__infos--top")[0].text.strip())
            res["link"] = self.GNIUS_HOST + link["href"]
            date = article.select(".o-teaser__infos .fw-medium .a-info__text")[0].text.strip()
            res["date"] = dateparser.parse(
                date,
                languages=["fr"],
                settings={"TIMEZONE": "Europe/Paris", "RETURN_AS_TIMEZONE_AWARE": True},
            )
            res["content"] = unescape(link.text.strip())
            scraps.append(res)
        if verbose:
            print(f"{len(scraps)} posts extracted on page {pageNumber}")
        return scraps

    def print_data(self, verbose=False):
        posts = self.scrapPages()
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(posts)
        print(f"{len(posts)} extracted")

    def write_feed_to_file(self, feed, filename):
        with open(filename, 'wb') as file:
            file.write(feed)

    def get_full_article_content(self, article_url):
        response = requests.get(article_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            article_content = soup.find(class_="node__content").get_text()
            return article_content
        else:
            print(f"Failed to fetch article content from URL: {article_url}")
            return ""

    def generate_feed(self, verbose=True):
        fg = FeedGenerator()
        fg.title("Gnius - Actualités")
        fg.id(self.GNIUS_URL)
        fg.author({"name": "Gnius"})
        fg.link(href=self.GNIUS_URL, rel="alternate")
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
                full_content = self.get_full_article_content(article["link"])
                if full_content:
                    fe.content(full_content, type="CDATA")
        except Exception as e:
            print(e)
            capture_exception(e)

        atomfeed = fg.atom_str(pretty=True)
        return atomfeed

    def update_feed_file(self, filename='gnius_feed.xml'):
        feed = self.generate_feed(verbose=False)
        self.write_feed_to_file(feed, filename)
