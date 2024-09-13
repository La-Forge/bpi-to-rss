from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from scrappers.BpifranceScrapper import FEED_PATH as BPI_FEED_PATH
from scrappers.GniusScrapper import FEED_PATH as GNIUS_FEED_PATH


app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=Response)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def get_feed(feed_content):
    if feed_content is None:
        return Response(
            status_code=500, content="Internal Server Error: Could not read RSS feed"
        )
    headers = {"Content-Type": "application/rss+xml; charset=utf-8"}
    return Response(
        content=feed_content, media_type="application/rss+xml", headers=headers
    )


@app.get("/bpi", response_class=Response)
async def get_bpi_feed():
    return get_feed(feed_content=get_rss_bpifrance_feed_content())


@app.get("/gnius", response_class=Response)
async def get_gnius_feed():
    return get_feed(feed_content=get_rss_gnius_feed_content())


def get_rss_bpifrance_feed_content():
    return get_rss_feed_content(file_path=BPI_FEED_PATH)


def get_rss_gnius_feed_content():
    return get_rss_feed_content(file_path=GNIUS_FEED_PATH)


def get_rss_feed_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
