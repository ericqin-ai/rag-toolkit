# Round 2 implementation plan

Scope: Complete Overview, Evaluation, Datasets, Settings on the existing Streamlit/service/pipeline architecture. The user's Round 2 request is the execution specification.

1. Add pure settings import/validation/application services. Reject plaintext credentials on import, preserve existing secrets only for redacted round trips, validate before constructing models. Apply query defaults without re-embedding; atomically rebuild for index/model changes. Add optional lexical tokenizer selection without changing existing defaults or APIs.
2. Add evaluation/report services using actual SearchResponse and StageTrace; distinguish rule-based clues from confirmed causes (none are automatically confirmed). Export JSON/CSV/Markdown and retain per-query traces.
3. Complete Overview model/index status and session history, Evaluation strategy charts/filtering, Datasets safe line diagnostics/chunk previews/query management/sample loading, and Settings structured controls/import/export. Keep zh/en and native theme.
4. Add logic tests and AppTest flows including invalid uploads/configs, model/index invalidation, failures, language/session isolation and secret protection. Run full pytest, Ruff and format checks; report actual output and stop for confirmation.

Decision: Tokenizer means the lexical BM25 tokenizer (builtin CJK/Latin or whitespace); it does not change a real embedding model's internal tokenizer. Public examples are the bundled openly inspectable repository samples, loaded offline with source/license links; no live dataset download in UI/tests.

## Round 2 completion and verification

Implemented Overview, Evaluation, Datasets and Settings; added 19 logic/AppTest cases (110 total).

- Overview: document/chunk counts, loaded implementation and model configuration, store/index status, explicit remote-connectivity unknown state, real pipeline graph and last 20 session activities.
- Evaluation: import/replace judgments, current/multi-strategy runs, K validation, actual aggregate/per-query metrics, Plotly comparison, query/failure/clue filters, raw StageTrace evidence, JSON/CSV/Markdown exports. All diagnoses explicitly remain rule-based clues with `confirmed_root_cause: null`.
- Datasets: UTF-8 TXT/Markdown/JSONL upload and paste, safe error line numbers without record echoes, document/chunk previews, editable/exportable/clearable judgments, offline bundled public MIT examples and dataset/index status. Clearing data preserves current settings and loaded models.
- Settings: supported provider/model/device controls, API endpoint/batch size, vector-store configuration, BM25 tokenizer, splitter, recall/final K/fusion defaults, safe YAML/JSON imports and redacted exports. Query defaults reuse vectors; incompatible settings are validated before atomically building a replacement service. Failed application retains the old service. Configuration credentials are never put into input widgets.
- Optional BM25 tokenizer configuration preserves old behavior when omitted; embedding models retain their internal tokenizers. No business logic was added to package initializers.

Independent review found API batch-size loss and configuration reset on clearing datasets; both were fixed and covered by AppTest. Additional regression fixes cover imported form synchronization, effective default equivalence, stale evaluation invalidation and CSV summary/formula handling.

Actual final commands (Windows, Python 3.12.9; offline tests run outside the socket-restricting sandbox):

```text
uv run pytest
============================ 110 passed in 17.55s =============================

uv run ruff check .
All checks passed!

uv run ruff format --check .
94 files already formatted
```

Round 2 is complete; changes remain in the current working branch without commit or push. Wait for confirmation before the final round. Existing user edits to AGENTS.md are untouched.
