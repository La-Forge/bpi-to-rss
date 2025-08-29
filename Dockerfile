FROM ghcr.io/astral-sh/uv:alpine

WORKDIR /app

COPY . .

RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "python", "serve_feeds.py"]