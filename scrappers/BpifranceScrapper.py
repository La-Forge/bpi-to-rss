from scrappers.BaseScrapper import BaseScrapper
from html import unescape
import requests
from bs4 import BeautifulSoup
import dateparser

FEED_PATH = 'feeds/bpi_feed.xml'

class BpifranceScrapper(BaseScrapper):
    """
    Classe pour scrapper les données de BpiFrance - appel à projets. 
    """
    def __init__(self):
        super().__init__(
            base_url = "https://www.bpifrance.fr/views/ajax?_wrapper_format=drupal_ajax&labels=All&view_name=events_before_end_date&view_display_id=events_finishing_more_week&view_args=496&view_path=%2Fnode%2F7620&view_base_path=&view_dom_id=de2b6579af442525efdb3720e2433d578ae6af46c8d2cb9812d17facde4592ff&pager_element=0&_drupal_ajax=1&ajax_page_state%5Btheme%5D=bpi_main&ajax_page_state%5Btheme_token%5D=vUo2YdcgaSQx1XGJHIa_CX496Ili2qa2-fmRJpfpgV8&ajax_page_state%5Blibraries%5D=eJxtztsOwjAIBuAXqusjNXTFDkcPFqrOp3fuYotxN-TnCxA8qmJz-KpFMLgr8dqKha7FSfeJ1PjzkYgZG7DxlRzDe3GYlXSxCShv-A02cvHAFxkbVZV_14UpR1OhQWxQJ7Gh9Qo8HDL0XLtnkgmDuXca53Vltns6M0d5_VwUlERp3K8eYmQRxWQ9CJoH4VPsVge4wesHUgmd8QPX0HW2",
            #base_url="https://www.bpifrance.fr/views/ajax?_wrapper_format=drupal_ajax",
            host="https://www.bpifrance.fr",
            feed_title="BPI - Appels à projets & concours",
            feed_author="Bpifrance",
            feed_link="https://www.bpifrance.fr/nos-appels-a-projets-concours"
        )
        self.has_pagination = True

    def scrapPage(self, pageNumber, verbose=False):
        payload = {
        }

        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'cookie': '_hjSessionUser_1857115=eyJpZCI6IjcxMDBmYTlkLWY3YWQtNWE0MC05ZDZkLTFjODJiNzU2MmY2NCIsImNyZWF0ZWQiOjE3MDE2OTk5MDg4ODEsImV4aXN0aW5nIjp0cnVlfQ==; tCdebugLib=1; TCPID=12455955114162466917; TC_PRIVACY=0%40017%7C404%7C3480%40277%2C279%2C280%2C281%2C282%2C283%2C284%2C287%2C288%2C289%2C302%2C303%2C304%2C309%40240%401716537312946%2C1716537312946%2C1732089312946%40; TC_PRIVACY_CENTER=277%2C279%2C280%2C281%2C282%2C283%2C284%2C287%2C288%2C289%2C302%2C303%2C304%2C309; _pk_id.1.0856=e81da058ea127a2e.1716537319.; _pk_id.2.0856=6a88671d60ca1dc3.1716537319.; _mr_id=6a88671d60ca1dc3',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://www.bpifrance.fr/nos-appels-a-projets-concours',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }

        paginated_url = f"{self.base_url}&page={pageNumber}"

        page = requests.post(paginated_url, headers=headers,data=payload)
        json = page.json()
        content = next(
            x for x in json if "method" in x and x["method"] == "replaceWith"
        )
        scraps = []
        if "data" in content:
            soup = BeautifulSoup(content["data"], "html.parser")
            articles = self.get_articles(soup)
            for article in articles:
                # title and link
                title, link = self.get_article_title_and_link(article=article)
                # date
                start_date = self.get_start_date(article=article)
                # type
                type = self.get_article_type(article=article)

                # content
                content = self.get_article_content(article=article)

                # generate description
                description = f"[{type}][{start_date}]\n{content}"

                scraps.append(
                    {
                        "title": unescape(title),
                        "link": link,
                        "content": unescape(content),
                        "description": unescape(description),
                        "date": start_date,
                        "type": type,
                        "content_class": "body-content"
                    }
                )
        if verbose:
            print(f"{len(scraps)} posts extracted on page {pageNumber}")
        return scraps

    def get_articles(self, content: BeautifulSoup):
        return content.select(".article-card")

    def get_article_title_and_link(self, article: BeautifulSoup) -> tuple[str, str]:
        html_title = article.select(".desc-block .desc h3")[0]
        title = html_title.text.strip()
        link = self.host + html_title.find("a")["href"]
        return title, link

    def get_start_date(self, article: BeautifulSoup) -> str:
        desc_date = article.select(".card-date")[0].text.strip()
        range = desc_date.split(" au ")
        start_date = dateparser.parse(
            range[0],
            languages=["fr"],
            settings={
                "TIMEZONE": "Europe/Paris",
                "RETURN_AS_TIMEZONE_AWARE": True,
            },
        )
        return start_date

    def get_article_type(self, article: BeautifulSoup) -> str:
        return article.select(".rubrique.rubrique-project")[0].text.strip()

    def get_article_content(self, article: BeautifulSoup) -> str:
        p = article.select(".desc-block .desc p")
        content = ""
        if p and len(p):
            content = p[0].text.strip()
        return content
