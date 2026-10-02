#!/usr/bin/env python3
"""Summarize the bounded Dragster gameplay-object liveness fixture.

This intentionally reports raw evidence surfaces rather than equating any one
presentation structure with gameplay activation.  The first semantic event is
derived from the already-proven checkpoint/finish progress fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def u16(blob: bytes, addr: int) -> int:
    return int.from_bytes(blob[addr:addr + 2], "little")


def frame_info(dump_dir: Path, stem: str) -> dict:
    return json.loads((dump_dir / f"{stem}.info.json").read_text())


def raw_fb_stats(path: Path, previous: bytes | None) -> tuple[str, int | None]:
    blob = path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if previous is None or len(previous) != len(blob):
        return digest, None
    changed = sum(
        1
        for i in range(0, len(blob), 4)
        if blob[i:i + 4] != previous[i:i + 4]
    )
    return digest, changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump_dir", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    stems = sorted(
        p.name.removesuffix(".wram.bin")
        for p in args.dump_dir.glob("liveness-*.wram.bin")
    )
    if not stems:
        raise SystemExit("no liveness-*.wram.bin dumps found")

    rows = []
    previous_fb = None
    baseline_progress = None
    first_progress_change = None

    for stem in stems:
        wram = (args.dump_dir / f"{stem}.wram.bin").read_bytes()
        info = frame_info(args.dump_dir, stem)
        fb_path = args.dump_dir / f"{stem}.fb.bgrx"
        fb_hash = None
        changed_pixels = None
        if fb_path.is_file():
            fb_hash, changed_pixels = raw_fb_stats(fb_path, previous_fb)
            previous_fb = fb_path.read_bytes()

        progress = {
            "next_checkpoint": u16(wram, 0x1199),
            "finish_gate": u16(wram, 0x119D),
            "laps_remaining": u16(wram, 0x0EF1),
        }
        if baseline_progress is None:
            baseline_progress = progress.copy()
        changed_progress = progress != baseline_progress
        if changed_progress and first_progress_change is None:
            first_progress_change = {
                "stem": stem,
                "frame": int(info["frame"]),
                "progress": progress.copy(),
            }

        row = {
            "stem": stem,
            "frame": int(info["frame"]),
            "player": {
                "x": u16(wram, 0x0411),
                "y": u16(wram, 0x0415),
                "collision_word_persistent": u16(wram, 0x0E95),
            },
            "camera": {
                "x": u16(wram, 0x0419),
                "y": u16(wram, 0x041D),
                "edge_x": u16(wram, 0x0505),
                "edge_y": u16(wram, 0x050D),
            },
            "presentation": {
                "vram_list_count_1": u16(wram, 0x0DCD),
                "vram_list_count_2": u16(wram, 0x0DCF),
                "visibility_bits": u16(wram, 0x1599),
                "framebuffer_sha256": fb_hash,
                "changed_pixels_from_previous_dump": changed_pixels,
            },
            "progress": progress,
            "progress_changed_from_start": changed_progress,
            "object_map_prefix_hex": wram[0xC000:0xC014].hex(),
        }
        rows.append(row)

    report = {
        "fixture": "object-liveness-dragster",
        "sample_count": len(rows),
        "baseline_progress": baseline_progress,
        "first_progress_change": first_progress_change,
        "object_map_prefix_stable": len({r["object_map_prefix_hex"] for r in rows}) == 1,
        "rows": rows,
        "interpretation_guardrail": (
            "0x0DCD/0x0DCF are reported as presentation-side VRAM update-list "
            "counts only; they are not treated as gameplay activation state."
        ),
    }

    print(
        "samples=", report["sample_count"],
        "first_progress_change=", report["first_progress_change"],
        "object_map_prefix_stable=", report["object_map_prefix_stable"],
    )
    for r in rows:
        marker = "*" if r["progress_changed_from_start"] else " "
        print(
            f'{marker} {r["stem"]} f={r["frame"]} '
            f'x={r["player"]["x"]} camx={r["camera"]["x"]} '
            f'coll=0x{r["player"]["collision_word_persistent"]:04X} '
            f'dcd={r["presentation"]["vram_list_count_1"]} '
            f'dcf={r["presentation"]["vram_list_count_2"]} '
            f'cp={r["progress"]["next_checkpoint"]} '
            f'gate={r["progress"]["finish_gate"]} '
            f'laps={r["progress"]["laps_remaining"]} '
            f'pixdelta={r["presentation"]["changed_pixels_from_previous_dump"]}'
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
