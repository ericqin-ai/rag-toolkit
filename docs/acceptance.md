# v0.2 final acceptance — 2026-11-26

## Implemented functionality

- Seven working Streamlit pages: Overview, Search, Inspector, Compare, Evaluation,
  Datasets and Settings. Chinese/English UI and native Light/Dark configuration.
- Independent BM25/Dense recall, actual fusion/reranker candidates, ranks/scores,
  dropped-candidate status, stage/total timing, raw StageTrace and JSON export.
  Inspector uses separate recall-channel subplots; full IDs remain in hover/tables.
- Five actual comparison strategies, annotation-based metrics, per-query evidence,
  rule-based diagnostic clues (never automatically confirmed root causes), and
  JSON/CSV/Markdown evaluation reports.
- Dataset upload/paste/validation, document/chunk preview, judgment editing,
  public bundled MIT samples, index status and clearing without discarding models/settings.
- Testable service layers; validated configuration import/export, atomic incompatible
  index/model replacement, effective-default normalization and credential redaction.
  API failure middleware also prevents handled raw backend exceptions propagating
  into the ASGI server logger; public response contracts are preserved.
- Original accessible [SVG logo](assets/logo.svg) and [banner](assets/banner.svg).
  Detailed [API](api.md), [configuration](configuration.md), [architecture](architecture.md),
  [development](development.md), [benchmark status](benchmarks.md), [limits](limitations.md)
  and [capture instructions](screenshots.md), with synchronized English/Chinese READMEs.

## Actual verification results

Host: Windows, Python 3.12.9. Tests remain offline; normal local socket access was
needed outside the restricted sandbox for TestClient/AppTest/browser automation.

```text
uv run pytest
============================ 110 passed in 17.54s =============================

uv run ruff check .
All checks passed!

uv run ruff format --check .
106 files already formatted

uv run python scripts/verify_readme.py
README.md: exact SDK example executed; first result intro
README.zh-CN.md: exact SDK example executed; first result intro
111 local documentation links verified; 2 SVG assets parsed
18 screenshot files verified against capture metadata
```

Link checks cover local repository targets; external CI status is not claimed. The exact README SDK example also ran directly via
`uv run python examples/readme_sdk.py`. Basic/hybrid/rerank CLI examples completed,
and the offline evaluation was rerun: 6 indexed chunks, 8 queries, with its real
report refreshed. No real-model benchmark score has been invented.

`uv sync --locked --offline` succeeded. `docker compose config --quiet` succeeded;
Docker image build/container startup is not claimed. The API was actually started
with Uvicorn on localhost:8000: health and all three JSON request examples in the
API guide returned HTTP 200 over live HTTP (also verified using TestClient).

## Browser and layout acceptance

Chrome was launched headlessly with an isolated temporary profile; no existing
personal browser session was captured. Streamlit actually ran on localhost:8507
with `configs/offline.yaml`. All seven pages passed at 1440×1000 and 390×844:
no Streamlit exception panels or root horizontal overflow in those checks.

There are 18 real PNG captures in [the manifest](assets/screenshots/manifest.json):
14 page/layout frames, two scrolled Plotly views and two native Dark views.
Native theme foreground changed from `rgb(47, 45, 43)` to `rgb(237, 235, 232)`;
the Dark Inspector screenshot was visually checked for Plotly theme adaptation.
Screenshots are viewport captures, not full-page images or mockups. GIF recording
was not performed; honest local recording/conversion instructions are provided.

Independent review identified server-level exception propagation; it was reproduced
with strict TestClient exception propagation and fixed before the green full run.
Browser inspection led to explicit native light/dark theme accents and separated
recall-channel chart axes. No global CSS theme hack or initializer business logic
was introduced.

## Known limits

