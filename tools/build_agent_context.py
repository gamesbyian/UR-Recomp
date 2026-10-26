#!/usr/bin/env python3
"""Build a compact, derived context packet for a project work lane."""

from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

if __package__:
    from .release_evidence_brief import briefing as release_briefing
    from .select_three_project_reuse import REGISTER as REUSE_REGISTER, MATRIX as REUSE_MATRIX, read_json as read_reuse_json, context_hint
else:
    from release_evidence_brief import briefing as release_briefing
    from select_three_project_reuse import REGISTER as REUSE_REGISTER, MATRIX as REUSE_MATRIX, read_json as read_reuse_json, context_hint

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
                if isinstance(child, list) and any(isinstance(item, (dict, list)) for item in child):
                    # Keep record lists element-addressed (`key[i]`) so only the
                    # matching records are extracted, not their siblings.
                    if walk(child, child_path):
                        return True
                elif isinstance(child, (dict, list)):
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


# A small bounded view, not a substitute for the release quality ledger.
LANE_RELEASE_GATES: dict[str, tuple[str, ...] | None] = {
    "release-qa": None,
    "widescreen": ("QA-08", "QA-10"),
    "racer-hd": ("QA-08",),
    "modern-product": ("QA-02", "QA-03", "QA-04", "QA-05", "QA-09"),
    "ci": ("QA-04", "QA-10", "QA-12"),
    "baldosa-integration": ("QA-01", "QA-02", "QA-05", "QA-06", "QA-12"),
}


def release_brief_section(lane: str) -> list[str]:
    """Summarize candidate-bound ledger pointers without authenticating evidence."""
    if lane not in LANE_RELEASE_GATES:
        return []
    path = ROOT / "docs/RELEASE-QUALITY-LEDGER.json"
    try:
        raw = path.read_bytes()
        local_head = git_text("rev-parse", "HEAD")
        exact_head = local_head if re.fullmatch(r"[0-9a-f]{40}", local_head) else None
        view = release_briefing(json.loads(raw), source_sha=exact_head)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        return ["", "## Release gate navigation unavailable",
                "", "Read the authoritative docs/RELEASE-QUALITY-LEDGER.json directly.",
                "Read-only briefing error: " + str(exc)[:180]]

    match = ("unknown (HEAD unavailable)" if exact_head is None
             else "match" if view["source_matches_ledger"] else "MISMATCH")
    lines = [
        "", "## Release gate navigation (read-only, not acceptance)", "",
        "Ledger byte SHA256: " + hashlib.sha256(raw).hexdigest(),
        "Nominated candidate source: " + view["ledger_candidate_commit"],
        "Nominated candidate inner ZIP SHA256: " + view["ledger_zip_sha256"],
        "Current checkout HEAD: " + (exact_head or "unavailable"),
        "Source versus nominated candidate: " + match,
        "Ledger statuses: " + str(view["accepted_gate_count"]) + "/12 passed; "
            + str(view["pending_gate_count"]) + " pending. No independent evidence was checked.",
        "Pointers and witness counts never grant release credit.",
    ]
    allowed = LANE_RELEASE_GATES[lane]
    for row in view["gates"]:
        if allowed is not None and row["id"] not in allowed:
            continue
        lines.append(
            "- " + row["id"] + ": " + row["status"] + "/" + row["required_layer"]
            + "; refs=" + str(row["reference_count"])
            + "; registered witnesses=" + str(row["witness_count"])
            + "; blockers=" + (",".join(row["blockers"]) or "none recorded")
            + "; next=" + row["next_action"][:100]
        )
    lines.append("Regenerate after the ledger changes; compare two saved briefings "
                 "with tools/release_evidence_delta.py for diagnostic metadata differences.")
    return lines

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
    lines.extend(release_brief_section(lane))
    lines += ["", context_hint(read_reuse_json(REUSE_REGISTER), read_reuse_json(REUSE_MATRIX), lane)]
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
