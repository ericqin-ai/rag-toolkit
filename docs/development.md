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

Original editable SVGs live in `docs/assets/`: `logo-{light,dark}.svg`,
`banner-{light,dark}.svg`, and `architecture-{light,dark}.svg`.
`logo.svg` and `banner.svg` remain light-theme compatibility copies.
Three stacked layers represent retrieval processing, with a selected-result stroke.
README picture elements select themes via `prefers-color-scheme`; their fallback is light.
No generated application UI, remote fonts, copied branding or tracking is included.

Palette: primary #6366F1, primary dark #4338CA, secondary #A5B4FC,
success #10B981 (reserved for verified status), dark #0F172A, light #F8FAFC.
Segoe UI/Arial are system-font choices; body text stays native GitHub Markdown.
Banner ratio is 4:1; the portrait architecture stays legible on narrow screens.
See the [brand refresh review](readme-refresh.md) for migration and verification evidence.
