"""Guard rails on the GitHub Actions workflows (parsed offline, no network)."""

from pathlib import Path

import pytest
import yaml

WORKFLOWS = sorted((Path(__file__).parent.parent / ".github" / "workflows").glob("*.yml"))


def _triggers(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    # YAML 1.1 parses the bare key `on` as boolean True.
    triggers = data.get("on", data.get(True))
    return triggers if isinstance(triggers, dict) else dict.fromkeys(triggers or [])


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_push_and_pull_request_do_not_both_run_on_every_branch(path):
    """An unfiltered `push` + `pull_request` runs the job twice for each PR commit."""
    triggers = _triggers(path)
    if "push" not in triggers or "pull_request" not in triggers:
        pytest.skip("workflow does not use both triggers")
    push = triggers["push"] or {}
    assert push.get("branches"), "restrict `push` to the default branch (e.g. branches: [main])"
