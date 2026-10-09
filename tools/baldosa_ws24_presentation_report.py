#!/usr/bin/env python3
"""Conservative visual/guest gate for disposable native +24 split world raster."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

PRESENT = re.compile(
    r"UR_BALDOSA_WS24_PRESENT frame=(\d+) width=(\d+) height=(\d+) "
    r"pitch=(\d+) calibrated=(\d+) saved=(\d+)"
)
PREP = re.compile(
    r"UR_BALDOSA_WS24_PREP frame=(\d+) calibrated=(\d+) "
    r"logical=(\d+)x(\d+) margin=24"
)
NAME = re.compile(r"ur-baldosa-ws24-(\d{6})\.pam")
HEADER = (b"P7\nWIDTH 304\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
          b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
WIDTH, HEIGHT, EXTRA = 304, 224, 24


def edge_differences(raster: bytes, width: int = WIDTH, extra: int = EXTRA) -> dict[str, int]:
    """Require new pixels in each of four split-screen margins.

    This rejects solid black mattes, an ordinary 256-wide image padded at
    its edges, and a single viewport accidentally widening both halves.
    Independent original/frame parity remains a separate release oracle.
    """
    count = {}
    for section, y0, y1 in (("top", 0, 112), ("bottom", 112, 224)):
        for side in ("left", "right"):
            changed = 0
            for y in range(y0, y1):
                row = memoryview(raster)[y * width * 4:(y + 1) * width * 4]
                edge = extra if side == "left" else width - extra - 1
                baseline = row[edge * 4:edge * 4 + 4].tobytes()
                xs = range(extra) if side == "left" else range(width - extra, width)
                for x in xs:
                    if row[x * 4:x * 4 + 4].tobytes() != baseline:
                        changed += 1
            count[f"{section}_{side}"] = changed
    return count



def restore_logical_nearest(raster: bytes, width: int, height: int,
                            density: int) -> tuple[bytes, bool]:
    """Reverse an integer nearest expansion and inspect *every* subpixel.

    Reading a single subpixel could accept a 1x source written to just the
    corner of a 4x output, leaving the rest uninitialized.
    """
    if density == 1:
        return raster, True
    row_bytes = width * density * 4
    out = bytearray(width * height * 4)
    source = memoryview(raster)
    for y in range(height):
        for x in range(width):
            offset = (y * density * width * density + x * density) * 4
            pixel = source[offset:offset + 4].tobytes()
            block = pixel * density
            for sy in range(density):
                at = (y * density + sy) * row_bytes + x * density * 4
                if source[at:at + len(block)] != block:
                    return bytes(out), False
            out[(y * width + x) * 4:(y * width + x + 1) * 4] = pixel
    return bytes(out), True


def assess(base: Path, candidate: Path, log: Path, captures: Path,
           view: str = "ws24", density: int = 1) -> dict:
    if density not in (1, 2, 3, 4):
        raise ValueError("Only 1x-4x integer density is supported")
    if view not in ("ws24", "ws342"):
        raise ValueError("Only witnessed +24 and 342-wide source world modes are supported")
    wide = view == "ws342"
    width = 342 if wide else WIDTH
    extra = 43 if wide else EXTRA
    backing = 48 if wide else 24
    prefix = "ur-baldosa-ws342" if wide else "ur-baldosa-ws24"
    raster_width, raster_height = width * density, HEIGHT * density
    header = (f"P7\\nWIDTH {raster_width}\\nHEIGHT {raster_height}\\n"
              "DEPTH 4\\nMAXVAL 255\\nTUPLTYPE RGB_ALPHA\\nENDHDR\\n").encode()
    present_regex = PRESENT if not wide else re.compile(
        r"UR_BALDOSA_WS342_PRESENT frame=(\d+) width=(\d+) height=(\d+) "
        r"pitch=(\d+) calibrated=(\d+) saved=(\d+)")
    prep_regex = PREP if not wide else re.compile(
        r"UR_BALDOSA_WS342_PREP frame=(\d+) calibrated=(\d+) "
        r"logical=(\d+)x(\d+) backing=48 visible=43")
    filename_regex = NAME if not wide else re.compile(
        r"ur-baldosa-ws342-(\\d{6})\\.pam")
    if density != 1:
        # A 1x native log cannot establish a real scaled host allocation.
        present_regex = re.compile(
            present_regex.pattern +
            r" density=(\\d+) raster=(\\d+)x(\\d+)")
    original = base.read_bytes().splitlines()
    candidate_crc = candidate.read_bytes().splitlines()
    text = log.read_text(encoding="utf-8", errors="replace")
    presents = [tuple(map(int, m.groups())) for m in present_regex.finditer(text)]
    preps = [tuple(map(int, m.groups())) for m in prep_regex.finditer(text)]
    accepted = {
        x[0] for x in presents
        if x[1:3] == (width, HEIGHT) and
        x[3] >= raster_width * 4 and x[4] == 1 and x[5] == 1 and
        (density == 1 or x[6:] == (density, raster_width, raster_height))
    }
    evidence = []
    for file in sorted(captures.glob(prefix + "-*.pam")):
        match = filename_regex.fullmatch(file.name)
        if match is None:
            raise ValueError(f"Invalid frame name: {file.name}")
        content = file.read_bytes()
        if not content.startswith(header) or len(content) != len(header) + raster_width * raster_height * 4:
            raise ValueError(f"Invalid calibrated world physical raster: {file}")
        raster = content[len(header):]
        logical, exact_nearest = restore_logical_nearest(
            raster, width, HEIGHT, density)
        margin = edge_differences(logical, width=width, extra=extra)
        frame = int(match.group(1))
        evidence.append({
            "frame": frame, "filename": file.name,
            "sha256": hashlib.sha256(raster).hexdigest(),
            "world_margin_differences": margin,
            "exact_nearest_blocks": exact_nearest,
            "valid_four_margins": all(value > 32 for value in margin.values()),
        })
    witnessed = [v for v in evidence if
                 v["frame"] in accepted and v["valid_four_margins"] and
                 v["exact_nearest_blocks"]]
    passed = (
        original == candidate_crc and len(original) == 2473
        and len(witnessed) >= 2
        and len({e["sha256"] for e in witnessed}) >= 2
        and any(row[1] == 1 and row[2:4] == (width, HEIGHT) for row in preps)
    )
    return {
        "schema_version": 1, "status": "passed" if passed else "unproven",
        "logical_guest_geometry": [256, 224],
        "host_wide_raster": [width, HEIGHT],
        "presentation_raster": [raster_width, raster_height],
        "internal_density": density,
        "view_mode": view,
        "backing_course_margin": backing,
        "per_side_new_world_pixels": extra,
        "base_frames": len(original), "candidate_frames": len(candidate_crc),
        "identical_guest_crc_sequence": original == candidate_crc,
        "calibrated_presentations": len(accepted),
        "four_margin_image_frames": len(witnessed),
        "captures": evidence,
        "4k_or_hd_wide_claimed": False,
        "completed_usa_course_credit": 0,
        "limits": (
            "Two-player bounded route with exact nearest Original world "
            "pixels; still subject to stock/source geometry and per-slot "
            "OBJ/depth verification. Neither authored wide HD racer "
            "composition nor physical 3840x2160 output is established."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("base", "candidate", "log", "captures", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--view", choices=["ws24", "ws342"], default="ws24")
    p.add_argument("--density", type=int, choices=(1, 2, 3, 4), default=1)
    a = p.parse_args()
    evidence = assess(a.base, a.candidate, a.log, a.captures, view=a.view, density=a.density)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
