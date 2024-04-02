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

sentry_sdk.init(
    "https://050cb1f4aff04d22af23721245c4ae35@o1031661.ingest.sentry.io/5998395",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)


class BpiScrapper:
    def __init__(self):
        self.URL = "https://www.bpifrance.fr/views/ajax?_wrapper_format=drupal_ajax"
        self.BPI_URL = "https://www.bpifrance.fr/nos-appels-a-projets-concours"
        self.BPI_HOST = "https://www.bpifrance.fr"

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
        data = {
            "view_name": "events_before_end_date",
            "view_display_id": "events_finishing_more_week",
            "view_args": 496,
            "view_path": "/node/7620",
            "view_base_path": "",
            "view_dom_id": "ef9552745c8bdef720fe30fd6af40f43f517516afcef456a33e13f76abc8b567",
            "pager_element": 0,
            # "page": pageNumber,
            "_drupal_ajax": 1,
            "ajax_page_state[theme]": "bpi_main",
            "ajax_page_state[theme_token]": "QCTlfpv1f8P3RVm2pjQi5_mhEahwndMinor5r369hQU",
            "ajax_page_state[libraries]": "better_exposed_filters/auto_submit,better_exposed_filters/general,bpi_lazy_entity/main,bpi_main/global-scripts,bpi_main/global-styling,paragraphs/drupal.paragraphs.unpublished,quicklink/quicklink,quicklink/quicklink_init,statistics/drupal.statistics,system/base,views/views.ajax,views/views.module",
        }

        paginated_url = f"{self.URL}&page={pageNumber}"

        page = requests.post(paginated_url, data)
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
        link = self.BPI_HOST + html_title.find("a")["href"]
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

    def print_data(self, verbose=False):
        posts = self.scrapPages()
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(posts)
        print(f"{len(posts)} extracted")

    def generate_feed(self, verbose=True):
        fg = FeedGenerator()
        fg.title("BPI - Appels à projets & concours")
        fg.id(self.BPI_URL)
        fg.author({"name": "Bpifrance"})
        fg.link(
            href=self.BPI_URL,
            rel="alternate",
        )
        fg.subtitle("Powered by www.la-forge.ai")
        fg.language("fr")

        # add articles
        try:
            articles = self.scrapPages(verbose=verbose)
            for article in articles:
                fe = fg.add_entry()
                fe.id(article["link"])
                fe.title(article["title"])
                fe.link(href=article["link"])
                fe.description(article["description"])
                fe.pubDate(article["date"])
        except Exception as e:
            print(e)
            capture_exception(e)
        atomfeed = fg.atom_str(pretty=True)  # Get the ATOM feed as string
        return atomfeed
