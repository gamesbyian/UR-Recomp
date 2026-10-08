#!/usr/bin/env python3
"""Summarize the bounded Dragster object-activation / presentation probe.

This intentionally stays narrow: it follows the already-proven Dragster finish
route and reports only the checkpoint/finish behavior plane, player/camera
state, camera-filtered VRAM-update activity, and a conservative checkerboard
visibility discriminator.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TAIL_RE = re.compile(r"object-tail-(\d{3})$")


def u16(blob: bytes, addr: int) -> int:
    return blob[addr] | (blob[addr + 1] << 8)


def object_index(collision_word: int) -> int:
    return ((collision_word & 0x03F0) >> 2) + ((collision_word & 0x000F) >> 1)


def checker_score(raw: bytes, width: int, height: int) -> int:
    """Return longest conservative black/white alternating run in lower screen.

    Dragster's start/finish stripe is a dense sequence of near-black and
    near-white rectangular runs. Requiring >=8 alternating runs rejects the
    ordinary colored rail and HUD text in the established fixture.
    """

    best = 0
    for y in range(height // 2, height):
        classes: list[int] = []
        row = y * width * 4
        for x in range(width):
            b, g, r, _ = raw[row + x * 4 : row + x * 4 + 4]
            if max(r, g, b) < 40:
                classes.append(0)
            elif min(r, g, b) > 210:
                classes.append(1)
            else:
                classes.append(-1)

        runs: list[tuple[int, int, int, int]] = []
        start = 0
        for x in range(1, width + 1):
            if x == width or classes[x] != classes[start]:
                if classes[start] in (0, 1):
                    runs.append((classes[start], start, x, x - start))
                start = x

        for i, run in enumerate(runs):
            if not 3 <= run[3] <= 14:
                continue
            count = 1
            previous = run
            for current in runs[i + 1 :]:
                if (
                    current[1] != previous[2]
                    or current[0] == previous[0]
                    or not 3 <= current[3] <= 14
                ):
                    break
                count += 1
                previous = current
            best = max(best, count)
    return best


def finish_edge_checker_pixels(raw: bytes, width: int, height: int) -> int:
    """Count black/white finish-stripe pixels at the entering right edge.

    This is intentionally fixture-specific. On the deterministic Dragster tail,
    the ordinary dark rail contributes at most four classified pixels in this
    small window before the finish stripe arrives. The first finish pixels enter
    at the right edge and raise the count sharply (52 pixels in the first
    positive sample). A >=16 threshold therefore detects actual framebuffer
    ingress without conflating racer/trail blue pixels with the finish posts.
    """

    count = 0
    x0 = max(0, width - 4)
    y0 = min(145, height)
    y1 = min(165, height)
    for y in range(y0, y1):
        row = y * width * 4
        for x in range(x0, width):
            b, g, r, _ = raw[row + x * 4 : row + x * 4 + 4]
            if max(r, g, b) < 40 or min(r, g, b) > 210:
                count += 1
    return count


def ppu_counts(path: Path) -> dict[str, int]:
    counts = {"2116": 0, "2118": 0, "2119": 0, "2104": 0}
    if not path.is_file():
        return counts
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) >= 4 and fields[2].upper() in counts:
            counts[fields[2].upper()] += 1
    return counts


def dma_to_vram(path: Path) -> tuple[int, int]:
    """Return transfer count/bytes for DMA rows targeting PPU register $2118."""

    transfers = 0
    total = 0
    if not path.is_file():
        return transfers, total
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 9:
            continue
        # Header: frame line phase channel dir source breg dest size
        breg = fields[6].upper().removeprefix("0X").removeprefix("$")
        if breg not in {"18", "2118"}:
            continue
        transfers += 1
        try:
            total += int(fields[8], 0)
        except ValueError:
            try:
                total += int(fields[8], 16)
            except ValueError:
                pass
    return transfers, total


def prior_postframe_dispatch_candidate(rows: list[dict], progress: dict | None) -> dict | None:
    """Candidate dispatch input; NOT a captured instruction-time read.

    The USA race loop dispatches objects before sampling new surface contact.
    A consecutive prior end-of-frame stored P1 word can therefore be the
    subsequent frame's dispatcher input, absent intervening writes.
    """
    if progress is None:
        return None
    # Only a row from this exact captured sequence can carry the phase
    # inference. A reconstructed lookalike could belong to another run.
    matches = [pos for pos, row in enumerate(rows) if row is progress]
    if len(matches) != 1 or matches[0] == 0:
        return None
    current = rows[matches[0]]
    prior = rows[matches[0] - 1]
    if (
        prior["frame"] + 1 != current["frame"]
        or prior["relative_frame"] + 1 != current["relative_frame"]
    ):
        return None
    return {
        "observation_phase": "prior_postframe_stored_p1_word_dispatch_candidate",
        "source_frame": prior["frame"],
        "transition_frame": current["frame"],
        "collision_word": prior["collision_word"],
        "object_index": prior["object_index"],
        "object_code": prior["object_code"],
        "status": "candidate_only_not_instruction_time_verified",
        "caveat": (
            "Original object dispatch precedes new surface sampling, but "
            "this prior saved word has not been directly captured at handler "
            "entry and may have been changed by an intervening write."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump_dir", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    rows = []
    for info_path in sorted(args.dump_dir.glob("object-tail-*.info.json")):
        match = TAIL_RE.match(info_path.stem.removesuffix(".info"))
        if not match:
            continue
        name = info_path.name.removesuffix(".info.json")
        wram_path = args.dump_dir / f"{name}.wram.bin"
        fb_path = args.dump_dir / f"{name}.fb.bgrx"
        if not wram_path.is_file() or not fb_path.is_file():
            continue

        info = json.loads(info_path.read_text(encoding="utf-8"))
        wram = wram_path.read_bytes()
        fb = fb_path.read_bytes()
        collision = u16(wram, 0x0E95)
        idx = object_index(collision)
        ppu = ppu_counts(args.dump_dir / f"{name}.ppuw.tsv")
        dma_count, dma_bytes = dma_to_vram(args.dump_dir / f"{name}.dma.tsv")
        score = checker_score(fb, int(info["fb_width"]), int(info["fb_height"]))
        edge_pixels = finish_edge_checker_pixels(fb, int(info["fb_width"]), int(info["fb_height"]))
        row = {
            "sample": name,
            "relative_frame": int(match.group(1)),
            "frame": int(info["frame"]),
            "menu": wram[0x009F],
            "in_race": wram[0x0313],
            "player_x": u16(wram, 0x0411),
            "player_y": u16(wram, 0x0415),
            "camera_x": u16(wram, 0x0419),
            "camera_y": u16(wram, 0x041D),
            "camera_dx": u16(wram, 0x04F5),
            "camera_edge_x": u16(wram, 0x0505),
            "camera_edge_y": u16(wram, 0x050D),
            "collision_word": collision,
            "collision_observation_phase": "postframe_stored_p1_contact",
            "object_index": idx,
            "object_code": wram[0xC000 + idx] if 0 <= idx < 0x2000 else None,
            "checkpoint": u16(wram, 0x1199),
            "finish_gate": u16(wram, 0x119D),
            "laps_remaining": u16(wram, 0x0EF1),
            "update_count_1": u16(wram, 0x0DCD),
            "update_count_2": u16(wram, 0x0DCF),
            "ppu_2116_writes": ppu["2116"],
            "ppu_2118_writes": ppu["2118"],
            "ppu_2119_writes": ppu["2119"],
            "oam_2104_writes": ppu["2104"],
            "dma_to_2118_transfers": dma_count,
            "dma_to_2118_bytes": dma_bytes,
            "checker_score": score,
            "checker_visible": score >= 8,
            "finish_edge_checker_pixels": edge_pixels,
            "finish_edge_visible": edge_pixels >= 16,
            "checkpoint_cells": list(wram[0xC006:0xC00F]),
        }
        rows.append(row)

    if not rows:
        raise SystemExit("no object-tail samples found")

    base = rows[0]
    first_progress = next(
        (
            r
            for r in rows[1:]
            if (r["checkpoint"], r["finish_gate"], r["laps_remaining"])
            != (base["checkpoint"], base["finish_gate"], base["laps_remaining"])
        ),
        None,
    )
    first_direct_vram = next((r for r in rows if r["ppu_2118_writes"] > 0), None)
    visible = [r for r in rows if r["checker_visible"]]
    edge_visible = [r for r in rows if r["finish_edge_visible"]]

    report = {
        "fixture": "Dragster deterministic finish tail",
        "sample_relative_frames": [r["relative_frame"] for r in rows],
        "checkpoint_cells_expected": [0x14] * 9,
        "checkpoint_cells_stable": all(r["checkpoint_cells"] == [0x14] * 9 for r in rows),
        "first_progress_change": first_progress,
        "first_progress_dispatch_input_candidate": prior_postframe_dispatch_candidate(rows, first_progress),
        "course_dispatch_phase_caveat": (
            "Object dispatch runs before later contact/surface resampling "
            "on the USA main race path. The P1 collision word in each row "
            "is an end-of-frame observation, not proof of same-frame "
            "checkpoint handler input or a causally active C000 slot."
        ),
        "first_sample_with_direct_2118_write": first_direct_vram,
        "first_checker_visible": visible[0] if visible else None,
        "last_checker_visible": visible[-1] if visible else None,
        "first_finish_edge_visible": edge_visible[0] if edge_visible else None,
        "last_finish_edge_visible": edge_visible[-1] if edge_visible else None,
        "samples": rows,
    }

    lines = [
        "# Dragster object activation / presentation probe",
        "",
        "This artifact is a bounded observation over the established deterministic finish route.",
        "P1 C000 slot/code fields are **postframe** samples, not proven causes of the same-frame progress state.",
        "",
        f"- samples: **{len(rows)}** across targeted windows",
        f"- checkpoint behavior cells C000[6..14] stable as nine `0x14` bytes: **{report['checkpoint_cells_stable']}**",
        f"- first sampled semantic progress change: **{first_progress['sample'] if first_progress else 'none'}**",
        f"- preceding frame stored-contact candidate (not handler-entry proof): **{report['first_progress_dispatch_input_candidate']['object_index'] if report['first_progress_dispatch_input_candidate'] else 'unavailable'}**",
        f"- first sampled direct `$2118` write: **{first_direct_vram['sample'] if first_direct_vram else 'none'}**",
        f"- checkerboard-visible samples (conservative discriminator): **{len(visible)}**",
        f"- right-edge finish-stripe-visible samples: **{len(edge_visible)}**",
        "",
        "| sample | frame | P1 x | cam x | postframe C000 idx/code | next/gate/laps | CPU 2118 | DMA 2118 | checker | edge px |",
        "|---|---:|---:|---:|---|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        code = "--" if r["object_code"] is None else f"{r['object_code']:02X}"
        lines.append(
            f"| {r['sample']} | {r['frame']} | {r['player_x']} | {r['camera_x']} | "
            f"{r['object_index']}/{code} | "
            f"{r['checkpoint']}/{r['finish_gate']}/{r['laps_remaining']} | "
            f"{r['ppu_2118_writes']} | {r['dma_to_2118_transfers']} | {r['checker_score']} | {r['finish_edge_checker_pixels']} |"
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
