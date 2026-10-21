#!/usr/bin/env python3
"""Audit real SDL P7/PNG root identity legibility against its checkerboard.

Requires an independent native readback receipt, original P7, losslessly
converted PNG and process log. This is a bounded *pixel check*, not proof of
source authenticity, visual/art approval, physical GPU output or release QA.
No ROM, source art or third-party imaging library is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from verify_menu_source_art_bundle import read_png_rgba

STOCK_VIEWS = {
    (256, 224): (8, 10, 240, 204),
    (342, 224): (11, 10, 320, 204),
}
ROOT_LINE = re.compile(
    r"UR_BALDOSA_MODERN_DESTINATION stage=root "
    r"raster=(\d+)x(\d+) root=(\d+),(\d+),(\d+),(\d+)\b"
)
CAPTURE_LINE = "UR_MODERN_VISUAL_SDL_CAPTURE status=saved"
ROOT_PAINTED = "UR_BALDOSA_MODERN_ROOT painted=1"
MIN_TEXT_PIXELS = 64
MIN_BG_PIXELS = 64


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def source_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(value: int) -> float:
        s = value / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    return sum(weight * channel(value)
               for weight, value in zip((0.2126, 0.7152, 0.0722), rgb))


def ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    x, y = source_luminance(a), source_luminance(b)
    return (max(x, y) + .05) / (min(x, y) + .05)


def read_p7_rgba(path: Path, width: int, height: int) -> bytes:
    # Reject unbounded or malformed source instead of decoding mock PNG
    # from a receipt that merely CLAIMS an original unmodified readback.
    exact_header = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\n"
                    f"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode()
    with path.open("rb") as stream:
        header = stream.read(len(exact_header))
        if header != exact_header:
            raise ValueError("P7 is not exact expected native RGB_ALPHA")
        raw = stream.read(width * height * 4 + 1)
        if len(raw) != width * height * 4:
            raise ValueError("P7 pixels are truncated or trailing")
    return raw


def verify_capture(receipt: dict, png: Path, p7: Path, log: Path) -> dict:
    if receipt.get("schema_version") != 1 or (
            receipt.get("execution_mode") != "modern" or
            receipt.get("SDL_driver") != "windows" or
            receipt.get("native_process_exit") != 0 or
            receipt.get("visual_approved") is not False or
            receipt.get("release_gate_credit") != 0):
        raise ValueError("unsupported or pre-approved native receipt")
    dims = receipt.get("actual_sdl_renderer_output")
    if not isinstance(dims, list) or len(dims) != 2 or any(
            type(x) is not int or not 1 <= x <= 4096 for x in dims):
        raise ValueError("invalid native SDL output size")
    width, height = dims
    if (width, height) not in ((1024, 768), (1280, 720)):
        raise ValueError("check only calibrated native 4:3 and 16:9 sizes")
    for key, data in (("png_sha256", png), ("p7_sha256", p7),
                      ("native_process_log_sha256", log)):
        if not isinstance(receipt.get(key), str) or (
                sha256(data.read_bytes()) != receipt[key]):
            raise ValueError(f"{key}: file hash differs from source receipt")
    for key in ("exe_sha256", "source_sha"):
        value = receipt.get(key)
        if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{40,64}", value):
            raise ValueError(f"missing exact {key} provenance")
    lines = log.read_text(encoding="utf-8").splitlines()
    root = []
    for line in lines:
        m = ROOT_LINE.search(line)
        if m:
            root.append(tuple(int(x) for x in m.groups()))
    if not root or ROOT_PAINTED not in "\n".join(lines) or not any(
            CAPTURE_LINE in line and
            f"output={width}x{height}" in line and
            "source=SDL_RenderReadPixels" in line for line in lines):
        raise ValueError("missing actual source root paint/SDL readback log")
    geometries = set(root)
    if len(geometries) != 1:
        raise ValueError("native log mixes source root geometry")
    source_w, source_h, rx, ry, rw, rh = geometries.pop()
    expected = STOCK_VIEWS.get((source_w, source_h))
    if expected is None or (rx, ry, rw, rh) != expected:
        raise ValueError("source root geometry not recognized")
    native_rgba = read_p7_rgba(p7, width, height)
    converted_rgba = read_png_rgba(png, width, height)
    if native_rgba != converted_rgba:
        raise ValueError("PNG pixels differ from original native SDL P7")
    # Fit host source-pixel UI rectangle to actual SDL dimensions. This
    # is the observed bitmap mapping, not a hypothetical physical PAR.
    left = round((rx + 8) * width / source_w)
    right = round((rx + rw - 8) * width / source_w)
    top = round((ry + 36) * height / source_h)
    bottom = round((ry + 44) * height / source_h)
    if right - left < 50 or bottom - top < 8:
        raise ValueError("root identity sample region is too small")
    text_colors: dict[tuple[int, int, int], int] = {}
    checker_colors: dict[tuple[int, int, int], int] = {}
    for y in range(top, bottom):
        for x in range(left, right):
            offset = (y * width + x) * 4
            red, green, blue, alpha = native_rgba[offset:offset + 4]
            if not (red == green == blue):
                continue
            rgb = (red, green, blue)
            # Host text writes opaque grayscale pixels; the checker retains
            # alpha 0xE0. This admits exactly the source raster semantics.
            if alpha == 255 and 90 <= red < 245:
                text_colors[rgb] = text_colors.get(rgb, 0) + 1
            elif alpha == 224 and 30 <= red <= 95:
                checker_colors[rgb] = checker_colors.get(rgb, 0) + 1
    text_count = sum(text_colors.values())
    bg_count = sum(checker_colors.values())
    if text_count < MIN_TEXT_PIXELS or bg_count < MIN_BG_PIXELS or (
            len(checker_colors) < 2):
        raise ValueError("source image has no identifiable checker/text region")
    worst_checker = max(checker_colors, key=source_luminance)
    minimum = min(ratio(fg, worst_checker) for fg in text_colors)
    if minimum + 1e-10 < 4.5:
        raise ValueError(
            f"source SDL root identity contrast {minimum:.3f}:1 below 4.5:1")
    return {
        "source_root_contrast_verified": True,
        "identity_text_pixels": text_count,
        "checker_pixels": bg_count,
        "identity_rgb": [list(c) for c in sorted(text_colors)],
        "worst_checker_rgb": list(worst_checker),
        "minimum_contrast_ratio": round(minimum, 3),
        "native_source": [source_w, source_h],
        "native_output": [width, height],
        "png_sha256": receipt["png_sha256"],
        "exe_sha256": receipt["exe_sha256"],
        "visual_approved": False,
        "hardware_approved": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--png", type=Path, required=True)
    ap.add_argument("--p7", type=Path, required=True)
    ap.add_argument("--native-log", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    result = verify_capture(json.loads(args.receipt.read_text()),
                            args.png, args.p7, args.native_log)
    output = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.write_text(output)
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
