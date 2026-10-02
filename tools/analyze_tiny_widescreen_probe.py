#!/usr/bin/env python3
"""Compare deterministic Dragster dumps across tiny widescreen margins."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

MARGINS = (0, 8, 16, 24)
TAGS = [f"object-tail-{i:03d}" for i in range(50, 91)] + [
    f"object-tail-{i:03d}" for i in range(150, 191)
]


def u16(blob: bytes, addr: int) -> int:
    return blob[addr] | (blob[addr + 1] << 8)


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def read_bmp32(path: Path) -> tuple[bytes, int, int]:
    """Read the runner's top-down 32-bit BGRA framedump into BGRX bytes."""
    blob = path.read_bytes()
    if len(blob) < 54 or blob[:2] != b"BM":
        raise ValueError(f"{path}: not a BMP")
    offset = struct.unpack_from("<I", blob, 10)[0]
    width = struct.unpack_from("<i", blob, 18)[0]
    signed_height = struct.unpack_from("<i", blob, 22)[0]
    bpp = struct.unpack_from("<H", blob, 28)[0]
    if width <= 0 or signed_height == 0 or bpp != 32:
        raise ValueError(f"{path}: unsupported BMP geometry/bpp")
    height = abs(signed_height)
    raw = blob[offset : offset + width * height * 4]
    if len(raw) != width * height * 4:
        raise ValueError(f"{path}: truncated pixel payload")
    if signed_height > 0:
        rows = [raw[y * width * 4 : (y + 1) * width * 4] for y in range(height)]
        raw = b"".join(reversed(rows))
    return raw, width, height


