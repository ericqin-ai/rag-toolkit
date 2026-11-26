"""Verify README Python examples, local documentation links and original SVG assets."""

import ast
import json
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def main():
    example = (ROOT / "examples/readme_sdk.py").read_text(encoding="utf-8-sig")
    expected = ast.dump(ast.parse(example))
    for name in ["README.md", "README.zh-CN.md"]:
        text = (ROOT / name).read_text(encoding="utf-8-sig")
        blocks = re.findall(r"```python\s*\n(.*?)\n```", text, re.S)
        if len(blocks) != 1 or ast.dump(ast.parse(blocks[0])) != expected:
            raise SystemExit(f"{name}: SDK example differs from executable source")
        completed = subprocess.run(
            [sys.executable, "-c", blocks[0]],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        if "Offline Pipeline Sanity Check" not in completed.stdout:
            raise SystemExit(f"{name}: missing offline label")
        print(f"{name}: exact SDK example executed; first result intro")
    checked = 0
    for source in [
        ROOT / "README.md",
        ROOT / "README.zh-CN.md",
        *sorted((ROOT / "docs").glob("*.md")),
    ]:
        text = source.read_text(encoding="utf-8-sig")
        targets = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text)
        targets += re.findall(r'(?:src|srcset)="([^"]+)"', text)
        for target in targets:
            if target.startswith(("http:", "https:", "#", "mailto:")):
                continue
            destination = source.parent / unquote(target.split("#")[0])
            if not destination.exists():
                raise SystemExit(f"Broken link in {source.name}: {target}")
            checked += 1
    assets = sorted((ROOT / "docs/assets").glob("*.svg"))
    for asset in assets:
        name = asset.name
        root = ET.parse(ROOT / "docs/assets" / name).getroot()
        if root.tag != "{http://www.w3.org/2000/svg}svg":
            raise SystemExit(f"Invalid SVG: {name}")
    print(f"{checked} local documentation links verified; {len(assets)} SVG assets parsed")
    captures_root = ROOT / "docs/assets/screenshots"
    manifest = json.loads((captures_root / "manifest.json").read_text(encoding="utf-8"))
    expected_views = {
        (page, layout)
        for page in (
            "Overview",
            "Search",
            "Inspector",
            "Compare",
            "Evaluation",
            "Datasets",
            "Settings",
        )
        for layout in ("desktop", "narrow")
    }
    if not expected_views.issubset({(c["page"], c["layout"]) for c in manifest["captures"]}):
        raise SystemExit("Missing page/layout capture metadata")
    for capture in manifest["captures"]:
        data = (captures_root / capture["file"]).read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            raise SystemExit("Invalid PNG capture")
        width, height = struct.unpack(">II", data[16:24])
        if (width, height) != (capture["width"], capture["height"]) or capture.get("exceptions", 0):
            raise SystemExit("Capture dimensions or exception checks failed")
    print(f"{len(manifest['captures'])} screenshot files verified against capture metadata")


if __name__ == "__main__":
    main()
