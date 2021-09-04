import requests
from bs4 import BeautifulSoup

class BpiScrapper:
    def __init__(self):
        self.URL = "https://www.bpifrance.fr/views/ajax?_wrapper_format=drupal_ajax"

    def scrapPage(self,pageNumber):

        data = {
            "view_name": "events_before_end_date",
            "view_display_id": "events_finishing_more_week",
            "view_args": 496,
            "view_path": "/node/7620",
            "view_base_path": "",
            "view_dom_id": "527a323f1095779a3102657b4d0d861b1f38a2ba11f925571907847803f32906",
            "pager_element": 0,
            "page": 3,
            "_drupal_ajax": 1,
            "ajax_page_state[theme]": "bpi_main",
            "ajax_page_state[theme_token]": "YLv4rJpLFCWRQgYJnwGwIptKrEooLXNQuLLukVUr7Z0",
            "ajax_page_state[libraries]": "bpi_lazy_entity/main,bpi_main/global-scripts,bpi_main/global-styling,paragraphs/drupal.paragraphs.unpublished,statistics/drupal.statistics,system/base,views/views.ajax,views/views.module"
        }

        page = requests.post(self.URL, data)
        json = page.json()
        content = next(x for x in json if "method" in x and x["method"]=="replaceWith")
        scraps = [];
        if "data" in content:
            soup = BeautifulSoup(content["data"], "html.parser")
            articles = soup.select('[role="article"]')
            for article in articles:
                h3 = article.select('.desc-block .desc h3')[0]
                title = h3.text.strip()
                link = h3.find("a")
                scraps.append({"title": title, "link":link})
        print(scraps)