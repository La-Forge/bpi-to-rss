from scrappers.BaseScrapper import BaseScrapper
from html import unescape
import requests
from bs4 import BeautifulSoup
import dateparser


FEED_PATH = 'feeds/gnius_feed.xml'

class GniusScrapper(BaseScrapper):
    """
    Classe pour scrapper les données de GNius - actualités. 
    """
    def __init__(self):
        super().__init__(
            base_url="https://gnius.esante.gouv.fr/fr/a-la-une/actualites?page=<page-number>",
            host="https://gnius.esante.gouv.fr",
            feed_title="Gnius - Actualités",
            feed_author="Gnius",
            feed_link="https://gnius.esante.gouv.fr/fr/a-la-une/actualites"
        )
        self.has_pagination = True

    def scrapPage(self, pageNumber, verbose=False):
        page = requests.get(self.base_url.replace("<page-number>", str(pageNumber)))
        soup = BeautifulSoup(page.content, "html.parser")
        articles = soup.find_all("article")
        scraps = []
        for article in articles:
            res = {}
            link = article.find("h3").find("a")
            res["title"] = unescape(article.find("h3").text.strip())
            res["description"] = unescape(article.select(".o-teaser__infos--top")[0].text.strip())
            res["link"] = self.host + link["href"]
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
