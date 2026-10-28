#!/usr/bin/env python3
"""Source/PE-bound *diagnostic* final SDL witness for default stock attract.

Every case comes from an actual Windows guest-frame-targeted SDL readback.
A P7 checksum/pixel delta is evidence, never human/physical or MENU-10 approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from tools.probe_baldosa_modern_title_attract_win32 import MARKER
except ModuleNotFoundError:
    from probe_baldosa_modern_title_attract_win32 import MARKER

FRAMES = {"stock-attract-before": 1568,
          "stock-attract-after": 1584,
          "stock-attract-woken": 1616}
HEX = re.compile(r"[0-9a-f]{64}\Z")
SOURCE = re.compile(r"[0-9a-f]{40}\Z")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_case(root: Path, name: str, source: str):
    case = root / name
    if case.is_symlink() or not case.is_dir():
        raise ValueError("missing/redirected exact case: " + name)
    receipt_file = case / "readback-receipt.json"
    p7_file = case / "probe_first" / "actual-sdl-drawable.pam"
    log_file = case / "probe_first" / "native-process.log"
    for p in (receipt_file, p7_file, log_file):
        if not p.is_file() or p.is_symlink():
            raise ValueError("missing/redirected actual SDL evidence: " + name)
    d = json.loads(receipt_file.read_text(encoding="utf-8"))
    if (d.get("source_sha") != source or
            d.get("native_semantic_route") != name or
            d.get("observed_guest_frame") != FRAMES[name] or
            d.get("native_process_exit") != 0 or
            d.get("execution_mode") != "modern" or
            d.get("release_gate_credit") != 0 or
            d.get("visual_approved") is not False or
            d.get("hardware_approved") is not False or
            d.get("actual_sdl_renderer_output") != [1280, 720] or
            not isinstance(d.get("exe_sha256"), str) or
            not HEX.fullmatch(d["exe_sha256"])):
        raise ValueError("receipt lacks exact source/guest/PE/QA scope: " + name)
    log = log_file.read_bytes()
    p7 = p7_file.read_bytes()
    if digest(log) != d.get("native_process_log_sha256") or digest(p7) != d.get("p7_sha256"):
        raise ValueError("raw log or final SDL pixel SHA differs from receipt: " + name)
    header = b"P7\nWIDTH 1280\nHEIGHT 720\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
    if not p7.startswith(header) or len(p7) != len(header) + 1280 * 720 * 4:
        raise ValueError("invalid actual SDL P7 raster: " + name)
    # Windows native Path.write_text can retain CRLF. Hash immutable raw
    # bytes FIRST, then normalize line endings solely for exact regex parsing.
    # Never rewrite the forensic artifact or weaken source/guest markers.
    text = log.decode("utf-8", errors="replace").replace("\r\n", "\n")
    events = re.findall(
        r"(?m)^UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=(\d+) "
        r"guest_frame=(\d+) output=1280x720 "
        r"source=SDL_RenderReadPixels backend=(sdl2|sdl3)$", text)
    if (len(events) != 1 or int(events[0][1]) != FRAMES[name] or
            int(events[0][0]) != d.get("observed_in_draw") or
            d.get("SDL_driver") != "windows" or
            "UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=943" not in text):
        raise ValueError("actual guest-frame and SDL producer events not independently observed")
    original = [(m[1], int(m[2]), m[3], m[4], int(m[5]))
                for m in MARKER.finditer(text)]
    if (len(original) != 3 or
            [(m[0], m[1]) for m in original] != [
                ("main_menu", 440), ("attract_title", 943),
                ("demo_race", 1532)] or
            [m[4] for m in original] != [1, 1, 0] or
            original[0][2] != "d7" or original[0][3] == "01" or
            original[1][2] != "84" or original[1][3] == "01" or
            original[2][3] != "01"):
        raise ValueError("real original source MAIN-title-demo lifecycle not established")
    if name == "stock-attract-woken":
        if ("UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600" not in text
                or "UR_MODERN_TITLE_STOCK_ATTRACT p1_wake_consumed=1 frame=1600" not in text):
            raise ValueError("missing genuine source wake and Modern restoration")
    elif "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=demo_race frame=1532" not in text:
        raise ValueError("source original demo absent")
    return d, p7[len(header):]


def score(root: Path, source: str):
    if not SOURCE.fullmatch(source):
        raise ValueError("missing exact 40-character source SHA")
    rows = {name: read_case(root, name, source) for name in FRAMES}
    identities = {receipt["exe_sha256"] for receipt, _ in rows.values()}
    if len(identities) != 1:
        raise ValueError("captures do not share an exact native PE")
    def delta(a: str, b: str):
        p, q = rows[a][1], rows[b][1]
        # Compare RGB, not renderer alpha (which may legitimately be zero).
        return sum(p[i:i+3] != q[i:i+3] for i in range(0, len(p), 4))
    motion = delta("stock-attract-before", "stock-attract-after")
    wake = delta("stock-attract-after", "stock-attract-woken")
    if not motion or not wake:
        raise ValueError("stock demo did not move in final SDL or wake did not change drawable")
    if any(not any(p[i] or p[i+1] or p[i+2]
                   for i in range(0, len(p), 4)) for _, p in rows.values()):
        raise ValueError("one of the actual SDL frames is entirely black")
    return {
        "schema": "ur-menu10-final-sdl-diagnostic/1",
        "source_sha": source,
        "exe_sha256": next(iter(identities)),
        "actual_sdl_guest_frames": dict(FRAMES),
        "actual_sdl_original_demo_rgb_differing_pixels": motion,
        "actual_sdl_wake_rgb_differing_pixels": wake,
        "capture_paths": [name for name in FRAMES],
        "unmasked_rgb": True,
        "physical_hardware_verified": False,
        "menu10_independent_criterion_admitted": False,
        "release_gate_credit": 0,
        "first_usa_event_credit": 0,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = score(a.root, a.source_sha)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
