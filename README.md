# bpi-to-rss

## Dependencies 

`uv` : install [here](https://docs.astral.sh/uv/getting-started/installation/)

## installation

1. clone the git repository

```sh
git clone git@github.com:La-Forge/bpi-to-rss.git
```

2. install the dependencies

```sh
uv sync
```

## launch the web service

Either launch it manually:

```sh
python3 generate_feeds.py
python3 serve_feeds.py 8000
```

or use the `generate_feeds.sh` script to generate the feeds every hour, which can be put in a crontab if necessary : `0 * * * * {path_to_file}`

```sh
sh ./generate_feeds.sh
sh ./start_service.sh
```

## Tests

Tests are written with **pytest** and run in parallel via **pytest-xdist**.

```sh
uv run pytest           # run all offline tests (parallel, no network)
uv run pytest -m live   # live tests only (hits real sites)
uv run pytest -x        # stop on first failure for debugging
```

### Test structure

| Location | What it covers |
|---|---|
| `tests/test_web_scrapper.py` | URL normalisation, pagination loop, `max_pages` guard |
| `tests/test_projetachat.py` | ProjetAchat API parsing, date handling, SIREN cache |
| `tests/test_idf.py` | IDF API parsing, date conversion, pagination |
| `tests/test_serve_feeds.py` | Feed filtering (`?q=`), accent-insensitive search, Atom/RSS |
| `tests/test_scrape_health.py` | Consistency-monitoring alert logic (offline, mocked) |
| `tests/test_bpi_scrapping.py` | **Live only** (`@pytest.mark.live`) — real Bpifrance site |

All network calls are mocked in offline tests. The `tests/conftest.py` fixture
also disables Sentry to prevent network noise during test runs.

### Pre-commit hooks

The repo ships a `.pre-commit-config.yaml` that runs `ruff --fix` and `ty` on
every commit. Activate it once:

```sh
pre-commit install
```

Then commits are blocked (exit ≠ 0) if either `uvx ruff check --fix .` or
`uvx ty check .` reports any issue. Run everything manually with:

```sh
pre-commit run --all-files
```

### CI

- **Push / pull request** — lint (`ruff`) + offline tests (`pytest`) run in CI.
- **Daily (05:30 UTC)** — `monitoring/scrape_health.py` scrapes all 4 live sources,
  checks counts against thresholds, stores history as a GitHub artifact,
  and opens an issue if a scraper breaks or drops sharply.

## Lint & type checking

```sh
uv run ruff check .             # lint whole repo (line-length 100)
uv run ruff check --fix .       # auto-fix safe issues
uvx ty check                    # type checker (modern union syntax)
```


## search for terms in Projet Achat
You can now search for terms in the URL for the Projet Achat branch, by using the ?q='chosen terms' at the end of the URL. 

Example : https://rss.la-forge.dev/projet-achat?q=intelligence artificielle in your broser. 
 
