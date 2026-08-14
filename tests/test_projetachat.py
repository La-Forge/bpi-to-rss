"""Unit tests for ProjetsAchatScrapper parsing logic (no network)."""
import scrappers.ProjetAchatPublicScrapper as mod
from scrappers.ProjetAchatPublicScrapper import ProjetsAchatScrapper


def test_parse_date_none_or_invalid():
    assert ProjetsAchatScrapper.parse_date(None) is None
    assert ProjetsAchatScrapper.parse_date("not-a-date") is None


def test_parse_date_naive_becomes_utc():
    dt = ProjetsAchatScrapper.parse_date("2025-01-15")
    assert dt is not None
    assert dt.year == 2025
    assert dt.tzinfo is not None


def test_parse_date_aware_keeps_tz():
    dt = ProjetsAchatScrapper.parse_date("2025-01-15T10:00:00+02:00")
    assert dt is not None
    assert dt.tzinfo is not None


def test_format_articles_builds_fields(monkeypatch):
    s = ProjetsAchatScrapper()
    monkeypatch.setattr(
        s, "get_entity_name_from_siren", lambda siren: "Mairie de Paris"
    )
    records = [
        {
            "fields": {
                "libelle": "Travaux école",
                "code": "123",
                "description": "Des travaux",
                "statut": "Prévisionnel",
                "categorie_d_achat": "BTP",
                "date_previsionnelle_de_publication": "2025-06-01",
            }
        }
    ]
    articles = s.format_articles(records)
    assert len(articles) == 1
    a = articles[0]
    assert a["title"] == "Travaux école"
    assert a["link"] == "https://projets-achats.marches-publics.gouv.fr/project/123"
    assert "Mairie de Paris" in a["description"]
    assert a["date"].tzinfo is not None
    assert a["content_class"] is None


def test_format_articles_no_siren_no_network():
    s = ProjetsAchatScrapper()
    articles = s.format_articles(
        [{"fields": {"libelle": "Sans siren", "code": "9"}}]
    )
    assert len(articles) == 1
    assert articles[0]["title"] == "Sans siren"
    assert "—" in articles[0]["description"]


def test_entity_name_from_siren_is_cached(monkeypatch):
    s = ProjetsAchatScrapper()
    calls = {"n": 0}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"nom_complet": "Acme SARL"}

    def fake_get(url, timeout=6):
        calls["n"] += 1
        return FakeResponse()

    monkeypatch.setattr(mod.requests, "get", fake_get)
    assert s.get_entity_name_from_siren("123456789") == "Acme SARL"
    assert s.get_entity_name_from_siren("123456789") == "Acme SARL"
    assert calls["n"] == 1


def test_entity_name_none_and_error(monkeypatch):
    s = ProjetsAchatScrapper()
    assert s.get_entity_name_from_siren(None) is None

    class FailingResponse:
        status_code = 404

        def json(self):
            return {}

    monkeypatch.setattr(
        mod.requests, "get", lambda url, timeout=6: FailingResponse()
    )
    assert s.get_entity_name_from_siren("111111111") is None
