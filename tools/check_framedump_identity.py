#!/usr/bin/env python3
"""Check that two native runs of one route are bit-identical frame by frame.

The 4:3 regression gate: the shipping product with Widescreen off must leave
the authentic path untouched. A baseline built from the same generated
program without the Widescreen presentation layer and product host, and the
product in Original view, run the same deterministic route; every per-frame
framebuffer and WRAM image and every retained script dump must be identical.

Inputs are `--framedump` directories (frame_NNNNNN.{bmp,json,_wram.bin}) and,
optionally, `SNESRECOMP_DUMP_DIR` checkpoint directories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any

try:
    from tools.evidence_contract import assertion, make_envelope
except ModuleNotFoundError:
    from evidence_contract import assertion, make_envelope

FRAME_RE = re.compile(r"^frame_(\d{6})")


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _bmp_digest_outside_rect(path: Path, rect: tuple[int, int, int, int]) -> str:
    data = bytearray(path.read_bytes())
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError(f"not a BMP: {path}")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    height_raw = struct.unpack_from("<i", data, 22)[0]
    bpp = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    if width <= 0 or height_raw == 0 or bpp not in (24, 32) or compression != 0:
        raise ValueError(f"unsupported BMP layout: {path}")
    height = abs(height_raw)
    bytes_per_pixel = bpp // 8
    row_stride = ((width * bytes_per_pixel + 3) // 4) * 4
    if pixel_offset + row_stride * height > len(data):
        raise ValueError(f"truncated BMP pixels: {path}")

    x, y, w, h = rect
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(width, x + max(0, w))
    y1 = min(height, y + max(0, h))
    for logical_y in range(y0, y1):
        stored_y = logical_y if height_raw < 0 else height - 1 - logical_y
        start = pixel_offset + stored_y * row_stride + x0 * bytes_per_pixel
        end = pixel_offset + stored_y * row_stride + x1 * bytes_per_pixel
        data[start:end] = b"\x00" * (end - start)
    return hashlib.sha256(data).hexdigest()


def _files(root: Path) -> dict[str, Path]:
    return {p.name: p for p in sorted(root.iterdir()) if p.is_file()}


def compare_dirs(
    baseline: Path,
    candidate: Path,
    allowed_bmp_rect: tuple[int, int, int, int] | None = None,
) -> dict[str, Any]:
    a = _files(baseline)
    b = _files(candidate)
    common = sorted(set(a) & set(b))
    differing = []
    masked_bmp_files = 0
    for name in common:
        if allowed_bmp_rect is not None and name.lower().endswith(".bmp"):
            masked_bmp_files += 1
            same = (
                _bmp_digest_outside_rect(a[name], allowed_bmp_rect)
                == _bmp_digest_outside_rect(b[name], allowed_bmp_rect)
            )
        else:
            same = _digest(a[name]) == _digest(b[name])
        if not same:
            differing.append(name)
    frames = {int(m.group(1)) for name in common if (m := FRAME_RE.match(name))}
    first_frame = None
    for name in differing:
        m = FRAME_RE.match(name)
        if m and (first_frame is None or int(m.group(1)) < first_frame):
            first_frame = int(m.group(1))
    return {
        "files_compared": len(common),
        "frames_compared": len(frames),
        "only_in_baseline": sorted(set(a) - set(b))[:16],
        "only_in_candidate": sorted(set(b) - set(a))[:16],
        "differing_files": len(differing),
        "first_differing": differing[:16],
        "first_differing_frame": first_frame,
        "allowed_bmp_rect": list(allowed_bmp_rect) if allowed_bmp_rect else None,
        "masked_bmp_files": masked_bmp_files,
    }


def check(
    route: str,
    frames: tuple[Path, Path],
    dumps: tuple[Path, Path] | None,
    min_frames: int,
    allowed_bmp_rect: tuple[int, int, int, int] | None = None,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "frames": compare_dirs(*frames, allowed_bmp_rect=allowed_bmp_rect)
    }
    f = metrics["frames"]
    checks = [
        assertion(f"{route}-frame-coverage", f["frames_compared"] >= min_frames,
                  {"frames_compared": f["frames_compared"], "min_frames": min_frames}),
        assertion(f"{route}-same-frame-set",
                  not f["only_in_baseline"] and not f["only_in_candidate"],
                  {"only_in_baseline": f["only_in_baseline"],
                   "only_in_candidate": f["only_in_candidate"]}),
        assertion(f"{route}-frames-bit-identical", f["differing_files"] == 0,
                  {"differing_files": f["differing_files"],
                   "first_differing": f["first_differing"],
                   "first_differing_frame": f["first_differing_frame"]}),
    ]
    if dumps is not None:
        d = metrics["dumps"] = compare_dirs(*dumps)
        checks.append(assertion(
            f"{route}-dumps-bit-identical",
            d["files_compared"] > 0 and d["differing_files"] == 0
            and not d["only_in_baseline"] and not d["only_in_candidate"],
            {k: d[k] for k in ("files_compared", "differing_files", "first_differing",
                               "only_in_baseline", "only_in_candidate")},
        ))
    return make_envelope(
        evidence_type="framedump-identity",
        producer="tools/check_framedump_identity.py",
        subject={"route": route},
        inputs={
            "min_frames": min_frames,
            "allowed_bmp_rect": list(allowed_bmp_rect) if allowed_bmp_rect else None,
        },
        metrics=metrics,
        assertions=checks,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", required=True)
    parser.add_argument("--baseline-frames", required=True, type=Path)
    parser.add_argument("--candidate-frames", required=True, type=Path)
    parser.add_argument("--baseline-dumps", type=Path)
    parser.add_argument("--candidate-dumps", type=Path)
    parser.add_argument("--min-frames", type=int, default=1)
    parser.add_argument(
        "--allow-bmp-overlay-rect",
        metavar="X,Y,W,H",
        help="ignore framebuffer pixel differences only inside this host-owned BMP rectangle",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if (args.baseline_dumps is None) != (args.candidate_dumps is None):
        parser.error("--baseline-dumps and --candidate-dumps go together")
    allowed_bmp_rect = None
    if args.allow_bmp_overlay_rect:
        try:
            values = tuple(int(part) for part in args.allow_bmp_overlay_rect.split(","))
        except ValueError:
            parser.error("--allow-bmp-overlay-rect must be X,Y,W,H integers")
        if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
            parser.error("--allow-bmp-overlay-rect must be X,Y,W,H with positive W,H")
        allowed_bmp_rect = values

    dumps = (args.baseline_dumps, args.candidate_dumps) if args.baseline_dumps else None
    envelope = check(
        args.route,
        (args.baseline_frames, args.candidate_frames),
        dumps,
        args.min_frames,
        allowed_bmp_rect,
    )
    rendered = json.dumps(envelope, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0 if envelope["outcome"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
