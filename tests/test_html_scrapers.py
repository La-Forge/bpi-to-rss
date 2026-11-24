"""Unit tests for the HTML-based scrapers (Gnius, Bpifrance, WebScrapper) - no network."""

from datetime import datetime

from bs4 import BeautifulSoup

import scrappers.BpifranceScrapper as bpi_mod
import scrappers.GniusScrapper as gnius_mod
import scrappers.WebScrapper as web_mod
from scrappers.BpifranceScrapper import BpifranceScrapper
from scrappers.GniusScrapper import GniusScrapper
from scrappers.WebScrapper import WebScrapper

GNIUS_HTML = b"""
<html><body>
  <article>
    <h3><a href="/fr/a-la-une/actualites/un-teaser">Titre &amp; Cie</a></h3>
    <div class="o-teaser__infos--top">Une description</div>
    <div class="o-teaser__infos"><span class="fw-medium">
      <span class="a-info__text">12 janvier 2026</span>
    </span></div>
  </article>
  <article><p>Teaser sans titre ni lien</p></article>
  <article>
    <h3>Sans lien</h3>
    <div class="o-teaser__infos--top">x</div>
    <div class="o-teaser__infos"><span class="fw-medium">
      <span class="a-info__text">1 janvier 2026</span>
    </span></div>
  </article>
</body></html>
"""

BPI_CARDS = """
<div class="article-card">
  <div class="card-date">1 janvier 2026 au 3 mars 2026</div>
  <div class="rubrique rubrique-project">Projet</div>
  <div class="desc-block"><div class="desc">
    <h3><a href="/node/1">Appel a projets</a></h3>
    <p>Resume court.</p>
  </div></div>
</div>
<div class="article-card">
  <div class="desc-block"><div class="desc"><h3>Sans lien</h3></div></div>
</div>
"""


class _FakeResponse:
    """Minimal stand-in for a requests response."""

    def __init__(self, content=b"", status_code=200):
        self.content = content
        self.status_code = status_code
        self.apparent_encoding = "utf-8"
        self.encoding = "utf-8"

    def json(self):
        return [{"method": "replaceWith", "data": BPI_CARDS}]


def _make_web_scrapper():
    return WebScrapper(
        base_url="https://example.com",
        host="https://example.com",
        feed_title="t",
        feed_author="a",
        feed_link="l",
    )


def test_gnius_scrap_page_parses_teasers_and_skips_malformed(monkeypatch):
    monkeypatch.setattr(gnius_mod.requests, "get", lambda url, **kw: _FakeResponse(GNIUS_HTML))
    scraps = GniusScrapper().scrapPage(pageNumber=0)

    # The two articles without an <a href> are skipped, the valid one is parsed.
    assert len(scraps) == 1
    scrap = scraps[0]
    assert scrap["title"] == "Titre & Cie"
    assert scrap["description"] == "Une description"
    assert scrap["link"] == "https://gnius.esante.gouv.fr/fr/a-la-une/actualites/un-teaser"
    assert scrap["content"] == "Titre & Cie"
    assert scrap["content_class"] == "node__content"
    assert isinstance(scrap["date"], datetime)
    assert (scrap["date"].year, scrap["date"].month, scrap["date"].day) == (2026, 1, 12)


def test_bpi_scrap_page_parses_cards_and_skips_card_without_link(monkeypatch):
    monkeypatch.setattr(bpi_mod.requests, "post", lambda url, **kw: _FakeResponse())
    scraps = BpifranceScrapper().scrapPage(pageNumber=0)

    assert len(scraps) == 1
    scrap = scraps[0]
    assert scrap["title"] == "Appel a projets"
    assert scrap["link"] == "https://www.bpifrance.fr/node/1"
    assert scrap["type"] == "Projet"
    assert scrap["content"] == "Resume court."
    assert isinstance(scrap["date"], datetime)
    assert scrap["description"].startswith("[Projet][")
    assert scrap["description"].endswith("Resume court.")


def test_bpi_title_and_link_returns_none_when_href_missing():
    html = '<div class="desc-block"><div class="desc"><h3>Titre sans lien</h3></div></div>'
    soup = BeautifulSoup(html, "html.parser")
    assert BpifranceScrapper().get_article_title_and_link(soup) is None


def test_bpi_title_and_link_builds_absolute_url():
    html = (
        '<div class="desc-block"><div class="desc">'
        '<h3><a href="/node/7">Un titre</a></h3>'
        "</div></div>"
    )
    parsed = BpifranceScrapper().get_article_title_and_link(BeautifulSoup(html, "html.parser"))
    assert parsed == ("Un titre", "https://www.bpifrance.fr/node/7")


def test_web_scrapper_full_content_prefers_content_class(monkeypatch):
    body = b'<html><body><div class="node__content"><p>a</p><p>b</p></div></body></html>'
    monkeypatch.setattr(web_mod.requests, "get", lambda url, **kw: _FakeResponse(body))
    ws = _make_web_scrapper()
    assert ws.get_full_article_content("https://example.com/x", "node__content") == "a\nb"


def test_web_scrapper_full_content_falls_back_to_article(monkeypatch):
    body = b"<html><body><article><p>c</p></article></body></html>"
    monkeypatch.setattr(web_mod.requests, "get", lambda url, **kw: _FakeResponse(body))
    assert _make_web_scrapper().get_full_article_content("https://example.com/x", None) == "c"


def test_web_scrapper_full_content_empty_on_http_error(monkeypatch):
    monkeypatch.setattr(web_mod.requests, "get", lambda url, **kw: _FakeResponse(b"", 404))
    assert _make_web_scrapper().get_full_article_content("https://example.com/x", None) == ""
