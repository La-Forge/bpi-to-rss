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

@app.get("/bpi", response_class=Response, responses={200: {"content": {"application/rss+xml": {}}}})
async def get_bpi_feed():
    return get_rss_feed('feeds/bpi_feed.xml')

@app.get("/gnius", response_class=Response, responses={200: {"content": {"application/rss+xml": {}}}})
async def get_gnius_feed():
    return get_rss_feed('feeds/gnius_feed.xml')

def get_rss_feed(file_path: str):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(file_path, 'rb') as file:
        rss_content = file.read()
    return Response(content=rss_content, media_type="application/rss+xml; charset=utf-8")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
