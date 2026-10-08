#!/usr/bin/env python3
"""Check the captured SNES X/tabletop phase transitions without absolute-frame coupling.

The retained Dragster X-vs-jump-only pair has 7E:042F transitions
0->1->2->3->4->0, each two guest frames apart in both native and Snes9x.
This checker deliberately says nothing about completed stunt score/boost.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "analysis/generated/usjo8-x-tabletop-transient.json"
PAIRS = ((0, 1), (1, 2), (2, 3), (3, 4), (4, 0))


class TransientEvidenceError(ValueError):
    """Missing, truncated, malformed or non-equivalent stunt-phase evidence."""


def normalized(events: list[dict], source: str) -> list[dict]:
    if not isinstance(events, list) or len(events) != len(PAIRS):
        raise TransientEvidenceError(f"{source}: need five phase transitions")
    result = []
    base = None
    for i, (row, pair) in enumerate(zip(events, PAIRS)):
        if not isinstance(row, dict):
            raise TransientEvidenceError(f"{source}: transition {i} is not an object")
        frame, old, new = row.get("frame"), row.get("old"), row.get("val")
        if any(type(x) is not int for x in (frame, old, new)):
            raise TransientEvidenceError(f"{source}: noninteger event {i}")
        if (old, new) != pair:
            raise TransientEvidenceError(f"{source}: wrong phase transition {i}: {old}->{new}")
        if base is None:
            base = frame
        elif frame - base != 2 * i:
            raise TransientEvidenceError(f"{source}: input phase is not two guest frames")
        result.append({"relative_frame": frame - base, "old": old, "val": new})
    return result


def verify(evidence: dict, *, native: list[dict] | None = None,
           reference: list[dict] | None = None,
           control: list[dict] | None = None) -> dict:
    if evidence.get("schema_version") != 1 or evidence.get("causal_address") != "7E:042F":
        raise TransientEvidenceError("wrong schema or watched WRAM address")
    if evidence.get("observation", {}).get("absent_in_matched_control") is not True:
        raise TransientEvidenceError("matched jump-only control is not confirmed quiet")
    observation = evidence["observation"]
    inherited = native is None and reference is None and control is None
    if not inherited and (native is None or reference is None or control is None):
        raise TransientEvidenceError("new comparison needs both engines and the matched control")
    if inherited:
        if evidence.get("cross_runtime_checkpoint_parity") is not True:
            raise TransientEvidenceError("retained cross-runtime gate is missing")
        native, reference = observation["native"], observation["reference"]
    elif control:
        raise TransientEvidenceError("matched control changed the target phase field")
    n = normalized(native, "native")
    r = normalized(reference, "reference")
    if n != r:
        raise TransientEvidenceError("native/reference phase transitions disagree")
    if inherited:
        if observation.get("normalized_relative_frames") != [p["relative_frame"] for p in n]:
            raise TransientEvidenceError("retained relative frame summary disagrees")
        if observation.get("transition_values") != [p["val"] for p in n]:
            raise TransientEvidenceError("retained phase value summary disagrees")
    return {
        "status": "PASS",
        "kind": "retained-reference-recheck" if inherited else "new-event-relative-comparison",
        "address": "7E:042F",
        "phase_transitions": n,
        "absolute_frame_alignment_required": False,
        "limitation": "Phase parity only. Landing/boost credit and completed-tabletop semantics are not inferred.",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence", type=Path, default=DEFAULT)
    ap.add_argument("--native-trace", type=Path)
    ap.add_argument("--reference-trace", type=Path)
    ap.add_argument("--control-trace", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)
    paths = [args.native_trace, args.reference_trace, args.control_trace]
    if any(p is not None for p in paths) and not all(p is not None for p in paths):
        ap.error("new observations require --native-trace, --reference-trace, and --control-trace")
    try:
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        samples = None
        if all(p is not None for p in paths):
            samples = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
        report = verify(evidence) if samples is None else verify(
            evidence, native=samples[0], reference=samples[1], control=samples[2]
        )
    except (TransientEvidenceError, OSError, ValueError, KeyError, TypeError) as exc:
        ap.error(str(exc))
    output = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
