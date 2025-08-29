from fastapi import FastAPI, Query
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from scrappers.BpifranceScrapper import FEED_PATH as BPI_FEED_PATH
from scrappers.GniusScrapper import FEED_PATH as GNIUS_FEED_PATH
from scrappers.IleDeFranceScrapper import FEED_PATH as IDF_FEED_PATH
from scrappers.ProjetAchatPublicScrapper import FEED_PATH as PROJET_ACHAT_FEED_PATH
import uvicorn

import xml.etree.ElementTree as ET
import unicodedata
import re


app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=Response)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def get_feed(feed_content, q: str | None = None):
    if feed_content is None:
        return Response(
            status_code=500, content="Internal Server Error: Could not read RSS feed"
        )
    if q:
        try:
            feed_content = filter_feed_content(feed_content, q)
        except Exception as e:
            print(f"Filter error: {e}")
    headers = {"Content-Type": "application/rss+xml; charset=utf-8"}
    return Response(
        content=feed_content, media_type="application/rss+xml", headers=headers
    )


@app.get("/bpi", response_class=Response)
async def get_bpi_feed(q: str | None = Query(None, alias="q")):
    return get_feed(feed_content=get_rss_bpifrance_feed_content(), q=q)


@app.get("/gnius", response_class=Response)
async def get_gnius_feed(q: str | None = Query(None, alias="q")):
    return get_feed(feed_content=get_rss_gnius_feed_content(), q=q)

@app.get("/idf", response_class=Response)
async def get_idf_feed(q: str | None = Query(None, alias="q")):
    return get_feed(feed_content=get_rss_idf_feed_content(), q=q)

@app.get("/projet-achat", response_class=Response)
async def get_projetachat_feed(q: str | None = Query(None, alias="q")):
    return get_feed(feed_content=get_rss_projetachat_feed_content(), q=q)


def get_rss_bpifrance_feed_content():
    return get_rss_feed_content(file_path=BPI_FEED_PATH)

def get_rss_gnius_feed_content():
    return get_rss_feed_content(file_path=GNIUS_FEED_PATH)

def get_rss_idf_feed_content():
    return get_rss_feed_content(file_path=IDF_FEED_PATH)

def get_rss_projetachat_feed_content():
    return get_rss_feed_content(file_path=PROJET_ACHAT_FEED_PATH)


def get_rss_feed_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None


ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _strip_accents(text: str) -> str:
    if not text:
        return ""
    # Normalize and remove diacritics for accent-insensitive search
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def _normalize(text: str) -> str:
    return _strip_accents(text).lower()


def _tokenize_query(q: str) -> list[str]:
    words = [w.strip('"\'\'') for w in q.split() if w.strip()]
    return words


def _entry_text_atom(entry: ET.Element) -> str:
    title_el = entry.find(ATOM_NS + "title")
    content_el = entry.find(ATOM_NS + "content")
    summary_el = entry.find(ATOM_NS + "summary")
    parts = []
    for el in (title_el, content_el, summary_el):
        if el is not None and el.text:
            parts.append(el.text)
    return " \n ".join(parts)


def _entry_text_rss(item: ET.Element) -> str:
    title_el = item.find("title")
    desc_el = item.find("description")
    content_encoded_el = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
    parts = []
    for el in (title_el, desc_el, content_encoded_el):
        if el is not None and el.text:
            parts.append(el.text)
    return " \n ".join(parts)


def _matches_all_words(haystack: str, words: list[str]) -> bool:
    norm_hay = _normalize(haystack)
    return all(_normalize(w) in norm_hay for w in words)


def filter_feed_content(feed_xml: str, q: str) -> str:
    if not q:
        return feed_xml

    words = _tokenize_query(q)
    if not words:
        return feed_xml

    root = ET.fromstring(feed_xml)

    is_atom = root.tag.endswith("feed") and root.tag.startswith("{")

    if is_atom:
        entries = list(root.findall(ATOM_NS + "entry"))
        for entry in entries:
            text = _entry_text_atom(entry)
            if not _matches_all_words(text, words):
                root.remove(entry)
        if not root.findall(ATOM_NS + "entry"):
            return ""
    else:
        channel = root.find("channel")
        if channel is not None:
            items = list(channel.findall("item"))
            for item in items:
                text = _entry_text_rss(item)
                if not _matches_all_words(text, words):
                    channel.remove(item)
            if not channel.findall("item"):
                return ""

    return ET.tostring(root, encoding="unicode")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)