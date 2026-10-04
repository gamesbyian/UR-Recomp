#!/usr/bin/env python3
"""Validate any retained VS Widescreen capacity result.

This replaces margin-specific grep snippets with one parameterized contract.
Margins are strip-granular: +16 => depth 1, +24 => depths 1..2, etc.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from tools.evidence_contract import assertion, make_envelope


def expected_depths(margin: int) -> list[int]:
    if margin < 16 or margin % 8:
        raise ValueError("capacity margin must be an 8-pixel multiple >= 16")
    return list(range(1, margin // 8))


def validate_capacity(retained: dict[str, Any], generated: dict[str, Any], log: str) -> dict[str, Any]:
    margin = int(retained["candidate_margin_pixels_per_side"])
    depths = expected_depths(margin)
    checks = []

    expected_geometry = [256 + 2 * margin, 224]
    checks.append(assertion(
        "generated-classification-matches-retained",
        generated.get("capacity_classification") == retained.get("capacity_classification"),
    ))
    checks.append(assertion(
        "protected-state-parity",
        generated.get("protected_state_equal_at_all_checkpoints") is True
        and retained.get("protected_state_equal_at_all_checkpoints") is True,
    ))
    checks.append(assertion(
        "control-geometry",
        list(generated.get("control_frame_geometry", [])) == [256, 224]
        and list(retained.get("control_frame_geometry", [])) == [256, 224],
    ))
    wide_key = next(
        (key for key in generated if key.startswith("plus") and key.endswith("_frame_geometry")),
        None,
    )
    checks.append(assertion(
        "candidate-geometry",
        wide_key is not None
        and list(generated.get(wide_key, [])) == expected_geometry,
        {"expected": expected_geometry, "field": wide_key},
    ))
    checks.append(assertion(
        "retained-depth-set",
        retained.get("host_shadow_depths") == depths,
        {"expected": depths, "actual": retained.get("host_shadow_depths")},
    ))

    player_metrics: dict[str, Any] = {}
    for player in (1, 2):
        vals = re.findall(
            rf"URWS_VS_MATERIALIZER margin={margin} player={player} calibrated=(\d)",
            log,
        )
        expected_events = retained["calibration"][f"player{player}_events"]
        matches = vals.count("1")
        misses = vals.count("0")
        player_metrics[f"player{player}"] = {
            "events": len(vals),
            "matches": matches,
            "misses": misses,
        }
        checks.append(assertion(
            f"player{player}-calibration",
            len(vals) == expected_events
            and matches == retained["calibration"][f"player{player}_matches"]
            and misses == retained["calibration"][f"player{player}_misses"] == 0,
            player_metrics[f"player{player}"],
        ))
        for depth in depths:
            count = len(re.findall(
                rf"URWS_VS_SHADOW_EXT provider=course-runtime margin={margin} player={player} depth={depth}(?:\D|$)",
                log,
            ))
            expected = retained["host_shadow_events_per_depth"][f"player{player}"]
            checks.append(assertion(
                f"player{player}-depth-{depth}",
                count == expected,
                {"observed": count, "expected": expected},
            ))

    checks.append(assertion(
        "guest-descriptor-not-promoted",
        retained.get("guest_descriptor_promotion") is False,
    ))

    return make_envelope(
        evidence_type="widescreen-vs-capacity",
        producer="tools/check_widescreen_capacity_evidence.py",
        subject={"margin_pixels_per_side": margin, "depths": depths},
        inputs={"fixture": retained.get("fixture"), "authority": retained.get("authority")},
        metrics={"players": player_metrics, "expected_geometry": expected_geometry},
        assertions=checks,
        provenance={
            "workflow_run_id": retained.get("workflow_run_id"),
            "workflow_artifact_id": retained.get("workflow_artifact_id"),
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retained", required=True, type=Path)
    parser.add_argument("--generated", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    envelope = validate_capacity(
        json.loads(args.retained.read_text()),
        json.loads(args.generated.read_text()),
        args.log.read_text(errors="replace"),
    )
    rendered = json.dumps(envelope, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0 if envelope["outcome"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
