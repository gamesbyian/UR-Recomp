#!/usr/bin/env python3
"""Compose the reference-only result for the historical 2008 Dragster replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smv-meta", type=Path, required=True)
    ap.add_argument("--trace-summary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    smv = json.loads(args.smv_meta.read_text())
    trace = json.loads(args.trace_summary.read_text())
    result = {
        "source_movie": smv.get("path"),
        "sample_count": smv.get("sample_count"),
        "event_runs": smv.get("event_runs"),
        "reset_anchored": smv.get("reset_anchored"),
        "reset_markers": smv.get("reset_markers"),
        "embedded_sram_sha256": smv.get("embedded_sram_sha256"),
        "emitted_sram_size": smv.get("emitted_sram_size"),
        "emitted_sram_sha256": smv.get("emitted_sram_sha256"),
        "first_in_race_frame": trace.get("first_in_race_frame"),
        "first_race_results_frame": trace.get("first_race_results_frame"),
        "reference_reached_race": trace.get("first_in_race_frame") is not None,
        "reference_reached_results": trace.get("first_race_results_frame") is not None,
        "menu_transitions": trace.get("transitions", {}).get("menu", []),
        "in_race_transitions": trace.get("transitions", {}).get("inRace", []),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
