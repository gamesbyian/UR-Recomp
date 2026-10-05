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

def matching_json_entries(
    data: Any,
    keywords: list[str],
    max_entries: int = 12,
    max_chars: int = 5000,
    max_entry_chars: int = 1400,
) -> list[str]:
    """Return compact path-qualified JSON fragments that match lane keywords."""
    lowered = [keyword.lower() for keyword in keywords]
    out: list[str] = []
    used = 0

    def matches(value: Any, label: str = "") -> bool:
        haystack = f"{label} {json.dumps(value, sort_keys=True, ensure_ascii=True)}".lower()
        return any(keyword in haystack for keyword in lowered)

    def add(path: str, value: Any) -> bool:
        nonlocal used
        rendered = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        entry = f"{path}: {rendered}"
        if len(entry) > max_entry_chars or used + len(entry) > max_chars:
            return False
        out.append(entry)
        used += len(entry)
        return len(out) >= max_entries

    def walk(value: Any, path: str) -> bool:
        if len(out) >= max_entries or used >= max_chars:
            return True
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if isinstance(child, list):
                    # Lists are containers, not context entries: descend so one
                    # matching member does not pull unrelated siblings into the packet.
                    if walk(child, child_path):
                        return True
                elif isinstance(child, dict):
                    if matches(child, str(key)) and add(child_path, child):
                        return True
                    if len(json.dumps(child, sort_keys=True, ensure_ascii=True)) > max_entry_chars:
                        if walk(child, child_path):
                            return True
                elif matches(child, str(key)):
                    if add(child_path, child):
                        return True
        elif isinstance(value, list):
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]"
                if isinstance(child, (dict, list)):
                    if matches(child) and add(child_path, child):
                        return True
                    if len(json.dumps(child, sort_keys=True, ensure_ascii=True)) > max_entry_chars:
                        if walk(child, child_path):
                            return True
                elif matches(child):
                    if add(child_path, child):
                        return True
        elif matches(value):
            add(path or "$", value)
        return False

    walk(data, "")
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
        if not file_path.exists():
            continue
        if file_path.suffix in {".md",".yml",".yaml"}:
            blocks = matching_blocks(file_path.read_text(errors="replace"), keywords)
            if blocks:
                lines += ["",f"### {path}"]
                for block in blocks:
                    lines += ["",block]
        elif file_path.suffix == ".json":
            try:
                data = json.loads(file_path.read_text(errors="replace"))
            except json.JSONDecodeError:
                continue
            entries = matching_json_entries(data, keywords)
            if entries:
                lines += ["",f"### {path}","","```text",*entries,"```"]
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
