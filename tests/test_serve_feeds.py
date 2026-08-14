"""Unit tests for serve_feeds filtering logic (no network)."""
import xml.etree.ElementTree as ET

import serve_feeds as sf

ATOM_NS = "{http://www.w3.org/2005/Atom}"

ATOM_FEED = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="fr">
  <id>https://example.com/feed</id>
  <title>Test</title>
  <entry>
    <id>1</id>
    <title>Intelligence artificielle pour la santé</title>
    <content>Un texte de contenu intéressant.</content>
  </entry>
  <entry>
    <id>2</id>
    <title>Autre nouvelle</title>
    <content>Quelque chose d'autre.</content>
  </entry>
</feed>
"""

RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test RSS</title>
    <item><title>Intelligence artificielle</title><description>Un sujet</description></item>
    <item><title>Autre sujet</title><description>Texte</description></item>
  </channel>
</rss>
"""


def test_strip_accents():
    assert sf._strip_accents("éàçù") == "eacu"
    assert sf._strip_accents("") == ""
    assert sf._strip_accents(None) == ""


def test_normalize():
    assert sf._normalize("CAFÉ À Paris") == "cafe a paris"


def test_tokenize_query():
    assert sf._tokenize_query("intelligence artificielle") == [
        "intelligence",
        "artificielle",
    ]
    assert sf._tokenize_query("  ") == []


def test_filter_atom_matches_all_words():
    out = sf.filter_feed_content(ATOM_FEED, "intelligence artificielle")
    root = ET.fromstring(out)
    entries = root.findall(ATOM_NS + "entry")
    assert len(entries) == 1
    title_el = entries[0].find(ATOM_NS + "title")
    assert title_el is not None and title_el.text is not None
    assert "Intelligence artificielle" in title_el.text


def test_filter_atom_accent_insensitive():
    out = sf.filter_feed_content(ATOM_FEED, "sante")
    root = ET.fromstring(out)
    entries = root.findall(ATOM_NS + "entry")
    # "santé" matches "sante" after accent stripping.
    assert len(entries) == 1


def test_filter_atom_empty_result_returns_empty():
    out = sf.filter_feed_content(ATOM_FEED, "introuvablexyz")
    assert out == ""


def test_filter_no_query_returns_original():
    assert sf.filter_feed_content(ATOM_FEED, "") == ATOM_FEED


def test_filter_rss_matches():
    out = sf.filter_feed_content(RSS_FEED, "intelligence")
    root = ET.fromstring(out)
    channel = root.find("channel")
    assert channel is not None
    items = channel.findall("item")
    assert len(items) == 1
    title_el = items[0].find("title")
    assert title_el is not None and title_el.text is not None
    assert "Intelligence artificielle" in title_el.text
