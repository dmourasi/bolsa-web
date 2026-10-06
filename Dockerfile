# Build context is the repository root. bolsa-core is fetched from GitHub
# during `uv sync`, so the bolsa-core repository must be reachable at build time.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    HOST=0.0.0.0

# uv clones bolsa-core from git, and the slim image ships without git.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.11.7

WORKDIR /app

# Dependencies first, so code-only changes reuse this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev

RUN useradd --create-home --uid 10001 app
USER app

ENV PATH="/app/.venv/bin:$PATH"

# Hosting platforms set PORT; the server reads it through bolsa-web.
CMD ["bolsa-web"]
