#!/usr/bin/env python3
"""Run a manifest of Modern visual diagnostics and emit CI evidence.

Manifest (JSON): {"cases": [{"id": str, "p7": path, "expect_sha256": hex,
  "checks": [{"type": "clip"|"focus"|"contrast"|"compare"|"detect", ...}]}]}
Paths resolve relative to the manifest. Output: aggregate JSON (stdout or
--json) and a Markdown table (--summary, e.g. $GITHUB_STEP_SUMMARY). A case
whose frame is missing, mis-hashed or malformed is `incomplete`, never a
pass; the exit status is 2 unless every check passed. Measurement only: no
human, physical-monitor or original-parity credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from tools import qa_modern_visual_diagnostics as d
except ModuleNotFoundError:
    import qa_modern_visual_diagnostics as d


def _rgb(value: str):
    return d.parse_rgb(value)


def run_check(frame, base: Path, check: dict) -> dict:
    kind = check.get("type")
    mode, par = check.get("mode", "fit"), check.get("par", d.PAR_DEFAULT)
    if kind == "clip":
        return d.clip_audit(frame, *check["logical"],
                            [_rgb(c) for c in check["colours"]],
                            check.get("region", "title"), mode, par)
    if kind == "focus":
        m = d.mapping(*check["logical"], frame.width, frame.height, mode, par)
        scale = check.get("scale", m.sx)
        return d.focus_audit(frame, _rgb(check["marker"]), scale,
                             scale_y=check.get("scale", m.sy))
    if kind == "detect":
        return d.detect_logical(frame, tuple(check.get("widths", (256, 342))),
                                mode=mode, par=par)
    if kind == "contrast":
        return d.local_contrast(frame, tuple(check["roi"]), _rgb(check["foreground"]),
                                check.get("threshold", 4.5))
    if kind == "compare":
        other = d.load(base / check["other"], check.get("other_expect_sha256"))
        return d.compare_resolutions(frame, other, *check["logical"],
                                     check.get("max_diff", 0), mode, par)
    raise ValueError(f"unknown check type {kind!r}")


def run_manifest(manifest: dict, base: Path) -> dict:
    cases = []
    for case in manifest.get("cases", []):
        entry = {"id": case.get("id"), "status": "pass", "checks": []}
        try:
            frame = d.load(base / case["p7"], case.get("expect_sha256"))
            for check in case["checks"]:
                res = run_check(frame, base, check)
                entry["checks"].append({"type": check["type"], "pass": res["pass"],
                                        "report": res})
                if not res["pass"]:
                    entry["status"] = "fail"
        except (OSError, ValueError, KeyError, TypeError) as exc:
            entry["status"] = "incomplete"
            entry["error"] = f"{type(exc).__name__}: {exc}"
        cases.append(entry)
    ids = [c["id"] for c in cases]
    if not cases or len(set(ids)) != len(ids) or None in ids:
        status = "incomplete"
    elif any(c["status"] == "incomplete" for c in cases):
        status = "incomplete"
    else:
        status = "fail" if any(c["status"] == "fail" for c in cases) else "pass"
    return {"schema": "ur-modern-visual-report-v1", "status": status, "cases": cases,
            "human_visual_approved": False, "physical_monitor_approved": False,
            "original_guest_equivalence_approved": False, "release_gate_credit": 0}


def markdown(report: dict) -> str:
    lines = [f"### Modern visual diagnostics: **{report['status']}**", "",
             "| case | status | checks |", "|---|---|---|"]
    for case in report["cases"]:
        detail = ", ".join(f"{c['type']}={'ok' if c['pass'] else 'FAIL'}"
                           for c in case["checks"]) or case.get("error", "")
        lines.append(f"| {case['id']} | {case['status']} | {detail} |")
    lines += ["", "_Source-RGB measurement only; no human, physical or parity approval._"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument("--json", type=Path)
    p.add_argument("--summary", type=Path)
    a = p.parse_args(argv)
    try:
        manifest = json.loads(a.manifest.read_text())
    except (OSError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    report = run_manifest(manifest, a.manifest.resolve().parent)
    text = json.dumps(report, indent=2)
    if a.json:
        a.json.write_text(text + "\n")
    else:
        print(text)
    if a.summary:
        with a.summary.open("a") as handle:
            handle.write(markdown(report))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
