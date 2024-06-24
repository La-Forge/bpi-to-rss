from scrappers.base import BaseScrapper
from html import unescape
import requests
import pprint
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import dateparser
from sentry_sdk import capture_exception
import sentry_sdk


class BpiScrapper(BaseScrapper):
    def __init__(self):
        super().__init__(
            base_url="https://www.bpifrance.fr/views/ajax?_wrapper_format=drupal_ajax",
            host="https://www.bpifrance.fr",
            feed_title="BPI - Appels à projets & concours",
            feed_author="Bpifrance",
            feed_link="https://www.bpifrance.fr/nos-appels-a-projets-concours"
        )

    def scrapPage(self, pageNumber, verbose=False):
        data = {
            "view_name": "events_before_end_date",
            "view_display_id": "events_finishing_more_week",
            "view_args": 496,
            "view_path": "/node/7620",
            "view_base_path": "",
            "view_dom_id": "ef9552745c8bdef720fe30fd6af40f43f517516afcef456a33e13f76abc8b567",
            "pager_element": 0,
            "_drupal_ajax": 1,
            "ajax_page_state[theme]": "bpi_main",
            "ajax_page_state[theme_token]": "QCTlfpv1f8P3RVm2pjQi5_mhEahwndMinor5r369hQU",
            "ajax_page_state[libraries]": "better_exposed_filters/auto_submit,better_exposed_filters/general,bpi_lazy_entity/main,bpi_main/global-scripts,bpi_main/global-styling,paragraphs/drupal.paragraphs.unpublished,quicklink/quicklink,quicklink/quicklink_init,statistics/drupal.statistics,system/base,views/views.ajax,views/views.module",
        }

        paginated_url = f"{self.base_url}&page={pageNumber}"

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
