#!/usr/bin/env python3
"""Classify matched stock/+8 VS Widescreen evidence.

The analyzer consumes paired-player summaries produced by
tools/summarize_paired_player_slots.py. It treats racer state, race progress,
and camera/view state as protected. VRAM update-list differences are reported
as presentation evidence but do not themselves fail the semantic gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PROTECTED_SECTIONS = ("slot1", "slot2", "race_progress", "camera_and_viewport")


def analyze(control: dict, widened: dict) -> dict:
    if list(control) != list(widened):
        raise ValueError(f"checkpoint mismatch: {list(control)} != {list(widened)}")

    rows = []
    accepted = True
    for checkpoint in control:
        a = control[checkpoint]
        b = widened[checkpoint]
        protected_differences = {}
        for section in PROTECTED_SECTIONS:
            if a[section] != b[section]:
                protected_differences[section] = {
                    "control": a[section],
                    "plus8": b[section],
                }
        presentation_differences = {}
        if a["vram_update_lists"] != b["vram_update_lists"]:
            presentation_differences["vram_update_lists"] = {
                "control": a["vram_update_lists"],
                "plus8": b["vram_update_lists"],
            }
        row_ok = not protected_differences
        accepted = accepted and row_ok
        rows.append(
            {
                "checkpoint": checkpoint,
                "protected_equal": row_ok,
                "protected_differences": protected_differences,
                "presentation_differences": presentation_differences,
            }
        )

    return {
        "schema_version": 1,
        "fixture": "vs-first-race",
        "control_margin_pixels_per_side": 0,
        "candidate_margin_pixels_per_side": 8,
        "protected_sections": list(PROTECTED_SECTIONS),
        "rows": rows,
        "semantic_activation_preserved": accepted,
        "classification": "ordinary-2p-mixed-compatible" if accepted else "distinct-vs-exception-required",
        "accepted": accepted,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("control_json", type=Path)
    ap.add_argument("widened_json", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    report = analyze(
        json.loads(args.control_json.read_text(encoding="utf-8")),
        json.loads(args.widened_json.read_text(encoding="utf-8")),
    )
    payload = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if not report["accepted"]:
        raise SystemExit("VS +8 protected state diverged from stock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
