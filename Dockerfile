# The interpreter is pinned by `.python-version` (tracked in git), which `uv`
# honours here too: the Python build — and the OpenSSL bundled inside it — is the
# same one used by local dev, CI and this image. Bump it deliberately, see
# SECURITY.md.
FROM ghcr.io/astral-sh/uv:0.13.10-alpine3.23-dhi

WORKDIR /app

# Compile bytecode for faster cold starts; copy instead of hard-link because the
# uv cache and the venv end up on different layers.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Dependencies first: this layer is only rebuilt when the lock or the pin moves.
# Copying `.python-version` makes a missing pin a build error rather than a
# silent "whatever uv resolves today".
COPY pyproject.toml uv.lock .python-version ./

# This DHI image runs as uid/gid 65532 and has no /root, so the cache mount is
# aimed at its HOME and chowned to that uid — otherwise uv cannot write it.
RUN --mount=type=cache,target=/home/nonroot/.cache/uv,uid=65532,gid=65532 \
    uv sync --locked --no-dev

# Application code last, so a code change never re-downloads the dependency tree.
COPY . .

# Run the venv directly: `uv run` would re-check and re-sync the environment on
# every container start.
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []

EXPOSE 8000

CMD ["python", "serve_feeds.py"]
