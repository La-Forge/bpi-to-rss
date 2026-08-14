"""Unit tests for WebScrapper helpers and pagination (no network)."""

from scrappers.WebScrapper import WebScrapper


def _make(base_url="https://www.bpifrance.fr"):
    return WebScrapper(
        base_url=base_url,
        host="https://www.bpifrance.fr",
        feed_title="t",
        feed_author="a",
        feed_link="l",
    )


def test_normalize_url_empty():
    ws = _make()
    assert ws._normalize_url(None) == "https://www.bpifrance.fr"
    assert ws._normalize_url("") == "https://www.bpifrance.fr"
    # Whitespace-only is truthy, so it goes through urljoin (adds a trailing slash).
    assert ws._normalize_url("   ") == "https://www.bpifrance.fr/"


def test_normalize_url_absolute_unchanged():
    ws = _make()
    url = "https://www.bpifrance.fr/foo/bar"
    assert ws._normalize_url(url) == url


def test_normalize_url_relative_joined():
    ws = _make()
    assert ws._normalize_url("/foo/bar") == "https://www.bpifrance.fr/foo/bar"
    assert ws._normalize_url("foo/bar") == "https://www.bpifrance.fr/foo/bar"


def test_normalize_url_embedded_scheme():
    ws = _make()
    # Historically broken URL like "www.bpifrance.frhttps://..."
    url = "www.bpifrance.frhttps://www.bpifrance.fr/node/7620"
    assert ws._normalize_url(url) == "https://www.bpifrance.fr/node/7620"


def test_normalize_url_strips_whitespace():
    ws = _make()
    assert ws._normalize_url("  https://example.com/x  ") == "https://example.com/x"


def test_scrap_pages_stops_when_page_empty():
    ws = _make()
    calls = []

    def fake_scrap_page(pageNumber, verbose=False):
        calls.append(pageNumber)
        return [{"link": "x"}] if pageNumber < 2 else []

    ws.scrapPage = fake_scrap_page
    posts = ws.scrapPages()
    assert len(posts) == 2
    assert calls == [0, 1, 2]


def test_scrap_pages_max_pages_guard():
    ws = _make()
    ws.scrapPage = lambda pageNumber, verbose=False: [{"link": "x"}]
    posts = ws.scrapPages(max_pages=5)
    # The guard stops pagination after 5 pages even though none was empty.
    assert len(posts) == 5
