# Screenshot and demo capture

## What is included

Images in `assets/screenshots/` are actual Chrome viewport screenshots of the
running Streamlit application with bundled MIT sample data, English UI and
`configs/offline.yaml`. They are **Offline Pipeline Sanity Check** captures,
not mockups or evidence of real-model quality. Long pages scroll below the frame.
The capture script checks the page title, visible Streamlit exception panels and
root document width. Native data tables/charts may scroll internally.

| Page | Desktop (1440 × 1000) | Narrow (390 × 844) |
|---|---|---|
| Overview | [PNG](assets/screenshots/overview-desktop.png) | [PNG](assets/screenshots/overview-narrow.png) |
| Search | [PNG](assets/screenshots/search-desktop.png) | [PNG](assets/screenshots/search-narrow.png) |
| Inspector | [PNG](assets/screenshots/inspector-desktop.png) | [PNG](assets/screenshots/inspector-narrow.png) |
| Compare | [PNG](assets/screenshots/compare-desktop.png) | [PNG](assets/screenshots/compare-narrow.png) |
| Evaluation | [PNG](assets/screenshots/evaluation-desktop.png) | [PNG](assets/screenshots/evaluation-narrow.png) |
| Datasets | [PNG](assets/screenshots/datasets-desktop.png) | [PNG](assets/screenshots/datasets-narrow.png) |
| Settings | [PNG](assets/screenshots/settings-desktop.png) | [PNG](assets/screenshots/settings-narrow.png) |

[Capture metadata and layout checks](assets/screenshots/manifest.json).

## Reproduce on Windows (PowerShell)

Run from the repository root. Chrome/Edge and Node.js 22+ must already be installed;
no npm package or browser download is required. The script creates and removes its
own temporary browser profile, uses only the supplied local app URL, and never
captures an existing personal browser session.

```powershell
$env:RAG_TOOLKIT_CONFIG = "$PWD/configs/offline.yaml"
uv run streamlit run src/rag_toolkit/web/app.py --server.address 127.0.0.1 --server.port 8507 --server.headless true
```

In another terminal:

```powershell
$env:RAG_BROWSER = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:RAG_CAPTURE_URL = 'http://127.0.0.1:8507'
node scripts/capture_web.mjs
```

For Edge, set `RAG_BROWSER` to the installed `msedge.exe` path instead. For other
operating systems, set the same environment variables using that shell's syntax.
The capture automation loads the sample, searches `FAISS CPU`, runs Compare and
Evaluation, then navigates every page at both viewport widths. It overwrites only
the documented screenshot/manifest outputs.

## Manual fallback / recording checklist

No GIF recording is included or claimed. If a browser is unavailable, do not
substitute design mockups: keep the reserved screenshot paths above and use a local
browser to follow the same recipe. To record a demo, start the server, open the URL,
use the browser/OS screen recorder, and save the real capture as
`docs/assets/screenshots/demo.webm`. If FFmpeg is installed, a local conversion is:

```sh
ffmpeg -i docs/assets/screenshots/demo.webm -vf "fps=8,scale=960:-1:flags=lanczos" -loop 0 docs/assets/screenshots/demo.gif
```

This optional recording/conversion command is a local follow-up recipe, not a
claim that recording or FFmpeg conversion was performed in this acceptance.
Before publishing, inspect every frame for credentials and personal data.

[Documentation index](index.md)

## Additional real captures

- [Inspector independent-channel Plotly paths](assets/screenshots/inspector-chart-desktop.png)
- [Evaluation Plotly metrics](assets/screenshots/evaluation-chart-desktop.png)

Each ranking channel has its own subplot, so no shared BM25→Dense axis implies
sequential processing. Legend IDs are shortened for readability; full IDs remain
available in hover details and candidate tables.


- [Native Dark Search](assets/screenshots/search-dark-desktop.png)
- [Native Dark Inspector / Plotly](assets/screenshots/inspector-dark-desktop.png)

The final collection contains 18 real frames: 14 page/layout captures, two
scrolled Plotly views and two native Dark views. Native Light/Dark accents are
configured explicitly in `.streamlit/config.toml`; the recorded run verified a
system-theme change from dark text to light text without a CSS override.
After a complete capture, `node scripts/capture_web.mjs --theme-only` refreshes
just the Dark frames while retaining existing page/layout records.
