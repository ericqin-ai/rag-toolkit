# Development and contributing

## Tests and CI

```sh
uv sync --locked --group dev
uv run pytest
uv run ruff check .
```

Tests use real FAISS plus injected model/HTTP/Elasticsearch clients; FastAPI
TestClient and Streamlit AppTest verify API/UI behavior without external services.
On the Windows development host, TestClient required sandbox-external execution
because the sandbox restricted event-loop operations. Test execution remained offline.

The repository-root `.github/workflows/ci.yml` runs the standalone project
for Python 3.11/3.12 on Ubuntu: locked dependency installation, Ruff, pytest,
the evaluation example, and Compose configuration validation. See [GitHub Actions](https://github.com/ericqin-ai/rag-toolkit/actions) for run results.


## Docker Compose

Run from the repository root with a running Docker daemon:

```sh
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 api inspector
docker compose down
```

The Dockerfile uses Python 3.12 and uv 0.11.15, installs locked runtime dependencies,
includes libgomp for FAISS, and runs as a non-root user. Compose starts independent
API (8000) and Inspector (8501) services with health checks and offline configuration.
Host ports bind to 127.0.0.1. Images/packages require network access to build; runtime
does not require a remote model. There is no Elasticsearch service, model image,
preloaded index, or persistent index volume in this default stack.

Validation on the development host: Compose configuration can be checked locally;
Docker Desktop's Linux daemon was unavailable, so an image build and container
startup have **not** been verified here.


[Documentation index](index.md)

## Contribution workflow

Use Python 3.11+ and uv; preserve SDK/FastAPI contracts. Put business logic in focused
modules, never package initializers. Keep tests offline, use deterministic injected
models/clients when needed, and label all hash/token results as offline sanity only.
Bug fixes should include a regression test. Keep the two README languages aligned.
Run `uv run python scripts/verify_readme.py` as well as pytest, Ruff and format checks.
Do not commit credentials, browser profiles or verification logs. The screenshot
script is a local Node/Chrome developer utility, not a runtime/CI dependency.

Detailed privacy, deployment and integration limits are in [known limits](limitations.md).

## Visual assets

`docs/assets/logo.svg` and `banner.svg` are original repository-native vectors using
basic paths, shapes and system-font text, with accessible SVG title/description.
Two separate input branches joining a ranked result are the project mark; no external
image generation, copied brand assets, trackers or remote fonts are embedded.
