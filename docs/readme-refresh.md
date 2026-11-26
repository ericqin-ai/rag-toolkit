# README brand refresh review

## Scope and implementation plan

Documentation and original brand assets only. No retrieval code, Web behavior,
model interfaces or core architecture changes. Existing AGENTS.md edits are user-owned.
No commit or push is authorized. The documentation SDK example now loads the existing configs/offline.yaml to keep the example compact and formatted.

Six steps: audit sources; define structure and visual rules; create theme assets;
rewrite both READMEs and reuse detailed guides; render desktop/mobile themes;
verify examples, links, assets, Quick Start and repository checks.

## Reference review (2026-11-26)

Read the actual repository README sources, rather than relying on search summaries.
These are observations about presentation, not copied product claims or artwork.

| Reference | Structure and positioning | Visual/product evidence | Onboarding and decision for this project |
|---|---|---|---|
| [Langfuse](https://github.com/langfuse/langfuse/blob/main/README.md) | Product positioning followed by core capabilities and documentation | Wide brand header; feature image and linked demo | Multiple entry points; adopt clear positioning before implementation detail, retain only relevant local entry points |
| [Qdrant](https://github.com/qdrant/qdrant/blob/master/README.md) | Focused vector-search category, then getting started and client libraries | Strong centered identity and consistent logo; no need for a screenshot gallery to explain its API | Short container command and Python connection example; adopt compact executable onboarding and a coherent brand mark |
| [Promptfoo](https://github.com/promptfoo/promptfoo/blob/main/README.md) | Quick Start, capabilities, then supporting reasons and links | Evaluation matrix, terminal animation and report demonstrate comparison output | Initialize, evaluate, view results; show actual experiment evidence and a short SDK loop |
| [RAGFlow](https://github.com/infiniflow/ragflow/blob/main/README.md) | Broad engine positioning, features, architecture and deployment | Product GIFs and architecture image | Detailed prerequisites and deployment; keep architecture understandable, move such detail to existing guides |
| [Dify](https://github.com/langgenius/dify/blob/main/README.md) | Brand cover, product description, Quick Start and feature list | Large cover and feature imagery, multi-language links | Explicit setup prerequisites with advanced docs links; keep bilingual navigation and a small default path |

Do not inherit agent-platform positioning, production-readiness claims, community
metrics, release badges or external brand assets from these references.

## Keep / merge / migrate / delete

| Previous README content | Action | Destination / rationale |
|---|---|---|
| Introduction + Why + Core Features | Merge | One positioning statement, short introduction, four capability rows |
| CI, Python 3.11+, MIT | Keep | Three verified badges; CI points to the existing workflow |
| Seven desktop screenshots, narrow and dark captures | Remove from homepage, reuse guide | [Existing gallery](screenshots.md), all original files and metadata retained |
| Inspector ranking path capture | Promote | One visible real screenshot with offline-provider disclosure |
| Quick Start | Keep | Existing uv sync, SDK and Streamlit commands; link provider setup |
| SDK | Compress | 14-line README block; same AST as executable example |
| Retrieval Strategy Comparison | Migrate | [Architecture](architecture.md#retrieval-strategy-comparison), including diagnosis caveat |
| Sample benchmark numbers and raw report | Reuse detailed guide | [Benchmarks](benchmarks.md); homepage gives status only |
| Configuration and operational limitations | Reuse detailed guides | [Configuration](configuration.md), [known limits](limitations.md) |
| Contribution commands and engineering rules | Reuse detailed guide | [Development](development.md), AGENTS.md unchanged by this task |
| Mermaid overview | Replace homepage rendering | Theme-aware SVG; detailed contracts and Mermaid remain in architecture guide |
| Duplicate captions, disclaimers and headings | Delete repetition | Keep the relevant qualification once beside the screenshot or example |

No detailed configuration/API guide or second screenshot gallery was created.

## Design specification

Native GitHub Markdown holds all editable body content, tables and code. The eleven
sections follow the requested sequence, with the brand header and introduction
preceding Product Preview. English and Chinese have matching assets, commands,
code, capabilities, documentation destinations and roadmap status.

Original mark: three offset diamond layers with a selected-result stroke. This
expresses retrieval processing without implying that BM25 feeds Dense. The flow
illustration explicitly branches Query into independent BM25 and Dense recall,
then rejoins at Fusion, optional Reranker, Results + StageTrace, Inspector/Evaluation.
Recall independence describes semantics, not concurrent execution.

| Token | Value | Role |
|---|---|---|
| Primary | #6366F1 | Main mark, selected node borders |
| Primary dark | #4338CA | Lower layer |
| Secondary | #A5B4FC | Upper layer |
| Success | #10B981 | Reserved for verified status, not decorative claims |
| Dark background | #0F172A | Dark SVG canvas |
| Light background | #F8FAFC | Light SVG canvas |

System typography: Segoe UI/Arial in SVGs, native GitHub body fonts. Banner is 4:1
(1200×300), architecture 680×650, logo 128×128. Generous margins, flat fills,
no gradients, neon, external fonts or synthetic interface pictures. The portrait
architecture favors readable mobile labels over a compressed horizontal diagram.
`picture` uses dark/light media sources and a light img fallback with useful alt text.

## Preview and validation

Local Chromium renders use GitHub-like CSS; these are local documentation previews,
not screenshots of an uploaded GitHub page. The embedded product image is the
unchanged real application capture documented in [screenshots](screenshots.md).
Full README preview PNGs live in assets/previews. See verification results below.

### Rendered deliverables

- [Theme asset board](assets/previews/brand-themes.png)
- [Before / after opening sections](assets/previews/before-after.png)
- [Original English full page](assets/previews/en-before.png)
- English: [light desktop](assets/previews/en-light-desktop.png), [dark desktop](assets/previews/en-dark-desktop.png), [light mobile](assets/previews/en-light-mobile.png), [dark mobile](assets/previews/en-dark-mobile.png)
- 中文：[浅色桌面](assets/previews/zh-light-desktop.png)、[深色桌面](assets/previews/zh-dark-desktop.png)、[浅色移动端](assets/previews/zh-light-mobile.png)、[深色移动端](assets/previews/zh-dark-mobile.png)

The before image uses HEAD's README and original SVG, not a fabricated baseline.
Eight after renders cover 1200px and 390px widths, two languages and two theme
preferences. All three local images loaded in each render; dark/light currentSrc
selected the corresponding SVG; document scrollWidth did not exceed viewport width.
Code blocks and wide tables retain internal scrolling. Real desktop product imagery
scales on mobile; its linked full-resolution original provides readable detail.

### Verification record

- `uv sync --locked`: completed, 107 packages resolved, 56 checked.
- `uv run python examples/readme_sdk.py`: completed using configs/offline.yaml;
  first result is intro, four traces emitted, Offline Pipeline Sanity Check label printed.
- `uv run python scripts/verify_readme.py`: both README Python blocks executed and
  matched the executable source AST; 125 local links (including HTML src/srcset),
  eight SVGs and all eighteen original screenshot files checked.
- Additional local heading-anchor check: three fragment links resolved.
- `uv run ruff check .` and `uv run ruff format --check .`: passed after SDK cleanup.
- `uv run pytest`: 110 tests passed in 9.73s, offline, Windows/Python 3.12.9.
- Exact README Streamlit command launched on 127.0.0.1:8507;
  health endpoint returned HTTP 200, Retrieval Workbench rendered in Chrome,
  no Streamlit exception panels. The verification server was then stopped.
- `git diff --check`: passed.

An initial compact inline configuration failed the existing Ruff Markdown code
formatting check. It was replaced by loading the existing offline config, producing
a 14-line SDK block that passes both formatting and execution. Initial draft link
validation also caught this review document before creation; the final pass includes it.
No real-model benchmark was run or claimed. No GIF was generated.

### Git diff summary and self-review

Before: English 223 lines, Chinese 213 lines. After: English 126 lines, Chinese 123
lines. The four-value product story replaces three repeated introductory sections;
one real product capture replaces the homepage gallery, retained in the existing guide.

Changed: both README files, original logo/banner compatibility copies,
architecture/development/index guides, the documentation example and README verifier.
Added: six theme SVGs, thirteen PNG previews and this audit/migration report.
No src/, tests/, configs/, model interfaces, lockfiles or application behavior changed.
AGENTS.md was already modified before this task and is not part of this delivery.

Self-check by step: (1) all five README sources examined; (2) requested structure,
positioning and colors recorded; (3) original editable assets rendered and visually
inspected; (4) both languages use the same code, assets, links and roadmap;
(5) eight responsive/theme combinations passed local layout checks;
(6) execution, links, assets, tests and formatting checked. No commits or pushes.
