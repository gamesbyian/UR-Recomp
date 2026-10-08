#!/usr/bin/env python3
"""Replay the recovered Jumpover fall-through SMVs in historical Snes9x 1.51-rr.

Every case runs as an SMV through ``-autodemo`` so the emulator applies the
movie's own embedded anchor and sync settings. Controls are derived from the
same anchor by rebuilding the SMV with either a different controller stream or
a 16-bit P1 X override patched into the embedded freeze's WRAM (the same
frame-boundary write the historical Dessyreqt sweep scripts perform).
``tools/observe_jumpover_fallthrough.lua`` only observes.

Rebuilt movies and logs are scratch material under ``--work-dir``.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from extract_smv_freeze import (  # noqa: E402
    decompress_embedded_freeze,
    parse_freeze,
    parse_smv_header,
)

OBSERVER = ROOT / "tools" / "observe_jumpover_fallthrough.lua"


def controller_samples(data: bytes) -> list[int]:
    hdr = parse_smv_header(data)
    if hdr["controller_mask"] != 1:
        raise ValueError("probe supports single-controller movies only")
    count = struct.unpack_from("<I", data, 0x20)[0]
    off = hdr["controller_data_offset"]
    return [struct.unpack_from("<H", data, off + 2 * i)[0] for i in range(count)]


def rebuild_smv(data: bytes, samples: list[int] | None = None,
                wram_writes: dict[int, int] | None = None) -> bytes:
    """Return a movie with the same header/anchor and optional changes.

    ``samples`` replaces the P1 controller stream; ``wram_writes`` maps WRAM
    offsets to 16-bit little-endian values patched into the embedded freeze.
    """
    hdr = parse_smv_header(data)
    if hdr["smv_version"] not in (4, 5):
        raise ValueError("rebuild supports SMV 1.51+ movies only")
    save_off = hdr["savestate_offset"]
    ctrl_off = hdr["controller_data_offset"]
    state = data[save_off:ctrl_off]
    if wram_writes:
        freeze, _ = decompress_embedded_freeze(data, hdr)
        _, blocks = parse_freeze(freeze)
        ram = next(b for b in blocks if b["tag"] == "RAM")
        patched = bytearray(freeze)
        for addr, value in wram_writes.items():
            struct.pack_into("<H", patched, ram["offset"] + addr, value & 0xFFFF)
        state = gzip.compress(bytes(patched), compresslevel=9, mtime=0)
    old = controller_samples(data)
    new = old if samples is None else samples
    tail = data[ctrl_off + 2 * len(old):]
    out = bytearray(data[:save_off]) + state
    new_ctrl = len(out)
    out += b"".join(struct.pack("<H", v & 0xFFFF) for v in new) + tail
    struct.pack_into("<I", out, 0x10, len(new))  # frame count
    struct.pack_into("<I", out, 0x1C, new_ctrl)
    struct.pack_into("<I", out, 0x20, len(new))  # sample count
    return bytes(out)


def parse_log(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        if not line.startswith("frame="):
            continue
        rows.append({k: int(v) for k, v in (p.split("=", 1) for p in line.split())})
    return rows


def run_movie(snes9x: Path, rom: Path, movie: Path, work: Path, timeout: float = 60.0) -> list[dict]:
    home = work / "home"
    (home / ".snes96_snapshots").mkdir(parents=True, exist_ok=True)
    log = movie.with_suffix(".log")
    done = movie.with_suffix(".done")
    for p in (log, done):
        p.unlink(missing_ok=True)
    env = dict(os.environ, HOME=str(home), UR_JO_LOG=str(log), UR_JO_DONE=str(done))
    cmd = [
        "xvfb-run", "-a", str(snes9x), "-nostdconf", "-sound", "-soundsync", "-mute", "-nojoy",
        "-autodemo", str(movie), "-loadlua", str(OBSERVER), str(rom),
    ]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline and proc.poll() is None:
            if done.exists() and done.stat().st_size:
                break
            time.sleep(0.2)
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        proc.wait(timeout=10)
    status = done.read_text().strip() if done.exists() else "status=timeout"
    if status != "status=complete":
        raise RuntimeError(f"{movie.name}: observer ended with {status}")
    return parse_log(log.read_text())


# --- route definitions and analysis -----------------------------------------

GLITCHES = "reference/imported/reverse-engineering/dessyreqt/Glitches"
ROUTES = {
    # route: (movie, shoulder bit held during the stunt)
    "left": (f"{GLITCHES}/Jumpover - Jump through halfpipe - left.smv", 0x0020),
    "right": (f"{GLITCHES}/Jumpover - Jump through halfpipe.smv", 0x0010),
}
# The direction-matched ordinary control releases only the held shoulder
# button (L for left, R for right) on one movie input sample. The scan selects
# the latest sample that still changes the outcome; both routes share it.
CONTROL_SAMPLE = 42
SCAN_SAMPLES = range(30, 48)
EXTENSION_FRAMES = 60  # repeat the final held input, as the historical scripts do
FALL_CONFIRM_FRAMES = 10
TAKEOFF_SHIFTS = (-1, 1, 2, 3, 4)
WINDOW_BEFORE = 3
WINDOW_AFTER = 5
WINDOW_FIELDS = (
    "p1_x", "p1_y", "p1_x_speed", "p1_y_speed", "p1_pitch", "p1_air_time",
    "p1_stunt_air_latch", "p1_contact_word_persisted",
)
SEMANTIC_FIELDS = WINDOW_FIELDS + (
    "p1_angular_velocity", "p1_z_rotation", "p1_roll_count", "p1_flip_count",
    "race_active", "track_id",
)
CONTACT_FIELDS = ("p1_air_time", "p1_contact_word_persisted")


def trajectory_sha256(rows: list[dict]) -> str:
    text = "\n".join(" ".join(f"{k}={r[k]}" for k in sorted(r)) for r in rows)
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def takeoff_frame(rows: list[dict]) -> int | None:
    return next((r["frame"] for r in rows if r["p1_air_time"] > 0), None)


def contact_frames_after(rows: list[dict], frame: int) -> list[int]:
    return [r["frame"] for r in rows if r["frame"] > frame and r["p1_air_time"] == 0]


def ranges(frames: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    for f in frames:
        if out and f == out[-1][1] + 1:
            out[-1][1] = f
        else:
            out.append([f, f])
    return out


def classify(case: list[dict], control: list[dict]) -> dict:
    """Classify ``case`` against its direction-matched ordinary control.

    Fall-through: P1 crosses below the deepest Y the control ever reaches
    while airborne, and stays airborne for ``FALL_CONFIRM_FRAMES`` after the
    crossing. A later landing on a lower course surface is reported, not
    treated as a recovery. The control itself must take off and regain
    contact (an ordinary traversal) or classification is refused.
    """
    if not case or not control:
        raise ValueError("classification needs both a case and its direction-matched control")
    c_take = takeoff_frame(control)
    if c_take is None or not contact_frames_after(control, c_take):
        raise ValueError("control never takes off and regains contact; it is not an ordinary traversal")
    floor_y = max(r["p1_y"] for r in control)
    take = takeoff_frame(case)
    contacts = contact_frames_after(case, take) if take is not None else []
    below = next((r["frame"] for r in case if r["p1_y"] > floor_y), None)
    by_frame = {r["frame"]: r for r in case}
    falls = below is not None and all(
        f in by_frame and by_frame[f]["p1_air_time"] > 0
        for f in range(below, below + FALL_CONFIRM_FRAMES + 1)
    )
    before = [f for f in contacts if below is None or f < below]
    after = [f for f in contacts if below is not None and f > below]
    return {
        "outcome": "fall_through" if falls else "ordinary",
        "takeoff_frame": take,
        "post_takeoff_contact_ranges": ranges(contacts),
        "last_supported_frame_before_crossing": before[-1] if before else None,
        "control_max_y": floor_y,
        "first_frame_below_control_floor": below,
        "first_contact_below_control_floor": (
            {"frame": after[0], "p1_y": by_frame[after[0]]["p1_y"]} if after else None
        ),
        "final_y": case[-1]["p1_y"],
    }


def first_divergence(a: list[dict], b: list[dict], fields=SEMANTIC_FIELDS) -> dict | None:
    for ra, rb in zip(a, b):
        diff = sorted(f for f in fields if ra[f] != rb[f])
        if diff:
            return {"frame": ra["frame"], "fields": diff}
    return None


def window(rows: list[dict], center: int) -> list[dict]:
    return [
        {"frame": r["frame"], **{f: r[f] for f in WINDOW_FIELDS}}
        for r in rows
        if center - WINDOW_BEFORE <= r["frame"] <= center + WINDOW_AFTER
    ]


def run_route(route: str, snes9x: Path, rom: Path, work: Path, repeats: int, scan: bool) -> dict:
    from extract_smv_freeze import summarize_movie

    movie_rel, shoulder = ROUTES[route]
    src = (ROOT / movie_rel).read_bytes()
    anchor, _ = summarize_movie(ROOT / movie_rel, movie_rel)
    base = controller_samples(src)
    extended = base + [base[-1]] * EXTENSION_FRAMES
    control_inputs = list(extended)
    control_inputs[CONTROL_SAMPLE] &= ~shoulder

    def play(tag: str, data: bytes) -> list[dict]:
        path = work / f"{route}-{tag}.smv"
        path.write_bytes(data)
        return run_movie(snes9x, rom, path, work)

    unchanged = [play(f"unchanged-{i}", src) for i in range(repeats)]
    case = [play(f"extended-{i}", rebuild_smv(src, extended)) for i in range(repeats)]
    control = [play(f"control-{i}", rebuild_smv(src, control_inputs)) for i in range(repeats)]
    for runs, label in ((unchanged, "unchanged"), (case, "extended"), (control, "control")):
        if len({trajectory_sha256(r) for r in runs}) != 1:
            raise RuntimeError(f"{route} {label} replay is not repeatable")
    if case[0][: len(unchanged[0])] != unchanged[0]:
        raise RuntimeError(f"{route} extension altered the unchanged movie prefix")
    first = case[0][0]
    for name in ("p1_x", "p1_y", "p1_x_speed", "p1_pitch", "p2_x"):
        if first[name] != anchor["anchor_fields"][name]:
            raise RuntimeError(f"{route} frame 0 {name} does not equal the embedded anchor")

    cls = classify(case[0], control[0])
    ctl = classify(control[0], control[0])
    unchanged_cls = classify(unchanged[0], control[0])
    div = first_divergence(case[0], control[0])
    contact_div = first_divergence(case[0], control[0], CONTACT_FIELDS)
    result = {
        "route": route,
        "movie": movie_rel,
        "anchor_freeze_sha256": anchor["freeze_sha256"],
        "anchor_wram_sha256": anchor["wram_sha256"],
        "movie_frames": len(base),
        "extension_frames": EXTENSION_FRAMES,
        "repeats": repeats,
        "repeat_identical": True,
        "trajectory_sha256": {
            "unchanged": trajectory_sha256(unchanged[0]),
            "extended": trajectory_sha256(case[0]),
            "control": trajectory_sha256(control[0]),
        },
        "unchanged_movie": {
            "final_frame": unchanged[0][-1]["frame"],
            "final_y": unchanged[0][-1]["p1_y"],
            "first_frame_below_control_floor": unchanged_cls["first_frame_below_control_floor"],
            "crossing_within_unchanged_movie": unchanged_cls["first_frame_below_control_floor"] is not None,
        },
        "case": cls,
        "control": {
            "definition": (
                f"same anchor and inputs, extended identically; shoulder bit 0x{shoulder:04x} "
                f"released on movie input sample {CONTROL_SAMPLE} only"
            ),
            "outcome": "ordinary",
            "takeoff_frame": ctl["takeoff_frame"],
            "post_takeoff_contact_ranges": ctl["post_takeoff_contact_ranges"],
            "max_y": ctl["control_max_y"],
        },
        "first_semantic_divergence": div,
        "first_contact_state_divergence": contact_div,
        "event_window_case": window(case[0], contact_div["frame"]) if contact_div else [],
        "event_window_control": window(control[0], contact_div["frame"]) if contact_div else [],
    }
    if scan:
        outcomes = {}
        for sample in SCAN_SAMPLES:
            inputs = list(extended)
            inputs[sample] &= ~shoulder
            rows = play(f"scan-{sample}", rebuild_smv(src, inputs))
            outcomes[str(sample)] = {
                "outcome": classify(rows, control[0])["outcome"],
                "identical_to_case": rows == case[0],
            }
        result["single_sample_shoulder_release_scan"] = outcomes
        # Takeoff timing: drop (-1) or repeat (+d) the leading direction-only
        # sample, shifting the whole jump/stunt sequence by d frames (about
        # 15 X units per frame at the anchor speed).
        shifts = {}
        for d in TAKEOFF_SHIFTS:
            inputs = base[1:] if d < 0 else [base[0]] * d + base
            inputs = inputs + [base[-1]] * (len(extended) - len(inputs))
            rows = play(f"shift{d:+d}", rebuild_smv(src, inputs))
            c = classify(rows, control[0])
            shifts[f"{d:+d}"] = {
                "outcome": c["outcome"],
                "takeoff_frame": c["takeoff_frame"],
                "identical_to_case": rows == case[0],
            }
        result["takeoff_shift_scan"] = shifts
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snes9x", type=Path, required=True, help="historical Snes9x 1.51-rr executable")
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--work-dir", type=Path, required=True, help="scratch directory for rebuilt movies and logs")
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--scan", action="store_true", help="also scan single-sample shoulder releases")
    ap.add_argument(
        "--snes9x-revision",
        default="TASEmulators/snes9x-rr@e0b6a74 + lua51@528486b + tools/patch_historical_snes9x151.py",
    )
    args = ap.parse_args(argv)
    if args.repeats < 2:
        ap.error("--repeats must be at least 2 to establish repeatability")
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    routes = [
        run_route(r, args.snes9x.resolve(), args.rom.resolve(), work, args.repeats, args.scan)
        for r in ROUTES
    ]
    doc = {
        "schema_version": 1,
        "kind": "historical-reference-replay",
        "course": "Jumpover",
        "emulator": args.snes9x_revision,
        "observer": "tools/observe_jumpover_fallthrough.lua",
        "driver": "tools/probe_jumpover_fallthrough.py",
        "frame_convention": "frame k = P1 state after k emulated movie frames; frame 0 = embedded anchor; input sample i is consumed by frame i+1",
        "routes": routes,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    for r in routes:
        print(r["route"], r["case"]["outcome"], "contact divergence", r["first_contact_state_divergence"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
