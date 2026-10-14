#!/usr/bin/env python3
"""Regenerate a source-hash-bound Original Uniracers 2P / title reference sheet.

Only real original native PPU P7 RGBAs; no new artwork or inferred 3D model.
Uses an already accepted Baldosa AOT artifact ZIP. Output HTML embeds exact
lossless PNGs and annotates the 7:6 SNES pixel aspect and any CSS-only exposure.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import zipfile

try:
    from tools.export_native_racer_obj_source_reference import lossless_png
except ModuleNotFoundError:
    from export_native_racer_obj_source_reference import lossless_png


TITLE = ("baldosa-fixed-source/ur-baldosa-original-source-000400.pam",
         256, 224, "5b09079636c80f42daf6c4765db4e930374b55c13d820857d733944e1f4872d2")
RACE = ("baldosa-ws342-captures/ur-baldosa-ws342-002208.pam",
        342, 224, "f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a")
SLOTS = {
    98: (317, "de587f5986b30663f0178a0140e746b84e601716941bb09dacab5426e8d56fe2"),
    99: (313, "836da1c261ce6ea07cc9a7a66f5a4443e494388e07cefb6da232a4b98764b564"),
    96: (313, "658d79c05524ca40af81f92ce6bb0d49adbe6bbcbc07d599e7e8bcdbdd1eb580"),
    97: (317, "e9e924050ad5da46f24d4be4b3f587e80c80c8bb04bec19014e38cf06c0e5b44"),
}


def header(width: int, height: int) -> bytes:
    return (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\n"
            "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")


def read_exact(z: zipfile.ZipFile, path: str, w: int, h: int, sha: str) -> bytes:
    info = z.getinfo(path)
    hdr = header(w, h)
    if info.file_size != len(hdr) + w * h * 4:
        raise ValueError("unexpected native PPU source image byte size: " + path)
    content = z.read(info)
    if not content.startswith(hdr):
        raise ValueError("not the exact expected original P7 image: " + path)
    rgba = content[len(hdr):]
    if hashlib.sha256(rgba).hexdigest() != sha:
        raise ValueError("native original PPU source SHA mismatch: " + path)
    return rgba


def source_crop(rgba: bytes, width: int, height: int) -> tuple[bytes, list[int], int]:
    coords = [(n // 4 % width, n // 4 // width)
              for n in range(3, len(rgba), 4) if rgba[n]]
    if not coords:
        raise ValueError("empty original racer alpha source")
    left, top = max(0, min(x for x, _ in coords) - 5), max(0, min(y for _, y in coords) - 5)
    right = min(width - 1, max(x for x, _ in coords) + 5)
    bottom = min(height - 1, max(y for _, y in coords) + 5)
    crop = b"".join(rgba[4 * (y * width + left):4 * (y * width + right + 1)]
                    for y in range(top, bottom + 1))
    return crop, [left, top, right, bottom], len(coords)


def display_rgba(rgba: bytes, w: int, h: int, scale: int,
                 css: str = "") -> str:
    # The PNG source is unmodified. The SNES's 7:6 PAR affects display width.
    encoded = base64.b64encode(lossless_png(rgba, w, h)).decode("ascii")
    width = round(w * scale * 7 / 6)
    return (f'<img width="{width}" height="{h * scale}" '
            f'style="image-rendering:pixelated;{css}" '
            f'src="data:image/png;base64,{encoded}" '
            f'alt="Hash-verified original PPU source in 7:6 PAR">')


def build(artifact: Path, output: Path) -> dict:
    with zipfile.ZipFile(artifact) as z:
        title = read_exact(z, *TITLE)
        race = read_exact(z, *RACE)
        panels = [
            ("Unmodified original title frame 400 (dark fade)",
             display_rgba(title, 256, 224, 2)),
            ("Title fade, CSS-only exposure x4 (NOT original colours)",
             display_rgba(title, 256, 224, 2, "filter:brightness(4);")),
            ("Original native split 2P frame 2208, 342x224",
             display_rgba(race, 342, 224, 2)),
        ]
        slot_meta = {}
        for slot in (98, 99, 96, 97):
            opaque, digest = SLOTS[slot]
            name = ("baldosa-ws342-obj-slots/"
                    f"ur-baldosa-ws342-obj-slot{slot}-frame002208.pam")
            rgba = read_exact(z, name, 342, 224, digest)
            crop, bounds, count = source_crop(rgba, 342, 224)
            if count != opaque:
                raise ValueError(f"source slot{slot} alpha count differs from real native report")
            w, h = bounds[2] - bounds[0] + 1, bounds[3] - bounds[1] + 1
            panels.append((f"Isolated source OBJ slot{slot}: {count} alpha pixels, crop {bounds}",
                           display_rgba(crop, w, h, 9)))
            slot_meta[str(slot)] = {
                "native_source_path": name, "raw_rgba_sha256": digest,
                "opaque_original_pixels": count,
                "crop_native_xyxy_inclusive": bounds,
                "crop_rgba_sha256": hashlib.sha256(crop).hexdigest(),
            }
    title_max = max(title[i] for i in range(len(title)) if i % 4 != 3)
    if title_max > 64:
        raise ValueError("title not the accepted dark fade; do not label exposure as original")
    cards = "".join(
        '<section><h2>' + html.escape(label) + '</h2><div class="image">' + picture +
        '</div></section>' for label, picture in panels
    )
    page = (
        '<!DOCTYPE html><html lang="en"><meta charset="utf-8">'
        '<title>Original Uniracers racer reference audit</title>'
        '<style>body{background:#161a22;color:#eee;font:15px system-ui;margin:24px}'
        'main{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:14px}'
        'section{background:#29313c;padding:12px;border:1px solid #506070;border-radius:8px}'
        'h2{font-size:15px}.image{overflow:auto;text-align:center}'
        '.image img{max-width:100%;height:auto;image-rendering:pixelated}'
        'p{max-width:980px;line-height:1.5}</style>'
        '<h1>Uniracers: original title and racer source evidence</h1>'
        '<p>Immutable original native USA PPU images, frames 400 and 2208. '
        'All PNG payloads preserve exact RGBA; browser rendering corrects the '
        'SNES 7:6 pixel aspect. CSS exposure is separately labelled and never '
        'changes source colours. Isolated OAM alpha does not establish final '
        'PPU ownership, wheel anatomy, 3D rig or HD likeness approval.</p>'
        '<main>' + cards + '</main></html>'
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    report = {
        "schema": "qa08-original-title-2p-source-reference-sheet/1",
        "input_archive_name": artifact.name,
        "guest_title_frame": 400, "guest_2p_frame": 2208,
        "title_RGBA_SHA256": TITLE[3], "title_max_original_RGB8": title_max,
        "race_RGBA_SHA256": RACE[3], "SNES_pixel_aspect_ratio": "7:6",
        "CSS_title_exposure_does_not_modify_original_image": True,
        "physical_PPU_source_winner_proven": False,
        "HD_character_likeness_approved": False,
        "isolated_source_slots": slot_meta,
    }
    output.with_suffix(".json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    report = build(args.artifact, args.out)
    print("QA08_ORIGINAL_SOURCE_REFERENCE_SHEET_ACCEPTED "
          f"guest_title={report['guest_title_frame']} "
          f"guest_2p={report['guest_2p_frame']} "
          "source_planes=4 original_colors_unchanged=1 art_approved=0")


if __name__ == "__main__":
    main()
