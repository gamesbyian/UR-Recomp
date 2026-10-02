#!/usr/bin/env python3
"""Compare deterministic Dragster dumps across tiny widescreen margins."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MARGINS = (0, 8, 16, 24)
TAGS = [f"object-tail-{i:03d}" for i in range(50, 91)] + [
    f"object-tail-{i:03d}" for i in range(150, 191)
]


def u16(blob: bytes, addr: int) -> int:
    return blob[addr] | (blob[addr + 1] << 8)


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def load_sample(root: Path, margin: int, tag: str) -> dict:
    d = root / f"margin-{margin}"
    info_path = d / f"{tag}.info.json"
    wram_path = d / f"{tag}.wram.bin"
    fb_path = d / f"{tag}.fb.bgrx"
    if not (info_path.is_file() and wram_path.is_file() and fb_path.is_file()):
        raise FileNotFoundError(f"missing sample margin={margin} tag={tag}")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    wram = wram_path.read_bytes()
    fb = fb_path.read_bytes()
    width = int(info["fb_width"])
    height = int(info["fb_height"])
    if len(fb) != width * height * 4:
        raise ValueError(f"{fb_path}: unexpected framebuffer size")
    return {
        "info": info,
        "wram": wram,
        "fb": fb,
        "width": width,
        "height": height,
        "frame": int(info["frame"]),
    }


def center_crop(sample: dict, margin: int) -> bytes:
    width, height, fb = sample["width"], sample["height"], sample["fb"]
    if width != 256 + 2 * margin:
        raise ValueError(f"margin {margin}: expected width {256 + 2 * margin}, got {width}")
    out = bytearray()
    for y in range(height):
        row = y * width * 4
        x0 = margin * 4
        out += fb[row + x0 : row + x0 + 256 * 4]
    return bytes(out)


def nonblack_margin_pixels(sample: dict, margin: int, side: str) -> int:
    if margin == 0:
        return 0
    width, height, fb = sample["width"], sample["height"], sample["fb"]
    xs = range(0, margin) if side == "left" else range(width - margin, width)
    count = 0
    for y in range(height):
        row = y * width * 4
        for x in xs:
            b, g, r, _ = fb[row + x * 4 : row + x * 4 + 4]
            if r or g or b:
                count += 1
    return count


def checker_pixels(sample: dict, x0: int, x1: int) -> int:
    width, height, fb = sample["width"], sample["height"], sample["fb"]
    x0 = max(0, min(width, x0))
    x1 = max(x0, min(width, x1))
    y0, y1 = min(145, height), min(165, height)
    count = 0
    for y in range(y0, y1):
        row = y * width * 4
        for x in range(x0, x1):
            b, g, r, _ = fb[row + x * 4 : row + x * 4 + 4]
            if max(r, g, b) < 40 or min(r, g, b) > 210:
                count += 1
    return count


def state_tuple(wram: bytes) -> dict:
    return {
        "race_active": wram[0x0313],
        "p1_x": u16(wram, 0x0411),
        "p1_y": u16(wram, 0x0415),
        "p1_xspeed": u16(wram, 0x04B7),
        "p1_yspeed": u16(wram, 0x04BB),
        "camera_x": u16(wram, 0x0419),
        "collision": u16(wram, 0x0E95),
        "checkpoint": u16(wram, 0x1199),
        "finish_gate": u16(wram, 0x119D),
        "laps_remaining": u16(wram, 0x0EF1),
    }


def first_tag(rows: list[dict], key: str) -> dict | None:
    return next((r for r in rows if r[key]), None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    control = {tag: load_sample(args.root, 0, tag) for tag in TAGS}
    report = {
        "fixture": "tests/input/object-activation-dragster-tail.script",
        "margins": list(MARGINS),
        "control_width": 256,
        "results": {},
    }

    for margin in MARGINS:
        rows = []
        for tag in TAGS:
            sample = load_sample(args.root, margin, tag)
            ctrl = control[tag]
            state = state_tuple(sample["wram"])
            ctrl_state = state_tuple(ctrl["wram"])
            full_wram_equal = sample["wram"] == ctrl["wram"]
            center_equal = center_crop(sample, margin) == center_crop(ctrl, 0)
            classic_right = margin + 256
            right_checker = checker_pixels(sample, classic_right, sample["width"])
            row = {
                "tag": tag,
                "frame": sample["frame"],
                "width": sample["width"],
                "state": state,
                "state_equal": state == ctrl_state,
                "full_wram_equal": full_wram_equal,
                "wram_sha256": sha(sample["wram"]),
                "center_256_equal": center_equal,
                "left_margin_nonblack": nonblack_margin_pixels(sample, margin, "left"),
                "right_margin_nonblack": nonblack_margin_pixels(sample, margin, "right"),
                "right_margin_checker_pixels": right_checker,
                "finish_checker_in_extra_margin": right_checker >= 16,
            }
            rows.append(row)

        expected_width = 256 + 2 * margin
        if any(r["width"] != expected_width for r in rows):
            raise SystemExit(f"margin {margin}: framebuffer width mismatch")
        if any(not r["state_equal"] for r in rows):
            raise SystemExit(f"margin {margin}: authoritative state diverged from 4:3 control")

        first_checker = first_tag(rows, "finish_checker_in_extra_margin")
        first_center = first_tag([{**r, "_bad": not r["center_256_equal"]} for r in rows], "_bad")
        report["results"][str(margin)] = {
            "expected_width": expected_width,
            "all_authoritative_state_equal": all(r["state_equal"] for r in rows),
            "all_full_wram_equal": all(r["full_wram_equal"] for r in rows),
            "all_center_256_equal": all(r["center_256_equal"] for r in rows),
            "first_center_regression": first_center,
            "first_finish_checker_in_extra_margin": first_checker,
            "first_nonblack_margin": next(
                (
                    r
                    for r in rows
                    if r["left_margin_nonblack"] or r["right_margin_nonblack"]
                ),
                None,
            ),
            "samples": rows,
        }

    lines = [
        "# Tiny-margin Widescreen Dragster probe",
        "",
        "Host-only native-widescreen reconnaissance using the same deterministic",
        "Dragster finish fixture as the activation/visibility proof.",
        "",
        "| margin/side | width | auth state | full WRAM | center 256 | first checker in extra right margin |",
        "|---:|---:|---|---|---|---|",
    ]
    for margin in MARGINS:
        r = report["results"][str(margin)]
        first = r["first_finish_checker_in_extra_margin"]
        first_text = "none" if first is None else f"{first['tag']} / f{first['frame']}"
        lines.append(
            f"| {margin} | {r['expected_width']} | "
            f"{'match' if r['all_authoritative_state_equal'] else 'DIVERGE'} | "
            f"{'match' if r['all_full_wram_equal'] else 'diff'} | "
            f"{'match' if r['all_center_256_equal'] else 'diff'} | {first_text} |"
        )

    lines += [
        "",
        "Interpretation guardrails:",
        "",
        "- authoritative-state equality is the hard simulation invariant;",
        "- full-WRAM equality is stronger supporting evidence, but not required by the report schema;",
        "- center-256 equality checks that widening did not disturb the authentic viewport;",
        "- non-black margin pixels prove exposure, not correctness;",
        "- checker ingress only times the known finish/checker feature; it does not classify all margin art.",
    ]

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
