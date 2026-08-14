"""Live scrape consistency checker.

For each source this performs a *live* scrape, computes simple metrics and
compares them against per-source thresholds, plus the last recorded count.

Thresholds are config and deliberately kept in git. Metrics *history* (the
append-only list of daily counts) is kept out of git, in a JSON file whose
path is configurable via the SCRAPE_METRICS_FILE env var (default: ./metrics/).

Run manually:
    uv run python monitoring/scrape_health.py

Run from CI (scheduled) and alert on a non-zero exit code.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path

from scrappers.BpifranceScrapper import BpifranceScrapper
from scrappers.GniusScrapper import GniusScrapper
from scrappers.IleDeFranceScrapper import IleDeFranceScrapper
from scrappers.ProjetAchatPublicScrapper import ProjetsAchatScrapper

# Per-source thresholds. min_count is an absolute floor; min_ratio_vs_previous
# alerts when the count drops below that ratio of the last recorded run.
SOURCES = {
    "bpifrance": {"min_count": 5, "min_ratio_vs_previous": 0.5},
    "gnius": {"min_count": 5, "min_ratio_vs_previous": 0.5},
    "idf": {"min_count": 30, "min_ratio_vs_previous": 0.5},
    "projetachat": {"min_count": 30, "min_ratio_vs_previous": 0.5},
}

SCRAPER_FACTORIES = {
    "bpifrance": BpifranceScrapper,
    "gnius": GniusScrapper,
    "idf": IleDeFranceScrapper,
    "projetachat": ProjetsAchatScrapper,
}


def default_history_path() -> Path:
    """History file lives outside git: ./metrics/scrape_metrics.json."""
    return Path(__file__).resolve().parent.parent / "metrics" / "scrape_metrics.json"


def history_path() -> Path:
    return Path(os.environ.get("SCRAPE_METRICS_FILE", str(default_history_path())))


def load_history(path: Path | None = None) -> list[dict]:
    path = Path(path or history_path())
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def last_count_for_source(history: list[dict], source: str) -> int | None:
    for entry in reversed(history):
        if entry.get("source") == source and entry.get("count") is not None:
            return entry["count"]
    return None


def evaluate_metric(source: str, count: int, previous: int | None, config: dict) -> list[dict]:
    """Return a list of alert dicts for the given count.

    Rules:
    - count == 0 is critical (scraper likely broken).
    - count < min_count is critical.
    - a drop vs. the previous run beyond min_ratio_vs_previous is a warning.
    """
    alerts = []
    if count == 0:
        alerts.append(
            {
                "source": source,
                "level": "critical",
                "message": "scraper returned 0 items (likely broken)",
            }
        )
        return alerts
    if count < config["min_count"]:
        alerts.append(
            {
                "source": source,
                "level": "critical",
                "message": (f"count {count} is below the absolute floor {config['min_count']}"),
            }
        )
    if previous:
        threshold = config["min_ratio_vs_previous"] * previous
        if count < threshold:
            alerts.append(
                {
                    "source": source,
                    "level": "warning",
                    "message": (
                        f"count {count} dropped vs previous run ({previous}); "
                        f"below {config['min_ratio_vs_previous']:.0%} of it"
                    ),
                }
            )
    return alerts


def scrape_source(source: str, verbose: bool = False) -> dict:
    """Perform a live scrape and return metrics for one source."""
    scraper = SCRAPER_FACTORIES[source]()
    posts = scraper.scrapPages(verbose=verbose)
    complete = [p for p in posts if p.get("title") and p.get("link") and p.get("date")]
    return {
        "source": source,
        "run_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "count": len(posts),
        "complete_count": len(complete),
        "completeness_ratio": round(len(complete) / len(posts), 4) if posts else 0.0,
    }


def trim_history(history: list[dict], max_per_source: int = 60) -> list[dict]:
    """Keep at most ``max_per_source`` entries per source (oldest dropped)."""
    kept: list[dict] = []
    for source in SOURCES:
        entries = [e for e in history if e.get("source") == source]
        kept.extend(entries[-max_per_source:])
    unknown = [e for e in history if e.get("source") not in SOURCES]
    kept.extend(unknown)
    return kept


def write_history(path: Path, history: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")


def run(
    verbose: bool = False,
    scrape_fn=None,
    history_file: Path | None = None,
) -> dict:
    """Scrape all sources, evaluate, persist history and return a report."""
    path = Path(history_file or history_path())
    scrape_fn = scrape_fn or scrape_source
    history = load_history(path)

    report = {
        "run_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "sources": {},
        "alerts": [],
    }
    new_entries: list[dict] = []

    for source, config in SOURCES.items():
        try:
            metric = scrape_fn(source, verbose)
        except Exception as exc:  # noqa: BLE001 - a scrape error is an alert
            report["alerts"].append(
                {
                    "source": source,
                    "level": "critical",
                    "message": f"scrape failed: {exc}",
                }
            )
            new_entries.append({"source": source, "run_at": report["run_at"], "count": 0})
            continue

        previous = last_count_for_source(history, source)
        report["sources"][source] = metric
        report["alerts"].extend(evaluate_metric(source, metric["count"], previous, config))
        new_entries.append({"source": source, "run_at": metric["run_at"], "count": metric["count"]})

    history = trim_history(history + new_entries)
    write_history(path, history)
    return report


def main(argv=None) -> int:
    verbose = "-v" in (argv or sys.argv[1:])
    report = run(verbose=verbose)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["alerts"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