def load_sample(root: Path, margin: int, tag: str) -> dict:
    d = root / f"margin-{margin}"
    info_path = d / "state" / f"{tag}.info.json"
    wram_path = d / "state" / f"{tag}.wram.bin"
    if not (info_path.is_file() and wram_path.is_file()):
        raise FileNotFoundError(f"missing state sample margin={margin} tag={tag}")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    frame = int(info["frame"])
    # Scripted state dumps are taken at a simulation boundary labelled with
    # snes_frame_counter. FrameDump_Present names the already-completed raster
    # as snes_frame_counter - 1. Pair the state tag with that exact picture.
    presented_frame = frame - 1
    fb_path = d / "frames" / f"frame_{presented_frame:06d}.bmp"
    if not fb_path.is_file():
        raise FileNotFoundError(
            f"missing wide framedump margin={margin} presented_frame={presented_frame}"
        )
    fb, width, height = read_bmp32(fb_path)
    return {
        "info": info,
        "wram": wram_path.read_bytes(),
        "fb": fb,
        "width": width,
        "height": height,
        "frame": frame,
        "presented_frame": presented_frame,
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


def checker_columns(sample: dict, x0: int, x1: int) -> int:
    """Count columns containing the finish stripe's black/white/black stack.

    The known Dragster stripe is vertically checkered where it enters from the
    right. Requiring three contiguous alternating near-black/near-white runs
    rejects a solid dark backdrop, ordinary rail, and isolated bright pixels.
    """

    width, height, fb = sample["width"], sample["height"], sample["fb"]
    x0 = max(0, min(width, x0))
    x1 = max(x0, min(width, x1))
    y0, y1 = min(140, height), min(170, height)
    matched = 0
    for x in range(x0, x1):
        classes: list[int] = []
        for y in range(y0, y1):
            row = y * width * 4
            b, g, r, _ = fb[row + x * 4 : row + x * 4 + 4]
            if max(r, g, b) < 40:
                classes.append(0)
            elif min(r, g, b) > 210:
                classes.append(1)
            else:
                classes.append(-1)

        runs: list[tuple[int, int]] = []
        i = 0
        while i < len(classes):
            cls = classes[i]
            j = i + 1
            while j < len(classes) and classes[j] == cls:
                j += 1
            if cls in (0, 1):
                runs.append((cls, j - i))
            i = j

        found = False
        for i in range(len(runs) - 2):
            a, b, c = runs[i : i + 3]
            if (
                a[0] != b[0]
                and b[0] != c[0]
                and a[0] == c[0]
                and all(2 <= run[1] <= 14 for run in (a, b, c))
            ):
                found = True
                break
        if found:
            matched += 1
    return matched


def trajectory_state(wram: bytes) -> dict:
    """Durable event-relative race state used as the simulation invariant.

    $0E95 is deliberately excluded here. The Dragster tail evidence shows that
    this contact scratch word can differ transiently at the same scripted event
    while position, velocity, camera and progression remain identical and then
    reconverge. We retain it separately as a diagnostic surface rather than
    letting a boundary-phase scratch value masquerade as trajectory divergence.
    """
    return {
        "race_active": wram[0x0313],
        "p1_x": u16(wram, 0x0411),
        "p1_y": u16(wram, 0x0415),
        "p1_xspeed": u16(wram, 0x04B7),
        "p1_yspeed": u16(wram, 0x04BB),
        "camera_x": u16(wram, 0x0419),
        "checkpoint": u16(wram, 0x1199),
        "finish_gate": u16(wram, 0x119D),
        "laps_remaining": u16(wram, 0x0EF1),
    }


def contact_word(wram: bytes) -> int:
    return u16(wram, 0x0E95)


def classify_margin(rows: list[dict]) -> str:
    if any(not r["trajectory_equal"] for r in rows):
        return "meaningful-authoritative-divergence"
    deltas = {r["guest_frame_delta"] for r in rows}
    contact_diffs = [r for r in rows if not r["contact_equal"]]
    if len(deltas) == 1 and contact_diffs:
        return "host-presentation-cadence-transient-contact-only"
    if len(deltas) == 1:
        return "event-relative-match"
    return "event-relative-match-with-variable-host-cadence"


def first_tag(rows: list[dict], key: str) -> dict | None:
    return next((r for r in rows if r[key]), None)


def script_milestones(root: Path, margin: int) -> dict[str, int]:
    """Extract cheap frontend/race cadence anchors from the retained host log."""
    path = root / f"margin-{margin}.log"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    patterns = {
        "first_main_menu_until": r"script f=(\d+) until 0009F ok after",
        "race_entered_dump": r"script f=(\d+) dump race-entered ok",
        "finish_probe_start_dump": r"script f=(\d+) dump finish-probe-start ok",
    }
    out = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            out[name] = int(match.group(1))
    return out


def scan_presented_frames(root: Path, margin: int) -> dict:
    frames = root / f"margin-{margin}" / "frames"
    expected_width = 256 + 2 * margin
    first_checker = None
    first_nonblack = None
    scanned = 0
    for path in sorted(frames.glob("frame_*.bmp")):
        try:
            frame = int(path.stem.split("_")[-1])
        except ValueError:
            continue
        fb, width, height = read_bmp32(path)
        if width != expected_width:
            raise ValueError(
                f"{path}: expected presented width {expected_width}, got {width}"
            )
        sample = {"fb": fb, "width": width, "height": height}
        scanned += 1
        if margin:
            left = nonblack_margin_pixels(sample, margin, "left")
            right = nonblack_margin_pixels(sample, margin, "right")
            if first_nonblack is None and (left or right):
                first_nonblack = {
                    "presented_frame": frame,
                    "left_margin_nonblack": left,
                    "right_margin_nonblack": right,
                }
            cols = checker_columns(sample, margin + 256, width)
            if first_checker is None and cols:
                first_checker = {
                    "presented_frame": frame,
                    "right_margin_checker_columns": cols,
                }
    return {
        "scanned_frames": scanned,
        "first_nonblack_margin": first_nonblack,
        "first_finish_checker_in_extra_margin": first_checker,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    control = {tag: load_sample(args.root, 0, tag) for tag in TAGS}
    control_milestones = script_milestones(args.root, 0)
    report = {
        "fixture": "tests/input/object-activation-dragster-tail.script",
        "margins": list(MARGINS),
        "control_width": 256,
        "pixel_source": "SNESRecomp FrameDump_Present full presented framebuffer",
        "results": {},
    }

    for margin in MARGINS:
        rows = []
        for tag in TAGS:
            sample = load_sample(args.root, margin, tag)
            ctrl = control[tag]
            state = trajectory_state(sample["wram"])
            ctrl_state = trajectory_state(ctrl["wram"])
            contact = contact_word(sample["wram"])
            ctrl_contact = contact_word(ctrl["wram"])
            full_wram_equal = sample["wram"] == ctrl["wram"]
            center_equal = center_crop(sample, margin) == center_crop(ctrl, 0)
            classic_right = margin + 256
            right_checker = checker_columns(sample, classic_right, sample["width"])
            row = {
                "tag": tag,
                "frame": sample["frame"],
                "width": sample["width"],
                "state": state,
                "trajectory_equal": state == ctrl_state,
                "contact_word": contact,
                "control_contact_word": ctrl_contact,
                "contact_equal": contact == ctrl_contact,
                "guest_frame_delta": sample["frame"] - ctrl["frame"],
                "full_wram_equal": full_wram_equal,
                "wram_sha256": sha(sample["wram"]),
                "center_256_equal": center_equal,
                "left_margin_nonblack": nonblack_margin_pixels(sample, margin, "left"),
                "right_margin_nonblack": nonblack_margin_pixels(sample, margin, "right"),
                "right_margin_checker_columns": right_checker,
                "finish_checker_in_extra_margin": right_checker >= 1,
            }
            rows.append(row)

        expected_width = 256 + 2 * margin
        if any(r["width"] != expected_width for r in rows):
            raise SystemExit(f"margin {margin}: framebuffer width mismatch")

        presentation_scan = scan_presented_frames(args.root, margin)
        first_checker = presentation_scan["first_finish_checker_in_extra_margin"]
        first_center = first_tag([{**r, "_bad": not r["center_256_equal"]} for r in rows], "_bad")
        contact_diffs = [r for r in rows if not r["contact_equal"]]
        frame_deltas = sorted({r["guest_frame_delta"] for r in rows})
        milestones = script_milestones(args.root, margin)
        milestone_deltas = {
            name: frame - control_milestones[name]
            for name, frame in milestones.items()
            if name in control_milestones
        }
        earliest_cadence_anchor = next(
            (
                {"name": name, "guest_frame_delta": milestone_deltas[name]}
                for name in ("first_main_menu_until", "race_entered_dump", "finish_probe_start_dump")
                if milestone_deltas.get(name, 0) != 0
            ),
            None,
        )
        report["results"][str(margin)] = {
            "expected_width": expected_width,
            "classification": classify_margin(rows),
            "all_meaningful_authoritative_state_equal": all(r["trajectory_equal"] for r in rows),
            "all_contact_words_equal": not contact_diffs,
            "contact_mismatch_tags": [r["tag"] for r in contact_diffs],
            "contact_reconverged_by_final_sample": bool(rows[-1]["contact_equal"]),
            "guest_frame_deltas": frame_deltas,
            "constant_guest_frame_delta": len(frame_deltas) == 1,
            "script_milestones": milestones,
            "script_milestone_frame_deltas": milestone_deltas,
            "earliest_cadence_anchor": earliest_cadence_anchor,
            "cadence_shift_precedes_race": bool(
                earliest_cadence_anchor
                and earliest_cadence_anchor["name"] == "first_main_menu_until"
            ),
            "all_full_wram_equal": all(r["full_wram_equal"] for r in rows),
            "all_center_256_equal": all(r["center_256_equal"] for r in rows),
            "first_center_regression": first_center,
            "presentation_scan": presentation_scan,
            "first_finish_checker_in_extra_margin": first_checker,
            "first_nonblack_margin": presentation_scan["first_nonblack_margin"],
            "samples": rows,
        }

    lines = [
        "# Tiny-margin Widescreen Dragster probe",
        "",
        "Host-only native-widescreen reconnaissance using the same deterministic",
        "Dragster finish fixture as the activation/visibility proof.",
        "",
        "| margin/side | width | classification | guest-frame delta | trajectory | contact | center 256 | first checker in extra right margin |",
        "|---:|---:|---|---:|---|---|---|---|",
    ]
    for margin in MARGINS:
        r = report["results"][str(margin)]
        first = r["first_finish_checker_in_extra_margin"]
        first_text = "none" if first is None else f"presented f{first['presented_frame']}"
        delta_text = ",".join(str(v) for v in r["guest_frame_deltas"])
        lines.append(
            f"| {margin} | {r['expected_width']} | {r['classification']} | "
            f"{delta_text} | "
            f"{'match' if r['all_meaningful_authoritative_state_equal'] else 'DIVERGE'} | "
            f"{'match' if r['all_contact_words_equal'] else 'transient diff'} | "
            f"{'match' if r['all_center_256_equal'] else 'diff'} | {first_text} |"
        )

    lines += [
        "",
        "Interpretation guardrails:",
        "",
        "- durable trajectory/progression equality at the same scripted event is the hard simulation invariant;",
        "- guest-frame deltas and frontend/race log milestones are reported explicitly because host presentation can shift absolute guest cadence;",
        "- $0E95 contact words remain a diagnostic surface: transient differences are recorded, never silently ignored;",
        "- full-WRAM equality is supporting evidence only; host/render bookkeeping and global phase bytes are expected to differ;",
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
