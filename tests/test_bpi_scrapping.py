"""
2024.04.02 - v0.1 - Initial version

"""

import pytest
from bs4 import BeautifulSoup

from scrappers.BpifranceScrapper import BpifranceFeedGeenerator


@pytest.fixture
def bpi_data_soup():
    with open("tests/bpi_data.html", "r") as f:
        html = f.read()
        return BeautifulSoup(html, "html.parser")


@pytest.fixture
def bpi_scrapper():
    return BpifranceFeedGeenerator()


@pytest.fixture
def articles(bpi_scrapper, bpi_data_soup):
    return bpi_scrapper.get_articles(bpi_data_soup)


# write a pytest test that loads the html file "bpi_data.html" and checks if the data is correct
def test_get_articles(bpi_data_soup, bpi_scrapper):
    articles = bpi_scrapper.get_articles(bpi_data_soup)
    assert len(articles) == 9


def test_get_article_title_link(bpi_data_soup, bpi_scrapper):
    articles = bpi_scrapper.get_articles(bpi_data_soup)
    assert bpi_scrapper.get_article_title_and_link(articles[0]) == (
        "Multicap croissance N°4 (MC4)",
        "https://www.bpifrance.fr/nos-appels-a-projets-concours/multicap-croissance-ndeg4-mc4",
    )

def test_get_article_full_content(bpi_data_soup, bpi_scrapper):
    articles = bpi_scrapper.get_articles(bpi_data_soup)
    _, link = bpi_scrapper.get_article_title_and_link(articles[0])
    full_content = bpi_scrapper.get_full_article_content(link, 'body-content')
    assert len(full_content)>0

def test_get_start_date(bpi_data_soup, bpi_scrapper):
    articles = bpi_scrapper.get_articles(bpi_data_soup)
    assert bpi_scrapper.get_start_date(articles[0]).strftime("%Y-%m-%d") == "2023-11-28"


def test_get_article_type(bpi_data_soup, bpi_scrapper):
    articles = bpi_scrapper.get_articles(bpi_data_soup)
    assert bpi_scrapper.get_article_type(articles[0]) == "Appels à projets"


def test_get_article_content(articles, bpi_scrapper):
    content = bpi_scrapper.get_article_content(articles[0])
    assert len(content) == 153
