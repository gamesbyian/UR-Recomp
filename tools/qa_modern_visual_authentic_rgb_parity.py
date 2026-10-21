#!/usr/bin/env python3
"""Independent exact-RGB verifier: stock P6 -> final SDL3 P7, no art approval.

Read-only. Replays native 4:3 viewport, nearest-neighbour pixel-centre
sampling, verifies every RGB pixel plus black side/bottom bars. It requires
authentic execution and the *same retained run's* source and SDL readback
markers, but cannot independently prove physical monitor output or ROM parity.
Retains original zero-alpha P7 unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

P6_HEADER = b"P6\n256 224\n255\n"
P7_RE = re.compile(rb"\AP7\nWIDTH ([0-9]+)\nHEIGHT ([0-9]+)\nDEPTH 4\n"
                   rb"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")
MAX_PIXEL_BYTES = 3840 * 2160 * 4


class EvidenceError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_bytes(path: Path, *, max_size: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise EvidenceError(f"missing or redirected evidence: {path.name}")
    if path.stat().st_size > max_size:
        raise EvidenceError("oversized evidence")
    return path.read_bytes()


def verify(stage: Path, receipt_path: Path) -> dict:
    """Return a zero-approval independent pixel receipt or raise."""
    if not stage.is_dir() or stage.is_symlink():
        raise EvidenceError("unsafe stage directory")
    p6 = load_bytes(stage / "stock-composed-before-sdl.ppm",
                    max_size=len(P6_HEADER) + 256 * 224 * 3)
    if not p6.startswith(P6_HEADER) or len(p6) != len(P6_HEADER) + 256 * 224 * 3:
        raise EvidenceError("stock composed P6 format/geometry mismatch")
    p7 = load_bytes(stage / "actual-sdl-drawable.pam",
                    max_size=MAX_PIXEL_BYTES + 256)
    head = P7_RE.match(p7)
    if not head:
        raise EvidenceError("SDL P7 invalid header or non-RGBA format")
    w, h = map(int, head.groups())
    if not (320 <= w <= 3840 and 224 <= h <= 2160 and
            len(p7) == head.end() + w * h * 4):
        raise EvidenceError("SDL P7 raster incomplete or unsafe")
    log = load_bytes(stage / "native-process.log", max_size=2 * 1024 * 1024)
    receipt_raw = load_bytes(receipt_path, max_size=64 * 1024)
    try:
        receipt = json.loads(receipt_raw)
        native_log = log.decode("utf-8")
    except (ValueError, UnicodeError) as exc:
        raise EvidenceError("native log/receipt malformed") from exc
    if not isinstance(receipt, dict):
        raise EvidenceError("invalid native receipt")
    if (receipt.get("execution_mode") != "authentic" or
            receipt.get("native_semantic_route") != "authentic-stock" or
            receipt.get("actual_sdl_renderer_output") != [w, h] or
            receipt.get("p7_sha256") != sha256(p7) or
            receipt.get("native_process_log_sha256") != sha256(log) or
            receipt.get("release_gate_credit") != 0 or
            receipt.get("authentic_isolation_approved") is not False):
        raise EvidenceError("Authentic receipt hash, source or nonapproval mismatch")
    markers = [
        "[snes_load]",
        f"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=240 guest_frame=240 "
        f"output={w}x{h} source=SDL_RenderReadPixels backend=sdl3",
    ]
    if any(m not in native_log for m in markers):
        raise EvidenceError("genuine stock-load or SDL3 source marker missing")
    if "UR_BALDOSA_MODERN_ROOT opened=1" in native_log or "UR_BALDOSA_MODERN_ROOT painted=1" in native_log:
        raise EvidenceError("Modern root leaked into Authentic source execution")

    # SNES pixels have 7:6 aspect ratio, so 256x224 logical source fills
    # a 4:3 *host output viewport*. The actual SDL pixel position must agree,
    # not a transformed/re-encoded screenshot built from an arbitrary source.
    view_w = min(w, (h * 4) // 3)
    view_h = min(h, (w * 3) // 4)
    x0, y0 = (w - view_w) // 2, (h - view_h) // 2
    if view_w < 320 or view_h < 224:
        raise EvidenceError("unsafe or unexpected stock 4:3 SDL viewport")
    source = memoryview(p6)[len(P6_HEADER):]
    rgba = memoryview(p7)[head.end():]
    # Precompute one row per 224 source rows to bound runtime/memory.
    x_index = [min(255, ((2 * x + 1) * 256) // (2 * view_w))
               for x in range(view_w)]
    rows: dict[int, bytes] = {}
    matched = 0
    outer = 0
    alpha_nonzero = 0
    for y in range(h):
        line = rgba[y * w * 4:(y + 1) * w * 4]
        in_y = y0 <= y < y0 + view_h
        if in_y:
            sy = min(223, ((2 * (y - y0) + 1) * 224) // (2 * view_h))
            if sy not in rows:
                base = sy * 256 * 3
                rows[sy] = b"".join(
                    source[base + sx * 3:base + sx * 3 + 3]
                    for sx in x_index)
            expected = rows[sy]
        for x in range(w):
            i = x * 4
            if line[i + 3]:
                alpha_nonzero += 1
            if in_y and x0 <= x < x0 + view_w:
                j = (x - x0) * 3
                if (line[i] != expected[j] or
                        line[i+1] != expected[j+1] or
                        line[i+2] != expected[j+2]):
                    raise EvidenceError(f"stock RGB first divergence at SDL ({x},{y})")
                matched += 1
            else:
                if any(line[i:i+3]):
                    raise EvidenceError(f"nonblack stock pillarbox at SDL ({x},{y})")
                outer += 1
    if matched != view_w * view_h or matched + outer != w * h:
        raise EvidenceError("incomplete SDL source-to-viewport comparison")
    return {
        "schema_version": 1,
        "kind": "native authentic post-composition P6 vs final SDL3 P7 RGB comparison",
        "source_p6_sha256": sha256(p6),
        "readback_p7_sha256": sha256(p7),
        "retained_process_log_sha256": sha256(log),
        "native_executable_sha256": receipt.get("exe_sha256"),
        "drawable": [w, h],
        "source": [256, 224],
        "viewport": [x0, y0, view_w, view_h],
        "rgb_exact_viewport_pixels": matched,
        "rgb_exact_black_bar_pixels": outer,
        "total_exact_rgb_pixels": matched + outer,
        "nonzero_alpha_pixels": alpha_nonzero,
        "no_modern_root_marker": True,
        "rgb_pixel_parity_proven": True,
        "physical_display_approved": False,
        "authentic_isolation_approved": False,
        "human_visual_approved": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", type=Path, required=True,
                   help="Native host's probe_first directory containing source P6, SDL P7 and same-process log")
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        report = verify(args.stage, args.receipt)
        if args.out.exists() or args.out.is_symlink():
            raise EvidenceError("report destination already exists")
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0
    except (EvidenceError, ValueError, OSError) as exc:
        print("UR_AUTHENTIC_RGB_PARITY_REJECTED:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
