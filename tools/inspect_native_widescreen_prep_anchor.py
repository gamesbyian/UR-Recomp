#!/usr/bin/env python3
"""Inspect generated SNESRecomp C around Uniracers' accepted +8 prep seam."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

TRACE_RE = re.compile(r"cpu_trace_block\(cpu,\s*(0x[0-9A-Fa-f]+)")
TARGETS = {
    0x01A597: "wrapper_call_a59e",
    0x01A59A: "wrapper_call_ab88",
    0x01A59D: "wrapper_return",
    0x01A59E: "prep_helper_entry",
    0x02D2D1: "nmi_post_consume_cleanup",
}

def canon(pc: int) -> int:
    return pc & ~0x800000

def inspect(gen_dir: Path, radius: int = 24) -> dict:
    hits = []
    staging_initializers = []
    for path in sorted(gen_dir.glob("bank*_v2.c")):
        raw_text = path.read_text(encoding="utf-8", errors="replace").replace("\\n", "\n")
        for match in STAGE_INIT_RE.finditer(raw_text):
            staging_initializers.append({"file": path.name, "offset": match.start()})
        lines = raw_text.splitlines()
        for idx, line in enumerate(lines):
            match = TRACE_RE.search(line)
            if not match:
                continue
            raw_pc = int(match.group(1), 16)
            key = canon(raw_pc)
            if key not in TARGETS:
                continue
            lo, hi = max(0, idx-radius), min(len(lines), idx+radius+1)
            hits.append({
                "target": TARGETS[key],
                "raw_pc": raw_pc,
                "canonical_pc": key,
                "file": path.name,
                "line": idx+1,
                "context": [{"line": j+1, "text": lines[j]} for j in range(lo, hi)],
            })
    by_target = {}
    for hit in hits:
        by_target.setdefault(hit["target"], []).append(hit)
    return {
        "schema_version": 1,
        "targets": by_target,
        "target_counts": {name: len(by_target.get(name, [])) for name in TARGETS.values()},
        "staging_initializer_count": len(staging_initializers),
        "staging_initializers": staging_initializers,
        "all_required_found": all(by_target.get(name) for name in TARGETS.values()) and len(staging_initializers) == 1,
    }

def render(report: dict) -> str:
    lines = ["# Native +8 preparation override anchors", ""]
    for name in TARGETS.values():
        lines.append(f"- {name}: **{len(report['targets'].get(name, []))}** emitted block(s)")
    lines.append(f"- prep_helper_staging_initializer: **{report['staging_initializer_count']}** semantic match(es)")
    lines += ["", f"All required anchors found: **{report['all_required_found']}**", ""]
    for name in TARGETS.values():
        for hit in report["targets"].get(name, []):
            lines += [f"## {name} — {hit['file']}:{hit['line']}", "", "```c"]
            lines += [f"{row['line']:>6}: {row['text']}" for row in hit["context"]]
            lines += ["```", ""]
    return "\n".join(lines)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("gen_dir", type=Path)
    ap.add_argument("--radius", type=int, default=24)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()
    report = inspect(args.gen_dir, args.radius)
    md = render(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(md + "\n", encoding="utf-8")
    print(md)
    return 0 if report["all_required_found"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
