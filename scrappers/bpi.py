import requests
import pprint
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from http.server import BaseHTTPRequestHandler, HTTPServer
import time


class BpiScrapper:
    def __init__(self):
        self.URL = 'https://www.bpifrance.fr/views/ajax?_wrapper_format=drupal_ajax'
        self.BPI_URL = 'https://www.bpifrance.fr/nos-appels-a-projets-concours'
        self.BPI_HOST = 'https://www.bpifrance.fr'


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
        

    def scrapPage(self,pageNumber, verbose = False):

        data = {
            "view_name": "events_before_end_date",
            "view_display_id": "events_finishing_more_week",
            "view_args": 496,
            "view_path": "/node/7620",
            "view_base_path": "",
            "view_dom_id": "527a323f1095779a3102657b4d0d861b1f38a2ba11f925571907847803f32906",
            "pager_element": 0,
            "page": pageNumber,
            "_drupal_ajax": 1,
            "ajax_page_state[theme]": "bpi_main",
            "ajax_page_state[theme_token]": "YLv4rJpLFCWRQgYJnwGwIptKrEooLXNQuLLukVUr7Z0",
            "ajax_page_state[libraries]": "bpi_lazy_entity/main,bpi_main/global-scripts,bpi_main/global-styling,paragraphs/drupal.paragraphs.unpublished,statistics/drupal.statistics,system/base,views/views.ajax,views/views.module"
        }

        page = requests.post(self.URL, data)
        json = page.json()
        content = next(x for x in json if "method" in x and x["method"]=="replaceWith")
        scraps = []
        if "data" in content:
            soup = BeautifulSoup(content["data"], "html.parser")
            articles = soup.select('[role="article"]')
            for article in articles:
                desc_h3 = article.select('.desc-block .desc h3')[0]

                #title
                title = desc_h3.text.strip()

                #link
                link = self.BPI_HOST + desc_h3.find("a")["href"]
                
                #date
                desc_date = article.select('.desc-block .card-date')[0].text.strip()

                #type
                type = article.select('.desc-block .rubrique-project')[0].text.strip()
                
                #content
                content = article.select('.desc-block .desc p')[0].text.strip()

                #generate description
                description =  f"[{type}][{desc_date}]\n{content}"


                scraps.append({"title": title, "link":link, "content" : content, "description" : description, "date": desc_date, "type":type})
        if verbose:
            print(f"{len(scraps)} posts extracted on page {pageNumber}")        
        return scraps

    def print_data(self,verbose=False):
        posts = self.scrapPages()
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(posts)
        print(f"{len(posts)} extracted")        

    def generate_feed(self, verbose=True):
        fg = FeedGenerator()
        fg.title('BPI - Appels à projets & concours')
        fg.id(self.BPI_URL)
        fg.author( {'name':'Bpifrance'} )
        fg.link(href=self.BPI_URL, rel='alternate' )
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