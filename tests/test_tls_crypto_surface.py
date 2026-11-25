"""Guard rails on the TLS / crypto surface (offline, no network).

Triage of the OpenSSL advisory of 2026-11-10 (see ``SECURITY.md``) concluded
that none of its three issues are reachable from this project:

* CVE-2026-95691 (QUIC CRYPTO frame use-after-free) needs OpenSSL's QUIC stack.
* CVE-2026-107496 (``CMS_encrypt()`` infinite loop) needs the CMS API.
* CVE-2026-88823 (AES-GCM-SIV AAD forgery) needs the AES-GCM-SIV cipher.

CPython's stdlib ``ssl`` module exposes none of those APIs, no OpenSSL binding
is declared, and nothing shells out to the ``openssl`` CLI. These tests pin that
invariant: if one of them fails, re-run the CVE triage before relaxing it.
"""

import ast
import re
import ssl
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent

# Packages that expose the low-level OpenSSL EVP / CMS / QUIC APIs themselves.
OPENSSL_BINDINGS = {
    "cryptography",
    "pyopenssl",
    "m2crypto",
    "pycryptodome",
    "pycryptodomex",
}

# Symbols that would have to exist for the 2026-11-10 CVEs to be reachable.
VULNERABLE_API_MARKERS = ("QUIC", "CMS", "GCM_SIV")


def _dist_name(spec: str) -> str:
    """Extract the distribution name from a PEP 508 requirement string."""
    match = re.match(r"^[A-Za-z0-9._-]+", spec.strip())
    return match.group(0).lower() if match else ""


def _declared_packages() -> set[str]:
    """Distribution names declared in ``pyproject.toml`` and ``uv.lock``."""
    names: set[str] = set()

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    requirements = list(pyproject.get("project", {}).get("dependencies", []))
    for group in pyproject.get("dependency-groups", {}).values():
        requirements.extend(requirement for requirement in group if isinstance(requirement, str))
    names.update(filter(None, (_dist_name(req) for req in requirements)))

    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    names.update(package["name"].lower() for package in lock.get("package", []))
    return names


def _project_files() -> list[Path]:
    """Python sources shipped by the project (tests and caches excluded)."""
    files = sorted(ROOT.glob("*.py"))
    for package in ("scrappers", "monitoring"):
        files.extend(sorted((ROOT / package).rglob("*.py")))
    return [path for path in files if "__pycache__" not in path.parts]


@pytest.mark.parametrize("marker", VULNERABLE_API_MARKERS)
def test_stdlib_ssl_exposes_no_vulnerable_api(marker):
    """Python cannot reach the QUIC, CMS or AES-GCM-SIV code paths at all."""
    exposed = [name for name in dir(ssl) if marker.lower() in name.lower()]
    assert exposed == [], f"ssl now exposes {marker}: {exposed} - re-run the OpenSSL CVE triage"


def test_no_openssl_binding_is_declared():
    offending = sorted(_declared_packages() & OPENSSL_BINDINGS)
    assert offending == [], (
        f"OpenSSL binding(s) declared: {offending} - re-run the OpenSSL CVE triage in SECURITY.md"
    )


def test_project_code_does_not_reference_the_openssl_cli():
    """Guards against `subprocess.run(["openssl", ...])` sneaking in."""
    references: dict[str, list[str]] = {}
    for path in _project_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "openssl" in node.value.lower()
            ):
                references.setdefault(str(path.relative_to(ROOT)), []).append(node.value)
    assert references == {}, f"project code references the openssl CLI: {references}"


def test_local_interpreter_reports_an_openssl_version():
    """Sanity check that we are testing against a build exposing OpenSSL's version."""
    assert ssl.OPENSSL_VERSION.startswith("OpenSSL ")
