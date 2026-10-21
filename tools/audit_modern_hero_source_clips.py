#!/usr/bin/env python3
"""Inventory original-guest racer clip *candidates* for Modern hero acting.

This is a ROM-free source-registration gate, not a raster extractor, animation
player or art approval. It never asserts that two registered representations
rasterize identically or that a contiguous race excerpt can safely loop.
Original pixels and gameplay clocks remain exclusively with their owners.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "analysis/data/racer-hd-replacement-prototype.json"
SOURCE = ROOT / "analysis/generated/racer-presentation-family.json"
CANONICAL_USA_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"

# Every clip is an exact observed guest frame window, never a synthesized
# alternate order. The additional hold/recovery excerpts are deliberately
# separate from #2042's current 1213..1220 optional native experiment.
CANDIDATES = (
    ("root-entry-reaction", "motion_review_sequence", None, 1213, 1220),
    ("settle-and-recover", "motion_review_sequences",
     "ordinary-race-1230-1239-entry-hold-exit", 1230, 1239),
    ("long-hold-recovery", "motion_review_sequences",
     "ordinary-race-1244-1252-hold-recovery", 1244, 1252),
)


class ClipAdmissionError(ValueError):
    """A proposed source-registered sequence cannot be described faithfully."""


def _hex(value: Any, field: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ClipAdmissionError(f"{field}: expected registered 0x-hex ID")
    try:
        number = int(value, 16)
    except ValueError as exc:
        raise ClipAdmissionError(f"{field}: invalid registered hex") from exc
    if number <= 0 or number > 65535:
        raise ClipAdmissionError(f"{field}: invalid source ID")
    return number


def _runs(ids: list[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, item in enumerate(ids):
        if result and result[-1]["representation_id"] == item:
            result[-1]["host_frames"] += 1
        else:
            result.append({"first_clip_tick": index, "host_frames": 1,
                           "representation_id": item})
    return result


def inspect_clip(registry: dict, source: dict, specification: tuple) -> dict:
    name, section, key, first, last = specification
    if source.get("rom_sha256") != CANONICAL_USA_SHA256:
        raise ClipAdmissionError("source corpus is not canonical USA retail")
    if registry.get("schema_version") != 1:
        raise ClipAdmissionError("unsupported racer registration schema")
    timeline = registry.get(section)
    timeline = timeline.get(key) if key is not None and isinstance(timeline, dict) else timeline
    if not isinstance(timeline, dict) or not timeline.get("status", "").startswith("accepted "):
        raise ClipAdmissionError(f"{name}: source sequence is not an accepted registered window")
    if timeline.get("window_start", first + 1) > first or timeline.get("window_end", last - 1) < last:
        raise ClipAdmissionError(f"{name}: requested span exceeds observed source window")
    if not isinstance(timeline.get("frames"), list):
        raise ClipAdmissionError(f"{name}: missing original frame census")
    rows = [r for r in timeline["frames"]
            if isinstance(r, dict) and isinstance(r.get("frame"), int)
            and first <= r["frame"] <= last]
    if [r["frame"] for r in rows] != list(range(first, last + 1)):
        raise ClipAdmissionError(f"{name}: missing, duplicated or reordered guest frames")

    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise ClipAdmissionError("missing original composition register")
    lookup: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("representation_id"), str):
            raise ClipAdmissionError("malformed composition register")
        identifier = entry["representation_id"]
        if identifier in lookup:
            raise ClipAdmissionError("ambiguous source representation ID")
        lookup[identifier] = entry

    source_steps = []
    representations = []
    for row in rows:
        rid = row.get("p1_representation_id")
        entry = lookup.get(rid)
        if entry is None or entry.get("player") != "p1":
            raise ClipAdmissionError(f"{name}: source P1 raster family missing")
        if entry.get("palette_asset_id") != "0x06":
            raise ClipAdmissionError(f"{name}: original P1 palette registration changed")
        semantic = _hex(entry.get("semantic_frame_id"), "semantic_frame_id")
        guard = entry.get("composition_guards", {})
        if not isinstance(guard, dict) or _hex(guard.get("p1_primary"), "p1_primary") != semantic:
            raise ClipAdmissionError(f"{name}: registered P1 composition guard disagrees")
        # The P1 primary semantic alone does not identify companion sprites.
        # Record the entire registered representation, including context.
        source_steps.append({"original_guest_frame": row["frame"],
                             "presentation_tick": row["frame"] - first,
                             "p1_semantic_id": f"0x{semantic:04X}",
                             "representation_id": rid})
        representations.append(rid)

    return {
        "clip_id": name,
        "source_key": key or section,
        "source_guest_frames": [first, last],
        "ticks_at_source_60hz": last - first + 1,
        "source_registration_status": timeline["status"],
        "source_observed_original_p1": source_steps,
        "registered_composition_holds": _runs(representations),
        "distinct_registered_compositions": len(set(representations)),
        "may_reverse_or_loop": False,
        "reason_no_loop": "Adjacent original race-frame registration does not prove a cyclic menu idle transition",
        "raster_bytes_verified_here": False,
        "source_sprite_cadence_certified_in_native": False,
        "native_visual_approval": "pending",
    }


def build_report(registry: dict, source: dict) -> dict:
    clips = [inspect_clip(registry, source, s) for s in CANDIDATES]
    return {
        "schema_version": 1,
        "purpose": "Modern native menu original-racer reaction/hold source inventory",
        "canonical_rom_sha256": CANONICAL_USA_SHA256,
        "registry": REGISTRY.relative_to(ROOT).as_posix(),
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "clock": "observed original guest 60Hz; not the host menu UI clock",
        "admission": "registered timing candidates only; no new art, guest writes, or shipping hero",
        "next": "Rerasterize exact source P1/companion/CGAM composition under a private verified ROM, then check actual native 4:3/16:9 source-frame and final SDL captures with independent aesthetic approval.",
        "clips": clips,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path,
                        help="Optional JSON receipt location; stdout otherwise")
    args = parser.parse_args()
    result = build_report(json.loads(args.registry.read_text(encoding="utf-8")),
                          json.loads(args.source.read_text(encoding="utf-8")))
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
