from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import os


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=Response)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/bpi", response_class=Response)
async def get_bpi_feed():
    feed_content = get_rss_feed('feeds/bpi_feed.xml')
    if feed_content is None:
        return Response(status_code=500, content="Internal Server Error: Could not read RSS feed")
    headers = {"Content-Type": "application/rss+xml; charset=utf-8"}
    return Response(content=feed_content, media_type='application/rss+xml', headers=headers)

@app.get("/gnius", response_class=Response)
async def get_gnius_feed():
    feed_content = get_rss_feed('feeds/gnius_feed.xml')
    if feed_content is None:
        return Response(status_code=500, content="Internal Server Error: Could not read RSS feed")
    headers = {"Content-Type": "application/rss+xml; charset=utf-8"}
    return Response(content=feed_content, media_type='application/rss+xml', headers=headers)

def get_rss_feed(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
