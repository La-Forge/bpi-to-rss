# Security

## Reporting a vulnerability

Open a private security advisory on the GitHub repository
(`Security` -> `Report a vulnerability`) rather than a public issue.

## OpenSSL advisory of 2026-11-10 — triage

Advisory: <https://openssl-library.org/news/secadv/20261110.txt>
Fixes land in OpenSSL **4.1.1**, **4.0.4** and **3.5.10** (release scheduled
2026-12-01). None of these three CVEs is reachable from this project.

| CVE | Title | Vulnerable OpenSSL | Why this project is not exposed |
|---|---|---|---|
| CVE-2026-95691 | QUIC CRYPTO frame retransmission -> heap use-after-free | 4.1, 4.0, 3.5 (3.0 / 1.1.1 / 1.0.2 not affected) | Needs the OpenSSL **QUIC** stack. CPython's `ssl` module has no QUIC API, and `requests`/`urllib3` only speak HTTP/1.1 over TCP. The dev interpreter is OpenSSL 3.0.16, which is not affected at all. |
| CVE-2026-107496 | Infinite loop in `CMS_encrypt()` with an EC group order of 1 | 4.1, 4.0, 3.5, 3.0, 1.1.1, 1.0.2 | Needs an application call to `CMS_encrypt()`/`CMS_encrypt_ex()` with an attacker-supplied EC certificate. Python exposes no CMS API and the project depends on no OpenSSL binding. |
| CVE-2026-88823 | AES-GCM-SIV AAD forgery after zero-length incremental AAD update | 4.1, 4.0, 3.5 (3.0 / 1.1.1 / 1.0.2 not affected) | Needs the AES-GCM-SIV EVP cipher with fragmented AAD. Not exposed by `ssl`, not a negotiable TLS cipher suite, and the dev interpreter is OpenSSL 3.0.16 (AES-GCM-SIV only exists from 3.2 onwards). |

Exposure comes only from TLS done by CPython's `ssl` module on behalf of
`requests` (scraping) and `sentry-sdk`. The service itself is served over plain
HTTP by uvicorn (`serve_feeds.py` has no TLS options), typically behind a
reverse proxy.

`tests/test_tls_crypto_surface.py` pins these assumptions: no OpenSSL binding in
the dependency tree, no reference to the `openssl` CLI in project code, and no
QUIC / CMS / AES-GCM-SIV symbol in the stdlib `ssl` module.

### What would have to be upgraded

Nothing in `pyproject.toml` / `uv.lock`: the vulnerable code lives in **OpenSSL
itself**, which is compiled into the CPython interpreter (the `uv`-managed
standalone builds), not into a Python package.

| Where OpenSSL comes from | Version observed | Status |
|---|---|---|
| `pyproject.toml` + `uv.lock` packages | no OpenSSL binding at all | nothing to upgrade |
| `.venv` interpreter — `uv`-managed CPython 3.13.2 | OpenSSL **3.0.16** (2025-02-11) | not affected by CVE-2026-95691 or CVE-2026-88823 (3.0 not listed); CVE-2026-107496 listed, but the CMS call is unreachable. Note OpenSSL 3.0 is out of free support, so 3.0.24 is premium-only anyway. |
| Newest CPython 3.13 build installable today — 3.13.18 (python-build-standalone `20261124`) | OpenSSL **3.5.9** (2026-09-29) | the 3.5 line *is* listed for all three CVEs → upgrading the interpreter today does **not** fix them |
| Docker image `ghcr.io/la-forge/bpi-to-rss` (`uv:0.13.10-alpine3.23-dhi` + `uv sync`) | uv 0.13.10 + Alpine 3.23 frozen by the tag; interpreter from `.python-version` (`3.13.18` → OpenSSL 3.5.9), same as dev/CI | 3.5 line is listed → bump `.python-version` once a build bundles OpenSSL >= 3.5.10 |

So the single component with a pending upgrade is **the CPython runtime that
bundles OpenSSL**, and the target is a build carrying **OpenSSL >= 3.5.10**
(or >= 4.0.4 / >= 4.1.1). Those releases are published on **2026-12-01**, so
there is nothing to bump today — a rebuild now would only move 3.0.16 to 3.5.9,
which is still inside the affected range.

Residual drift: both halves of the toolchain are now pinned — the interpreter
*version* by `.python-version`, the uv + Alpine pair by the base tag
(`0.13.10-alpine3.23-dhi`) — so a rebuild resolves the same
python-build-standalone build and therefore the same OpenSSL patch level. What is
**not** automated is the bump itself: the `dhi` community tier carries no CVE
remediation SLA (that is a Select/Enterprise feature) and version tags are
immutable, so a stale tag never patches itself. Now that the tag is frozen, add a
dependency bot (Renovate or Dependabot, `docker` ecosystem); note the digest of
the tag you deploy with
`docker buildx imagetools inspect ghcr.io/astral-sh/uv:<tag>` if you want it
recorded, or pin by digest for bit-exact reproducibility.

### Deployment note: the image runs as non-root

The DHI base runs as uid/gid **65532** and ships no package manager. Two
consequences: `feeds/` must be world-readable (0644 files / 0755 dir) for the
container to serve it — a root-owned 0600 file that used to work now yields an
empty feed, because `get_rss_feed_content()` swallows the read error — and
`RUN apk add ...` is impossible, so extra OS packages need a `-dev` DHI variant
or the paid customization tier.

### Follow-up after 2026-12-01

1. Read the OpenSSL version actually in use — never assume it, `ssl` reports the
   bundled copy:

   ```sh
   uv run python -c "import ssl; print(ssl.OPENSSL_VERSION)"
   docker run --rm ghcr.io/la-forge/bpi-to-rss:latest \
     python -c "import ssl; print(ssl.OPENSSL_VERSION)"
   ```

2. If it is below 3.5.10, bump the pin instead of letting `uv` float: set
   `.python-version` to the CPython 3.13 patch whose standalone build bundles
   OpenSSL >= 3.5.10, run `uv sync`, then rebuild and redeploy the image. That
   file is the only place the interpreter version lives — dev, CI and the
   `Dockerfile` all inherit it (`uv python upgrade 3.13` would ignore the pin, so
   don't use it here).
3. Do this even though the three CVEs are unreachable: it keeps scanner findings
   closed and gets the image off OpenSSL 3.0/3.5.x.
4. If a crypto binding (`cryptography`, `pyOpenSSL`, ...) is ever added, re-open
   this triage: those bindings do expose CMS and AEAD ciphers directly, and
   `tests/test_tls_crypto_surface.py` will fail to remind you.
