#!/usr/bin/env python3
"""Build a compact, derived context packet for a project work lane."""

from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

def git_text(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"

def matching_blocks(text: str, keywords: list[str], max_blocks: int = 8, max_chars: int = 5000) -> list[str]:
    blocks = re.split(r"\n\s*\n", text)
    lowered = [keyword.lower() for keyword in keywords]
    matches = [block.strip() for block in blocks if any(keyword in block.lower() for keyword in lowered)]
    out: list[str] = []
    used = 0
    for block in matches:
        if used + len(block) > max_chars:
            break
        out.append(block)
        used += len(block)
        if len(out) >= max_blocks:
            break
    return out

def build_context(config: dict[str, Any], lane: str) -> str:
    lane_cfg = config["lanes"][lane]
    authorities = lane_cfg["authorities"]
    keywords = lane_cfg["keywords"]
    lines = [f"# Agent context: {lane}","",f"HEAD: {git_text('rev-parse','--short=12','HEAD')}",f"Branch: {git_text('branch','--show-current')}","","## Canonical authorities"]
    lines.extend(f"- `{path}`" for path in authorities)
    lines += ["","## Recent lane commits","```text"]
    paths = [path for path in authorities if (ROOT / path).exists()]
    lines += [git_text("log","-n","12","--oneline","--",*paths) if paths else "unavailable","```","","## Current extracted state"]
    for path in authorities:
        file_path = ROOT / path
        if not file_path.exists() or file_path.suffix not in {".md",".yml",".yaml"}:
            continue
        blocks = matching_blocks(file_path.read_text(errors="replace"), keywords)
        if blocks:
            lines += ["",f"### {path}"]
            for block in blocks:
                lines += ["",block]
    lines += ["","## Admission rule","","Before opening new investigation work, name the decision changed, downstream gate, cheapest discriminator, success condition, and stop condition. Prefer extending shared structured evidence or a parameterized harness over adding a sibling one-off workflow.",""]
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane")
    parser.add_argument("--config", type=Path, default=ROOT / "analysis/agent-context-lanes.json")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.lane not in config.get("lanes", {}):
        raise SystemExit(f"unknown lane: {args.lane}")
    rendered = build_context(config, args.lane)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
