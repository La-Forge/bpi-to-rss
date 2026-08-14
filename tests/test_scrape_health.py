"""Unit tests for the scrape consistency checker (no network)."""
from pathlib import Path

from monitoring.scrape_health import (
    SOURCES,
    evaluate_metric,
    last_count_for_source,
    load_history,
    run,
    trim_history,
)


def test_evaluate_metric_zero_is_critical():
    alerts = evaluate_metric("bpifrance", 0, 10, SOURCES["bpifrance"])
    assert alerts and alerts[0]["level"] == "critical"
    assert "0 items" in alerts[0]["message"]


def test_evaluate_metric_below_floor_is_critical():
    alerts = evaluate_metric("bpifrance", 2, 10, SOURCES["bpifrance"])
    assert any(a["level"] == "critical" for a in alerts)


def test_evaluate_metric_drop_vs_previous_is_warning():
    # 40 is > floor (5) but < 50% of the previous run (100) -> warning, not critical.
    alerts = evaluate_metric("bpifrance", 40, 100, SOURCES["bpifrance"])
    assert any(a["level"] == "warning" for a in alerts)
    assert not any(a["level"] == "critical" for a in alerts)


def test_evaluate_metric_healthy():
    alerts = evaluate_metric("bpifrance", 45, 46, SOURCES["bpifrance"])
    assert alerts == []


def test_last_count_and_history(monkeypatch, tmp_path):
    path = Path(tmp_path) / "metrics.json"
    monkeypatch.setenv("SCRAPE_METRICS_FILE", str(path))

    # Missing file -> empty list.
    assert load_history(path) == []

    history = [
        {"source": "bpifrance", "run_at": "2025-01-01", "count": 44},
        {"source": "bpifrance", "run_at": "2025-01-02", "count": 46},
    ]
    assert last_count_for_source(history, "bpifrance") == 46
    assert last_count_for_source(history, "gnius") is None


def test_run_persists_and_healthy(monkeypatch, tmp_path):
    path = Path(tmp_path) / "metrics.json"

    def fake_scrape(source, verbose=False):
        return {
            "source": source,
            "run_at": "2025-01-01T00:00:00+00:00",
            "count": SOURCES[source]["min_count"] + 50,
            "complete_count": 1,
            "completeness_ratio": 1.0,
        }

    report = run(verbose=False, scrape_fn=fake_scrape, history_file=path)
    assert report["alerts"] == []
    assert len(report["sources"]) == len(SOURCES)

    # History file written and readable on the next run.
    history = load_history(path)
    assert len(history) == len(SOURCES)


def test_run_alerts_on_breakage(monkeypatch, tmp_path):
    path = Path(tmp_path) / "metrics.json"

    def fake_break(source, verbose=False):
        return {
            "source": source,
            "run_at": "2025-01-01T00:00:00+00:00",
            "count": 0,
            "complete_count": 0,
            "completeness_ratio": 0.0,
        }

    report = run(verbose=False, scrape_fn=fake_break, history_file=path)
    assert len(report["alerts"]) == len(SOURCES)
    assert all(a["level"] == "critical" for a in report["alerts"])


def test_trim_history_keeps_bound():
    history = [
        {"source": "bpifrance", "run_at": str(i), "count": i}
        for i in range(100)
    ] + [{"source": "gnius", "run_at": "x", "count": 1}]
    trimmed = trim_history(history, max_per_source=10)
    bpifrance = [e for e in trimmed if e["source"] == "bpifrance"]
    assert len(bpifrance) == 10
