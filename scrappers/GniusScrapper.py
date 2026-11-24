from html import unescape

import dateparser
import requests
from bs4 import BeautifulSoup

from scrappers.WebScrapper import WebScrapper

FEED_PATH = "feeds/gnius_feed.xml"


class GniusScrapper(WebScrapper):
    """
    Classe pour scrapper les données de GNius - actualités.
    """

    def __init__(self):
        super().__init__(
            base_url="https://gnius.esante.gouv.fr/fr/a-la-une/actualites?page=<page-number>",
            host="https://gnius.esante.gouv.fr",
            feed_title="Gnius - Actualités",
            feed_author="Gnius",
            feed_link="https://gnius.esante.gouv.fr/fr/a-la-une/actualites",
        )

    def scrapPage(self, pageNumber, verbose=False):
        page = requests.get(self.base_url.replace("<page-number>", str(pageNumber)))
        soup = BeautifulSoup(page.content, "html.parser")
        articles = soup.find_all("article")
        scraps = []
        for article in articles:
            heading = article.find("h3")
            link = heading.find("a") if heading is not None else None
            href = link.get("href") if link is not None else None
            if heading is None or link is None or not isinstance(href, str):
                # Malformed teaser (no <h3>/<a href>): skip it rather than raising,
                # which would abort the whole page and leave the feed empty.
                continue
            res = {}
            res["title"] = unescape(heading.text.strip())
            res["description"] = unescape(article.select(".o-teaser__infos--top")[0].text.strip())
            res["link"] = self.host + href
            date = article.select(".o-teaser__infos .fw-medium .a-info__text")[0].text.strip()
            res["date"] = dateparser.parse(
                date,
                languages=["fr"],
                settings={"TIMEZONE": "Europe/Paris", "RETURN_AS_TIMEZONE_AWARE": True},
            )
            res["content"] = unescape(link.text.strip())
            res["content_class"] = "node__content"
            scraps.append(res)
        if verbose:
            print(f"{len(scraps)} posts extracted on page {pageNumber}")
        return scraps
