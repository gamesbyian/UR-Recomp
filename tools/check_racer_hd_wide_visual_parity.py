#!/usr/bin/env python3
"""Compare native-wide stock/HD-fallback screenshots at aligned guest states.

A fixed *present* frame number is not a deterministic simulation checkpoint:
an enabled-but-ineligible HD presenter can change host pacing enough that
screen captures from separate processes are a few guest frames apart. Choose
a constant frame offset by the exact authoritative WRAM presentation trace,
then compare entire P6 pictures only at equal traced states. No pixel
differences are waived on a successfully aligned frame.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

from check_ppm import inspect_ppm
from summarize_racer_semantic_trace import parse_trace

STATE_FIELDS = (
    "p1_primary", "p2_primary", "p1_companion", "p2_companion",
    "p1_selector", "p2_selector", "p1_gate", "p2_gate",
)


def load_capture(directory: Path, log_path: Path) -> dict[int, dict]:
    trace = {
        row["frame"]: tuple(row[field] for field in STATE_FIELDS)
        for row in parse_trace(log_path.read_text(encoding="utf-8", errors="replace"))
    }
    out: dict[int, dict] = {}
    with (directory / "presents.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            frame = int(row["frame"])
            index = int(row["present"])
            path = directory / f"present_{index:06d}.ppm"
            state = trace.get(frame)
            if state is None:
                continue
            summary = inspect_ppm(path)
            if (summary.width, summary.height) != (342, 224):
                raise ValueError(f"{path}: expected 342x224, got {summary.width}x{summary.height}")
            frame_record = out.setdefault(frame, {"state": state, "sha256": set()})
            if frame_record["state"] != state:
                raise ValueError(f"{directory}: conflicting semantics at frame {frame}")
            frame_record["sha256"].add(summary.sha256)
    if not out:
        raise ValueError(f"{directory}: no screenshots with accompanying semantic trace")
    return out


def compare_series(
    original: dict[int, dict],
    enabled: dict[int, dict],
    *,
    max_offset: int = 10,
    min_matched_frames: int = 8,
) -> dict:
    if not original or not enabled:
        raise ValueError("both capture series must be nonempty")
    scored = []
    for offset in range(-max_offset, max_offset + 1):
        aligned = [
            (frame, frame + offset)
            for frame in sorted(original)
            if frame + offset in enabled
            and original[frame]["state"] == enabled[frame + offset]["state"]
        ]
        scored.append((len(aligned), offset, aligned))
    # The offset is chosen *only* from exact eight-word semantic identity,
    # never by looking for coincidentally equal pictures.
    best_count = max(count for count, _, _ in scored)
    best = [item for item in scored if item[0] == best_count]
    if best_count < min_matched_frames:
        raise ValueError(
            f"only {best_count} semantic-aligned captures; need {min_matched_frames}"
        )
    if len(best) != 1:
        raise ValueError(
            f"ambiguous equal-best guest-frame offsets: {[x[1] for x in best]}"
        )
    _, offset, aligned = best
    matched = []
    mismatched = []
    for original_frame, enabled_frame in aligned:
        original_hashes = original[original_frame]["sha256"]
        enabled_hashes = enabled[enabled_frame]["sha256"]
        pair = {
            "original_frame": original_frame,
            "hd_enabled_frame": enabled_frame,
            "p1_primary": original[original_frame]["state"][0],
            "p2_primary": original[original_frame]["state"][1],
            "p1_companion": original[original_frame]["state"][2],
            "p2_companion": original[original_frame]["state"][3],
        }
        if original_hashes == enabled_hashes:
            matched.append(pair)
        else:
            pair["original_sha256"] = sorted(original_hashes)
            pair["hd_enabled_sha256"] = sorted(enabled_hashes)
            mismatched.append(pair)

    witness = any(
        pair["p1_primary"] == "0x0541"
        and pair["p2_primary"] == "0x0540"
        and pair["p1_companion"] == "0x0D2D"
        for pair in matched
    )
    success = (
        len(matched) >= min_matched_frames
        and not mismatched
        and witness
    )
    return {
        "schema_version": 1,
        "ok": success,
        "selected_guest_frame_offset": offset,
        "semantic_aligned_frames": len(aligned),
        "pixel_exact_matched_frames": len(matched),
        "different_image_frames": len(mismatched),
        "registration_witness_0541_0540_0d2d": witness,
        "pixel_exact_matched": matched,
        "different_images": mismatched,
        "note": (
            "Frame offset is inferred independently from eight-word WRAM "
            "presentation identity. Every aligned pair must have exactly "
            "the same complete 342x224 image hash; no tolerances or crops."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--original-dir", required=True, type=Path)
    ap.add_argument("--original-log", required=True, type=Path)
    ap.add_argument("--hd-dir", required=True, type=Path)
    ap.add_argument("--hd-log", required=True, type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--min-frames", type=int, default=8)
    args = ap.parse_args()
    report = compare_series(
        load_capture(args.original_dir, args.original_log),
        load_capture(args.hd_dir, args.hd_log),
        min_matched_frames=args.min_frames,
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        "UR_RACER_HD_WIDE_PARITY "
        f"{'PASS' if report['ok'] else 'FAIL'} "
        f"offset={report['selected_guest_frame_offset']} "
        f"aligned={report['semantic_aligned_frames']} "
        f"pixel_exact={report['pixel_exact_matched_frames']} "
        f"mismatched={report['different_image_frames']} "
        f"witness={int(report['registration_witness_0541_0540_0d2d'])}"
    )
    if not report["ok"]:
        for item in report["different_images"][:8]:
            print("MISMATCH " + json.dumps(item, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
