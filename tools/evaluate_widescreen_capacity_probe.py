#!/usr/bin/env python3
"""Evaluate a fresh parameterized VS Widescreen capacity probe."""

from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from tools.evidence_contract import assertion, make_envelope
    from tools.check_widescreen_capacity_evidence import expected_depths
except ModuleNotFoundError:
    from evidence_contract import assertion, make_envelope
    from check_widescreen_capacity_evidence import expected_depths

def evaluate_probe(generated: dict[str, Any], log: str, margin: int) -> dict[str, Any]:
    depths = expected_depths(margin)
    checks = [
        assertion("protected-state-parity", generated.get("protected_state_equal_at_all_checkpoints") is True),
        assertion("geometry", generated.get("geometry_accepted") is True),
    ]
    players = {}
    for player in (1, 2):
        values = re.findall(rf"URWS_VS_MATERIALIZER margin={margin} player={player} calibrated=(\d)", log)
        events = len(values)
        matches = values.count("1")
        misses = values.count("0")
        players[f"player{player}"] = {"events":events,"matches":matches,"misses":misses}
        checks.append(assertion(
            f"player{player}-calibration",
            events > 0 and matches == events and misses == 0,
            players[f"player{player}"],
        ))
        for depth in depths:
            shadows = len(re.findall(
                rf"URWS_VS_SHADOW_EXT provider=course-runtime margin={margin} player={player} depth={depth}(?:\D|$)",
                log,
            ))
            checks.append(assertion(
                f"player{player}-depth-{depth}",
                shadows == events and events > 0,
                {"observed":shadows,"expected":events},
            ))
    return make_envelope(
        evidence_type="widescreen-vs-capacity-probe",
        producer="tools/evaluate_widescreen_capacity_probe.py",
        subject={"margin_pixels_per_side":margin,"depths":depths},
        inputs={"fixture":generated.get("fixture")},
        metrics={"players":players,"candidate_geometry":generated.get(f"plus{margin}_frame_geometry")},
        assertions=checks,
    )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--margin", required=True, type=int)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    envelope = evaluate_probe(json.loads(args.generated.read_text()), args.log.read_text(errors="replace"), args.margin)
    rendered = json.dumps(envelope, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0 if envelope["outcome"] == "accepted" else 1

if __name__ == "__main__":
    raise SystemExit(main())
