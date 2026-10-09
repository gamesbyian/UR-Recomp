#!/usr/bin/env python3
"""Find a *reference-only*, frame-grounded Zoom Zoo archive scene anchor.

Retained original 2014 Snes9x checkpoints include a second race entry and
later confirmed track ID 1. Earlier failed absolute native replay is retained
as evidence of startup phase drift, not interpreted as a physics bug.
No original movie bytes, ROM, SRAM or native state modifications.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "analysis/generated/historical-2014-first-race-reference.json"
REPLAY = ROOT / "analysis/generated/historical-2014-first-race-replay.json"
METADATA = ROOT / "analysis/generated/historical-2014-smv-metadata.json"


class SceneAnchorError(ValueError):
    pass


def build(meta: dict, reference: dict, replay: dict) -> dict:
    if (meta.get("uid") != 1396370047
            or meta.get("version") != 4
            or meta.get("controller_mask") != 1
            or not meta.get("reset_anchored")
            or meta.get("pal") is not False
            or meta.get("rom_info", {}).get("crc32") != "383858c7"):
        raise SceneAnchorError("archived Snes9x original movie identity is not pinned")
    source = meta["path"]
    if reference.get("source_movie") != source or replay.get("source_movie") != source:
        raise SceneAnchorError("historical reference/replay source differs from movie")
    if reference.get("first_in_race_frame") != 794 or reference.get("first_race_results_frame") != 2874:
        raise SceneAnchorError("first reference race/results provenance has changed")
    if reference.get("in_race_transitions") is None:
        raise SceneAnchorError("missing reference-only race transitions")
    entries = [
        row["frame"] for row in reference["in_race_transitions"]
        if row.get("old") == 0 and row.get("val") == 1
    ]
    if entries[:2] != [794, 3190]:
        raise SceneAnchorError("first/second original race entries not independently observed")
    rows = [
        item for item in replay.get("sampled_mismatches", [])
        if item.get("frame") in (3400, 3800, 4200, 4600, 5000)
    ]
    if len(rows) != 5 or [r["frame"] for r in rows] != [3400, 3800, 4200, 4600, 5000]:
        raise SceneAnchorError("incomplete original second-race checkpoint set")
    for row in rows:
        ref = row["reference"]
        if not isinstance(ref, list) or len(ref) != 9 or ref[1:3] != [1, 1]:
            raise SceneAnchorError("later original checkpoints do not identify active Zoom Zoo track")
    native_at_3400 = rows[0]["native"]
    if not isinstance(native_at_3400, list) or len(native_at_3400) != 9:
        raise SceneAnchorError("missing prior absolute native checkpoint provenance")
    return {
        "schema_version": 1,
        "source_movie": source,
        "source_uid": meta["uid"],
        "source_sample_count": meta["sample_count"],
        "reference_only": {
            "first_race_entry": 794,
            "first_race_results": 2874,
            "second_race_entry_candidate": 3190,
            "source": "analysis/generated/historical-2014-first-race-reference.json",
            "subsequent_track_verified_at_frames": [r["frame"] for r in rows],
            "verified_track_id": 1,
            "course_id": "course:02",
            "course_name": "Zoom Zoo",
        },
        "prior_absolute_native_alignment": {
            "same_movie_frame_3400_reference_in_race_track": rows[0]["reference"][1:3],
            "same_movie_frame_3400_native_in_race_track": native_at_3400[1:3],
            "valid_for_guest_physics_parity": False,
        },
        "next_discriminator": (
            "Original Snes9x 2014 movie window may be bounded from frame 3190 "
            "for Zoo first 1810 frames through measured frame 5000. Replay its "
            "controller samples after fresh stock Zoom Zoo entry on each core. "
            "Keep relative controller phase +/-1 speculative until captured."
        ),
        "scope": (
            "Original-only scene and course identification. Native absolute "
            "frame divergence is inherited startup phase, not gameplay proof. "
            "No complete race or parity witnessed by this report."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--meta", type=Path, default=METADATA)
    p.add_argument("--reference", type=Path, default=REFERENCE)
    p.add_argument("--replay", type=Path, default=REPLAY)
    p.add_argument("--json-out", type=Path)
    a = p.parse_args()
    result = build(*(json.loads(path.read_text(encoding="utf-8")) for path in
                     (a.meta, a.reference, a.replay)))
    rendered = json.dumps(result, indent=2) + "\n"
    if a.json_out is None:
        print(rendered, end="")
    else:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
