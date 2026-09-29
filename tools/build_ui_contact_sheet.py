#!/usr/bin/env python3
"""Build a self-contained visual contact sheet from ui-atlas.json.

Canonical framebuffer captures are embedded directly. Optional public/manual
visual-reference leads are rendered as links and can create placeholder cards
for states that do not yet have a local framebuffer.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path


def data_uri(path: Path) -> str:
    raw = path.read_bytes()
    return f"data:image/bmp;base64,{base64.b64encode(raw).decode('ascii')}"


def render_references(refs: list[dict]) -> str:
    if not refs:
        return ""
    items = []
    for ref in refs:
        url = html.escape(str(ref.get("url", "")), quote=True)
        kind = html.escape(str(ref.get("kind", "reference")))
        detail = []
        if ref.get("pdf_page") is not None:
            detail.append(f"manual p.{html.escape(str(ref['pdf_page']))}")
        if ref.get("timestamp"):
            detail.append(html.escape(str(ref["timestamp"])))
        if ref.get("variant"):
            detail.append(html.escape(str(ref["variant"])))
        observation = html.escape(str(ref.get("observation", "")))
        suffix = f" ({', '.join(detail)})" if detail else ""
        items.append(
            f'<li><a href="{url}">{kind}</a>{suffix}'
            + (f"<br><span>{observation}</span>" if observation else "")
            + "</li>"
        )
    return '<div class="refs"><h3>Visual references</h3><ul>' + "".join(items) + "</ul></div>"


def card(item: dict, refs: list[dict]) -> str:
    files = item.get("files", {})
    fb = files.get("framebuffer")
    image_html = '<div class="missing">no canonical framebuffer yet</div>'
    if fb:
        path = Path(fb)
        if path.is_file():
            image_html = (
                f'<img src="{data_uri(path)}" alt="{html.escape(str(item.get("tag", "")))}">'
            )
        else:
            image_html = '<div class="missing">framebuffer path missing</div>'

    obs = item.get("observed", {})
    details = [
        ("tag", item.get("tag", "")),
        ("variant", item.get("variant") or ""),
        ("fixture", item.get("source_fixture") or ""),
        ("frame", item.get("frame", "")),
        ("menu", obs.get("current_menu", "")),
        ("selected", obs.get("selected_option", "")),
        ("row", obs.get("menu_row", "")),
        ("col", obs.get("menu_col", "")),
        ("inRace", obs.get("in_race", "")),
        ("status", item.get("status", "")),
    ]
    rows = "".join(
        f"<dt>{html.escape(str(k))}</dt><dd>{html.escape(str(v))}</dd>"
        for k, v in details
        if v != ""
    )
    mismatches = item.get("mismatches", [])
    mismatch_html = ""
    if mismatches:
        mismatch_html = '<ul class="mismatch">' + "".join(
            f"<li>{html.escape(str(m))}</li>" for m in mismatches
        ) + "</ul>"

    state = html.escape(str(item.get("state_id", "UNKNOWN")))
    return f"""
      <article class="card">
        <h2>{state}</h2>
        {image_html}
        <dl>{rows}</dl>
        {mismatch_html}
        {render_references(refs)}
      </article>
    """


def reference_only_card(state: str, refs: list[dict]) -> str:
    item = {
        "state_id": state,
        "tag": "",
        "status": "reference-only",
        "files": {},
        "observed": {},
        "mismatches": [],
    }
    return card(item, refs)


def build_html(report: dict, include_missing: bool, reference_index: dict | None) -> str:
    refs_by_state: dict[str, list[dict]] = {}
    if reference_index:
        for entry in reference_index.get("entries", []):
            refs_by_state.setdefault(entry["state_id"], []).extend(entry.get("references", []))

    items = report.get("captures", [])
    if not include_missing:
        items = [i for i in items if i.get("files", {}).get("framebuffer")]

    items = sorted(
        items,
        key=lambda i: (
            str(i.get("state_id", "")),
            str(i.get("variant") or ""),
            str(i.get("tag", "")),
        ),
    )
    cards = [
        card(item, refs_by_state.get(str(item.get("state_id", "")), []))
        for item in items
    ]

    represented_states = {str(item.get("state_id", "")) for item in items}
    for state in sorted(refs_by_state):
        if state not in represented_states:
            cards.append(reference_only_card(state, refs_by_state[state]))

    summary = report.get("summary", {})
    summary_bits = [
        f"{html.escape(str(k))}: {html.escape(str(v))}"
        for k, v in summary.items()
    ]
    if refs_by_state:
        summary_bits.append(f"reference-only/linked states: {len(refs_by_state)}")
    summary_text = " · ".join(summary_bits)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Uniracers UI Atlas</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin: 0; padding: 20px; font: 14px/1.4 system-ui, sans-serif; background: #111; color: #eee; }}
  header {{ margin-bottom: 20px; }}
  h1 {{ margin: 0 0 6px; font-size: 28px; }}
  .summary {{ color: #aaa; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill,minmax(290px,1fr)); gap: 16px; }}
  .card {{ background: #1b1b1b; border: 1px solid #333; border-radius: 10px; padding: 12px; }}
  .card h2 {{ margin: 0 0 10px; font-size: 18px; overflow-wrap: anywhere; }}
  img {{ width: 100%; height: auto; image-rendering: pixelated; background: #000; border: 1px solid #333; }}
  .missing {{ aspect-ratio: 8/7; display: grid; place-items: center; background: #222; color: #777; border: 1px dashed #555; }}
  dl {{ display: grid; grid-template-columns: max-content 1fr; gap: 2px 10px; margin: 10px 0 0; }}
  dt {{ color: #999; }}
  dd {{ margin: 0; overflow-wrap: anywhere; }}
  .mismatch {{ color: #ffb4b4; padding-left: 20px; }}
  .refs {{ margin-top: 12px; border-top: 1px solid #333; padding-top: 8px; }}
  .refs h3 {{ margin: 0 0 6px; font-size: 14px; }}
  .refs ul {{ margin: 0; padding-left: 18px; }}
  .refs li {{ margin: 0 0 7px; }}
  .refs span {{ color: #aaa; }}
  a {{ color: #9ecbff; }}
</style>
</head>
<body>
<header>
  <h1>Uniracers UI Atlas</h1>
  <div class="summary">{summary_text}</div>
</header>
<main class="grid">
{"".join(cards)}
</main>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", type=Path, required=True)
    ap.add_argument("--reference-index", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--include-missing", action="store_true")
    args = ap.parse_args()

    report = json.loads(args.atlas.read_text())
    references = json.loads(args.reference_index.read_text()) if args.reference_index else None
    output = build_html(report, args.include_missing, references)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