No real-model/public-dataset benchmark, live real-model/Elasticsearch integration,
GPU validation or Docker runtime acceptance is claimed. Indexes and history are
in memory; use one API worker. Remote writes are nontransactional and old remote
session indexes need cleanup. Authentication and durable multi-process state are
future work. PDF/semantic splitters remain abstract extension points. Third-party
verbose HTTP logs/provider startup failures are outside the handled-request logging
boundary; keep secrets out of URLs and arbitrary user text. See [full limits](limitations.md).

## Git snapshot before approval

Branch: `codex/v02-workbench`. This is the cumulative uncommitted work from all three rounds,
not a Round 3-only diff. Existing user changes in `AGENTS.md` are preserved and are
included by Git's output; they were not authored by this work.
No staging, commit, push or publication has been performed. Default diff statistics
exclude untracked files, which include the new service modules, guides, examples,
original logo and screenshot assets listed by status.

`git status --short`:

```text
 M .github/workflows/ci.yml
 M AGENTS.md
 M README.md
 M README.zh-CN.md
 M docs/assets/banner.svg
 M pyproject.toml
 M src/rag_toolkit/api/app.py
 M src/rag_toolkit/pipeline/retrieval.py
 M src/rag_toolkit/retrievers/bm25.py
 M src/rag_toolkit/utils/text.py
 M src/rag_toolkit/web/app.py
 M src/rag_toolkit/web/data_view.py
 M src/rag_toolkit/web/datasets.py
 M src/rag_toolkit/web/evaluation.py
 M src/rag_toolkit/web/inspection.py
 M src/rag_toolkit/web/inspector.py
 M src/rag_toolkit/web/search.py
 M src/rag_toolkit/web/session.py
 M tests/test_api.py
 M uv.lock
?? .streamlit/
?? docs/acceptance.md
?? docs/api.md
?? docs/architecture.md
?? docs/assets/logo.svg
?? docs/assets/screenshots/
?? docs/benchmarks.md
?? docs/configuration.md
?? docs/development.md
?? docs/index.md
?? docs/limitations.md
?? docs/screenshots.md
?? docs/v02-round1-design.md
?? docs/v02-round2-plan.md
?? docs/web-workbench.md
?? examples/readme_sdk.py
?? scripts/
?? src/rag_toolkit/web/activity.py
?? src/rag_toolkit/web/charts.py
?? src/rag_toolkit/web/compare.py
?? src/rag_toolkit/web/controls.py
?? src/rag_toolkit/web/i18n.py
?? src/rag_toolkit/web/model_controls.py
?? src/rag_toolkit/web/overview.py
?? src/rag_toolkit/web/services/
?? src/rag_toolkit/web/settings.py
?? tests/test_round2.py
?? tests/test_workbench.py
```

`git diff --stat`:

```text
 .github/workflows/ci.yml              |   2 +
 AGENTS.md                             |   8 +
 README.md                             | 403 ++++++++++++++--------------------
 README.zh-CN.md                       | 392 ++++++++++++++-------------------
 docs/assets/banner.svg                |  40 ++--
 pyproject.toml                        |  11 +-
 src/rag_toolkit/api/app.py            |  13 +-
 src/rag_toolkit/pipeline/retrieval.py |  11 +-
 src/rag_toolkit/retrievers/bm25.py    |   7 +-
 src/rag_toolkit/utils/text.py         |   4 +
 src/rag_toolkit/web/app.py            |  38 +++-
 src/rag_toolkit/web/data_view.py      | 118 +++++++---
 src/rag_toolkit/web/datasets.py       |  54 +++--
 src/rag_toolkit/web/evaluation.py     | 164 +++++++++++---
 src/rag_toolkit/web/inspection.py     |  53 +++--
 src/rag_toolkit/web/inspector.py      |  14 +-
 src/rag_toolkit/web/search.py         |  79 +++++--
 src/rag_toolkit/web/session.py        |  51 ++++-
 tests/test_api.py                     |   5 +-
 uv.lock                               |  15 ++
 20 files changed, 844 insertions(+), 638 deletions(-)
```

Ready for user review. Commit and push remain blocked on the user's explicit confirmation.
