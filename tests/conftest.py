"""Shared pytest fixtures and environment setup.

The key side effect we defuse here is Sentry: ``scrappers.BaseScrapper`` calls
``sentry_sdk.init`` at import time. Setting an empty ``SENTRY_DSN`` before any
scrapper module is imported prevents Sentry from initializing (and trying to
reach the network) during tests.
"""

import os

# Must be set before any module that imports scrappers is imported.
os.environ.setdefault("SENTRY_DSN", "")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _disable_sentry():
    """Guard against Sentry initializing even if an env-var fixture runs late."""
    import sentry_sdk

    sentry_sdk.init("")
