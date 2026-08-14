# AGENTS.md

Practical notes for working efficiently in this repository. Read this before
making changes — it captures gotchas that are easy to trip on and that cost time.

## What this project is

`bpi-to-rss` scrapes French public-funding sources and republishes them as Atom
feeds served by a FastAPI app. Pipeline: `scrappers/*` -> feedgen Atom XML ->
`feeds/*.xml` (gitignored) -> `serve_feeds.py` (FastAPI, adds `?q=` search).

Four scrapers (all under `scrappers/`):

| Scraper | Type | Notes |
|---|---|---|
| `BpifranceScrapper` | HTML/AJAX (Drupal) | **fragile** — base_url embeds an expiring `theme_token`; hardcoded cookie & Sentry DSN |
| `GniusScrapper` | HTML | GET+pagination, parses `<article>` |
| `IleDeFranceScrapper` | JSON API (OpenDataSoft) | offset pagination |
| `ProjetAchatPublicScrapper` | JSON API (OpenDataSoft) | offset pagination + SIREN->name via a 2nd API |

Python 3.13, managed with **uv** (`pyproject.toml`). Docker image runs
`serve_feeds.py` (see `Dockerfile`).

## Commands

```sh
uv sync                 # install (dev deps incl. pytest, pytest-xdist)
uv run pytest           # fast unit tests (parallel, offline; live excluded)
uv run pytest -m live   # live tests only (hits real sites) - CI-periodic
uv run ruff check .     # whole-repo lint (must stay clean)
uv run ruff check --fix .   # auto-fix safe issues
uvx ty check            # type checker (must stay clean)
pre-commit install      # activate repo pre-commit hooks (.pre-commit-config.yaml)
pre-commit run --all-files   # run ruff --fix + ty over the whole repo
uv run python serve_feeds.py           # serve web service (default :8000)
uv run python generate_feeds.py        # (re)generate feeds from live sources
uv run python monitoring/scrape_health.py   # live consistency check (hits network)
```

Get a live smoke check of the web app without httpx/TestClient:
```sh
uv run python -m uvicorn serve_feeds:app --port 8971 &  # then curl /
```

## Critical gotchas (learned the hard way)

- **`IleDeFranceScrapper` imports `import datetime` (the module).** It was broken
  because `parse_date` used `datetime.strptime` — the module has **no** `strptime`,
  so it silently returned `None` (caught by a broad `except`). The correct call is
  `datetime.datetime.strptime(...)`. Any date-handling there must use
  `datetime.datetime.*`.
- **`Sentry` initializes at import time** in `scrappers/BaseScrapper.py`. Set
  `SENTRY_DSN=""` (empty) to disable — the guard there won't call `sentry_sdk.init`.
  `tests/conftest.py` already does this for tests. Do the same for any script that
  imports scrappers if you don't want Sentry network noise.
- **`feeds/*.xml` are gitignored AND generated.** Never point tests at the real
  `feeds/` dir — use `tmp_path`. The old `tests/test_bpi_scrapping.py` wrote to the
  real file and hit the network; it's now marked `@pytest.mark.live` so it's excluded
  by default.
- **`httpx` is NOT installed.** You cannot use `starlette.testclient.TestClient`
  directly (it errors asking for `httpx2`). For endpoint checks, start uvicorn and
  curl, or add httpx as a dev dep if you want TestClient-based endpoint tests.
- **`BpifranceScrapper` 403s when its `theme_token`/session expires** (repo history
  shows a past 403 fix). The `cookie` and the Sentry DSN are **hardcoded** — treat
  them as secrets; don't add your own gratuitous copies. `monitoring/scrape_health.py`
  is designed to catch the "0 items" failure mode.
- **`WebScrapper` is a base class:** it does NOT define `scrapPage` (subclasses do).
  If you construct it directly for tests, attach a `scrapPage` via plain assignment
  (`ws.scrapPage = fake`), NOT `monkeypatch.setattr` (that raises since the attr
  doesn't exist).

## Tooling config (in `pyproject.toml`)

- **pytest**: `addopts = "-n auto -m \"not live\" -ra"`, `testpaths = ["tests"]`,
  marker `live`. `-n auto` requires `pytest-xdist`.
  Do NOT run `pytest -p no:xdist` — `-n` is still in `addopts` and will error.
- **ruff**: `line-length = 100`, rules `E,F,W,I,UP,B`. Whole repo must pass.
- **Type hints use modern unions** (`str | None`); `uvx ty check` must pass.
- **pre-commit**: `.pre-commit-config.yaml` runs `uvx ruff check --fix .` and
  `uvx ty check .` on every commit (`language: system`, `pass_filenames: false`,
  `always_run: true`). Requires `pre-commit install` per clone. A commit is
  blocked if either command exits non-zero; ruff's `--fix` may auto-stage its
  own changes.

## Testing conventions (established this session)

- `tests/conftest.py` autouse-disables Sentry (`SENTRY_DSN=""` + init("")).
- **Mock all network** with pytest's built-in `monkeypatch` (no `responses`/`requests-mock`
  dep). Example: patch `scrappers.<Module>.requests.get` on the module reference.
- `filter_feed_content`/Atom parsing: the APIScrapper/WebScrapper produce **Atom**
  feeds; `serve_feeds` also handles RSS. Keep both branches tested.
- `tests/test_scrape_health.py` tests the monitoring logic offline by injecting a
  fake `scrape_fn` — never let it hit the network in unit tests.
- Live-only things (real scraping, writing committed feeds) go behind `@pytest.mark.live`.

## CI

- `.github/workflows/pytest.yml` — on `push` + `pull_request`; runs
  `uv sync --frozen`, `uv run ruff check tests monitoring`, `uv run pytest`.
  (Only `tests`/`monitoring` are linted there, but the whole repo is clean.)
- `.github/workflows/live-monitoring.yml` — daily cron (05:30 UTC) + manual dispatch;
  runs `monitoring/scrape_health.py`, persists history as a GitHub artifact
  (external store, not git), opens an issue on alert.
- `.github/workflows/deploy.yml` — on PR merge to main: build/push Docker image
  (`ghcr.io/la-forge/bpi-to-rss`), SSH deploy to server, mount `./feeds`.

## Editor / file-editing tips

- The `editor` tool can **fail to match strings containing backslash-escaped quotes**
  (e.g. `w.strip('"\\'\\'')`). When you can't get an exact `old_text` match on such
  content, either match a broader unique anchor (a whole function/def block) or do a
  byte-exact replacement with a small Python script (read file, `str.replace`, write).

## Locally-edited files to be aware of

`scrappers/BaseScrapper.py`, `WebScrapper.py`, `IleDeFranceScrapper.py`,
`ProjetAchatPublicScrapper.py`, `serve_feeds.py`, `generate_feeds.py` were touched
for bug fixes / lint / types. `monitoring/scrape_health.py` is the consistency
checker (thresholds are config in-git; history JSON is gitignored under `metrics/`).
Before assuming a file is "as upstream", check `git diff`.