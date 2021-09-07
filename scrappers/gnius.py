import requests
from bs4 import BeautifulSoup

from feedgen.feed import FeedGenerator
class GniusScrapper:
    def __init__(self):

        self.GNIUS_URL = "https://gnius.esante.gouv.fr/fr/a-la-une/actualites?page=<page-number>"
        self.GNIUS_HOST = "https://gnius.esante.gouv.fr"
    def scrapPage(self,pageNumber, verbose=False):
        page = requests.get(self.GNIUS_URL.replace('<page-number>', str(pageNumber)))
        soup = BeautifulSoup(page.content, "html.parser")
        articles = soup.find_all("article")
        scraps = []
        for article in articles:
            res = {}
            link = article.find("h3").find("a")
            res['title'] = article.find("h3").text.strip()
            res['description']= article.select('.o-teaser__infos--top')[0].text.strip()
            res['link']= self.GNIUS_HOST+link['href']
            res['date']= article.select(".o-teaser__infos .fw-medium .a-info__text")[0].text.strip()
            res['content']= link.text.strip()
            scraps.append(res)
            print(res)

        return scraps
        
    def scrapPages(self, verbose=False):
        page = 0
        count_for_current_page = -1
        posts = []
        while count_for_current_page!=0:
            posts_on_current_page = self.scrapPage(pageNumber=page, verbose=verbose)
            posts.extend(posts_on_current_page)
            count_for_current_page = len(posts_on_current_page)
            page = page + 1
        return posts
        
    def generate_feed(self, verbose=True):
        fg = FeedGenerator()
        fg.title('Gnius - Actualités')
        fg.id(self.GNIUS_URL)
        fg.author( {'name':'Bpifrance'} )
        fg.link(href=self.GNIUS_URL, rel='alternate' )
        fg.subtitle('Powered by www.la-forge.ai')
        fg.language('fr')

        #add articles
        articles = self.scrapPages(verbose=verbose)
        for article in articles:
            fe = fg.add_entry()
            fe.id(article['link'])
            fe.title(article['title'])
            fe.link(href=article['link'])
            fe.description(article['description'])

        atomfeed = fg.atom_str(pretty=True) # Get the ATOM feed as string
        return atomfeed