import requests
from bs4 import BeautifulSoup

class GniusScrapper:
    def __init__(self):
        self.URL = "https://gnius.esante.gouv.fr/fr/a-la-une/actualites?page=<page-number>"

    def scrap(self,pageNumber):
        page = requests.get(self.URL)
        soup = BeautifulSoup(page.content, "html.parser")
        articles = soup.find_all("article")
        for article in articles:
            res = {}
            res['title'] = article.find("h3").text.strip()
            res['category']= article.select('.o-teaser__infos--top')[0].text.strip()
            print(res)

