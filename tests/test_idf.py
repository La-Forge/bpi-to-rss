"""Unit tests for IleDeFranceScrapper parsing logic (no network)."""
import scrappers.IleDeFranceScrapper as mod
from scrappers.IleDeFranceScrapper import IleDeFranceScrapper


def test_parse_date_returns_rfc822_still_contains_date():
    s = IleDeFranceScrapper.parse_date("2025-06-01T12:00:00+0200")
    assert isinstance(s, str)
    assert "2025" in s
    assert "12:00:00" in s
    assert "+0200" in s


def test_parse_date_invalid_returns_none():
    assert IleDeFranceScrapper.parse_date("garbage") is None
    assert IleDeFranceScrapper.parse_date(None) is None


def test_format_articles_builds_fields():
    s = IleDeFranceScrapper()
    records = [
        {
            "nom_de_l_aide_de_la_demarche": "Aide R&D",
            "url_descriptif": "https://example.com/rnd",
            "chapo_txt": "Pour les PME",
            "objectif_txt": "Innovation",
            "qui_peut_en_beneficier": ["PME", "ETI"],
            "date": "2025-06-01T12:00:00+0000",
        }
    ]
    articles = s.format_articles(records)
    assert len(articles) == 1
    a = articles[0]
    assert a["title"] == "Aide R&D"
    assert a["link"] == "https://example.com/rnd"
    assert "PME, ETI" in a["description"]
    assert isinstance(a["date"], str)


def test_format_articles_missing_optionals():
    s = IleDeFranceScrapper()
    articles = s.format_articles([{}])
    assert len(articles) == 1
    a = articles[0]
    # Missing fields fall back to defaults without raising.
    assert a["title"] == "Titre inconnu"
    assert a["description"]
    assert a["date"] is None


def test_scrap_pages_pagination_stops_on_short_page(monkeypatch):
    s = IleDeFranceScrapper()
    s.limit_per_request = 10
    pages = []

    def fake_get(url, params):
        offset = params["offset"]
        pages.append(offset)
        if offset == 0:
            results = [
                {"nom_de_l_aide_de_la_demarche": f"t{i}", "url_descriptif": f"u{i}"}
                for i in range(10)
            ]
        else:
            results = [{"nom_de_l_aide_de_la_demarche": "last", "url_descriptif": "u"}]

        class R:
            def json(self):
                return {"results": results}

            def raise_for_status(self):
                pass

        return R()

    monkeypatch.setattr(mod.requests, "get", fake_get)
    articles = s.scrapPages()
    # Page 0 returned a full page (==limit) so we continue; page 1 is short -> stop.
    assert pages == [0, 10]
    assert len(articles) == 11
