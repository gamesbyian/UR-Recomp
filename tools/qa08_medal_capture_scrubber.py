#!/usr/bin/env python3
"""Offline QA08 registered 2014/native result-medal visual scrubber.

Source image pixels are embedded ONLY in a local reviewer output; never
commit the HTML or image crops to Git. Original callback is always guest-1.
All 25 source frames must match the independent immutable archive manifests.
No source emulator, network access, host redraw, guest frame shift or ROM file.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import struct
import zipfile
import zlib
from pathlib import Path

ORIGINAL_SHA = "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
INTEGRATED_SHA = "832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727"
NATIVE_INNER_SHA = "c36fdd0238735e739219b013d25665e42a008a7827ee97631a322217c9f4f0cd"
FULL_ROUTE_CRC = "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
P7_HEADER = (b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
             b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
GUEST_FRAMES = tuple(range(4032, 5185, 48))
CROP = (184, 78, 246, 169)
MEDAL_BOX = (202, 91, 228, 154)  # fixed medal ROI, separate from scene context


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def chunk(tag: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + tag + payload +
            struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))


def rgb_png(width: int, height: int, data: bytes) -> bytes:
    """Stdlib-only lossless RGB8 source-review PNG (not a source correction)."""
    if not (0 < width <= 256 and 0 < height <= 224 and
            len(data) == width * height * 3):
        raise ValueError("invalid exact image crop dimensions or byte count")
    lines = b"".join(b"\x00" + data[y * width * 3:(y + 1) * width * 3]
                     for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(lines, 9)) + chunk(b"IEND", b""))


def read_crop(original: bytes, native: bytes,
              box: tuple[int, int, int, int] = CROP) -> tuple[bytes, bytes, bytes, int, int]:
    if len(original) != 256 * 224 * 4 or len(native) != len(P7_HEADER) + len(original):
        raise ValueError("original BGRX/native P7 exact 256x224 source shape changed")
    if not native.startswith(P7_HEADER):
        raise ValueError("actual native P7 channel order/shape changed")
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= 256 and 0 <= y0 < y1 <= 224):
        raise ValueError("review crop outside authenticated original raster")
    a, b, mask = bytearray(), bytearray(), bytearray()
    wrong, different = 0, 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            pos = (y * 256 + x) * 4
            blue, green, red, reserved = original[pos:pos + 4]
            nr, ng, nb, na = native[len(P7_HEADER) + pos:len(P7_HEADER) + pos + 4]
            if reserved != 0 or na != 0:
                raise ValueError("actual source frame fourth-channel identity changed")
            src = (red, green, blue)
            dst = (nr, ng, nb)
            mismatch = max(abs((u >> 3) - (v >> 3)) for u, v in zip(src, dst))
            wrong += mismatch > 1
            different += mismatch > 0
            a.extend(src)
            b.extend(dst)
            mask.extend((255, 56, 60) if mismatch > 1 else (25, 29, 34))
    return bytes(a), bytes(b), bytes(mask), wrong, different


def count_large_errors_in_box(heat: bytes,
                              box: tuple[int, int, int, int] = MEDAL_BOX) -> int:
    """Count red disagreement pixels inside bounded fixed medal region."""
    x0, y0, x1, y1 = CROP
    mx0, my0, mx1, my1 = box
    width, height = x1-x0, y1-y0
    if not (x0 <= mx0 < mx1 <= x1 and y0 <= my0 < my1 <= y1 and
            len(heat) == width * height * 3):
        raise ValueError("medal region is not within true source crop")
    return sum(
        heat[((y - y0) * width + (x - x0)) * 3:
             ((y - y0) * width + (x - x0)) * 3 + 3] == b"\\xff\\x38\\x3c"
        for y in range(my0, my1) for x in range(mx0, mx1)
    )


def uri(rgb: bytes, width: int, height: int) -> str:
    return "data:image/png;base64," + base64.b64encode(rgb_png(width, height, rgb)).decode("ascii")


def build(original_zip: Path, integrated_zip: Path) -> list[dict]:
    original_bytes = original_zip.read_bytes()
    integrated_bytes = integrated_zip.read_bytes()
    if sha(original_bytes) != ORIGINAL_SHA or sha(integrated_bytes) != INTEGRATED_SHA:
        raise ValueError("source-immutable original/Windows archived ZIP identities differ")
    with zipfile.ZipFile(io.BytesIO(original_bytes)) as o, \
         zipfile.ZipFile(io.BytesIO(integrated_bytes)) as w:
        if o.testzip() or w.testzip():
            raise ValueError("source ZIP member CRC failure")
        manifest = json.loads(o.read("qa08-original-2p-fullroute.json"))
        report = json.loads(w.read("qa08-premath-full263-ab.json"))
        embedded = w.read("qa08-premath-source-images.zip")
        if (manifest["actual_callbacks_captured"] != 263 or
            report["all_263_full_logical_256x224_source_frames"] != 263 or
            report["native_actual_5484_guest_CRC_SHA256"] != FULL_ROUTE_CRC or
            sha(embedded) != NATIVE_INNER_SHA):
            raise ValueError("authentic complete source or guest identity drift")
        original_index = {
            x["real_original_snes9x_callback_frame"]: x
            for x in manifest["each_authentic_callback"]
        }
        native_index = {x["guest"]: x for x in report["per_frame"]}
        if len(original_index) != 263 or len(native_index) != 263:
            raise ValueError("duplicate original or native frame labels")
        with zipfile.ZipFile(io.BytesIO(embedded)) as n:
            if n.testzip():
                raise ValueError("native source-image member CRC failure")
            rows = []
            x0, y0, x1, y1 = CROP
            width, height = x1 - x0, y1 - y0
            for guest in GUEST_FRAMES:
                original_frame = guest - 1
                original_info = original_index.get(original_frame)
                native_info = native_index.get(guest)
                if (not original_info or not native_info or
                    original_info["original_1based_frame"] != guest or
                    native_info["original_callback"] != original_frame):
                    raise ValueError("native guest f vs authentic original callback f-1 registration lost")
                source = o.read(f"frames/frame_{original_frame:06}_256x224.raw")
                native = n.read(f"source/ur-baldosa-original-source-{guest:06}.pam")
                if (sha(source) != original_info["original_unchanged_BGRX_sha256"] or
                    sha(native) != native_info["experimental_P7_sha256"]):
                    raise ValueError("source-original or native image SHA does not match manifest")
                a, b, delta, large, any_rgb5 = read_crop(source, native)
                rows.append({
                    "guest": guest, "original": original_frame,
                    "large": large, "medal_large": count_large_errors_in_box(delta),
                    "any_rgb5": any_rgb5,
                    "original_png": uri(a, width, height),
                    "native_png": uri(b, width, height),
                    "difference_png": uri(delta, width, height)
                })
    if (len(rows) != 25 or rows[0]["large"] != 287 or
        rows[0]["medal_large"] != 287 or
        any(row["medal_large"] < 287 for row in rows)):
        raise ValueError("true source medial region residual mismatch changed")
    return rows


HTML = r"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UR QA08 | Authentic medal source comparison</title>
<style>
:root{font-family:system-ui,sans-serif;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:#10131c;color:#eef1fa}
main{max-width:1120px;margin:auto;padding:28px 16px}
h1{font-size:clamp(1.4rem,3vw,2rem);margin:0 0 12px}
p{color:#b6c0d4;line-height:1.55}
.panel{background:#1b2333;border:1px solid #43516b;border-radius:12px;padding:14px}
.row{display:flex;flex-wrap:wrap;align-items:center;gap:12px}
input{width:100%;accent-color:#9bbfff}
button{font:inherit;background:#32445e;color:white;border:1px solid #8695ac;border-radius:8px;padding:8px 14px;cursor:pointer}
.images{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:18px}
figure{min-width:0;margin:0}figcaption{text-align:center;font-weight:600;margin:0 0 10px}
figure img{display:block;margin:auto;width:100%;max-width:260px;aspect-ratio:62/91;image-rendering:pixelated;border:1px solid #6c7790}
.stat{background:#29354a;border-radius:6px;padding:7px 10px;font-variant-numeric:tabular-nums}
@media(max-width:700px){main{padding:12px 6px}.images{gap:5px}figure.panel{padding:6px}figcaption{font-size:.74rem}}
</style><main>
<h1>Uniracers QA08 · Medal timing review</h1>
<p>25 genuine 2014 original and compiled native Windows source captures, sampled every 48 guest frames.
<strong>Original video callback f−1</strong> is paired only with <strong>native guest frame f</strong>.
Red shows any RGB5 channel more than one step different. No frame shifts, recolouring or synthesized pixels. Context and fixed medal ROI counts are kept separate.</p>
<div class="panel"><div class="row"><button id="prev" type="button">← Previous</button>
<button id="next" type="button">Next →</button><span id="position" class="stat"></span></div>
<label for="slider"><p>Guest field <strong id="guest"></strong></p></label>
<input type="range" id="slider" min="0" max="24" step="1" value="0">
<div class="row"><span class="stat" id="pair"></span><span id="large" class="stat"></span>
<span class="stat" id="any"></span><span class="stat" id="medal"></span></div></div>
<div class="images"><figure class="panel"><figcaption>2014 original callback</figcaption>
<img id="original" alt="Correct registered original source pixel crop" width="62" height="91"></figure>
<figure class="panel"><figcaption>Native Windows PPU</figcaption>
<img id="native" alt="Compiled native source pixel crop" width="62" height="91"></figure>
<figure class="panel"><figcaption>RGB5 large-error mask</figcaption>
<img id="diff" alt="Red RGB5 mismatching region" width="62" height="91"></figure></div>
<p>Source crop x184–245, y78–168 in unchanged 256×224 images. This diagnostic does
not establish common original/native consumed input or beam time, a complete USA
event, shipping UHD output, or approval for any sprite-frame offset.</p>
<details><summary>Immutable sources</summary><p><small>
Original 2014 source SHA256: __ORIGINAL__<br>Native integrated observer outer SHA256:
__NATIVE__<br>Native source-image nested ZIP SHA256: __INNER__.
Images are embedded in this local generated file and MUST NOT be committed to Git.</small></p></details>
</main><script>"use strict";const frames=__ROWS__;
const $=x=>document.getElementById(x);const slider=$("slider");
function display(index){const i=Math.max(0,Math.min(frames.length-1,Number(index))),f=frames[i];slider.value=i;
$("position").textContent="Capture "+(i+1)+" / "+frames.length;
$("guest").textContent=f.guest;$("pair").textContent="Original "+f.original+" ↔ native "+f.guest;
$("large").textContent=f.large+" large-error pixels in crop";
$("medal").textContent=f.medal_large+" within medal 26×63 region";
$("any").textContent=f.any_rgb5+" any RGB5 difference";
$("original").src=f.original_png;$("native").src=f.native_png;$("diff").src=f.difference_png;
$("prev").disabled=i===0;$("next").disabled=i===frames.length-1}
slider.addEventListener("input",()=>display(slider.value));
$("prev").addEventListener("click",()=>display(Number(slider.value)-1));
$("next").addEventListener("click",()=>display(Number(slider.value)+1));
display(0);</script></html>"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original", type=Path, required=True,
                    help="private original.zip from authentic 2014 capture")
    ap.add_argument("--integrated", type=Path, required=True,
                    help="private authentic integrated Win32 263-P7 observer artifact")
    ap.add_argument("--out", type=Path, required=True,
                    help="local HTML; may embed original ROM-derived pixels")
    args = ap.parse_args()
    try:
        rows = build(args.original, args.integrated)
        html = (HTML.replace("__ROWS__", json.dumps(rows, separators=(",", ":")))
                .replace("__ORIGINAL__", ORIGINAL_SHA)
                .replace("__NATIVE__", INTEGRATED_SHA)
                .replace("__INNER__", NATIVE_INNER_SHA))
        if args.out.exists():
            raise ValueError("refusing to overwrite another local review file")
        args.out.write_text(html, encoding="utf-8")
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, UnicodeError) as exc:
        ap.exit(2, f"QA08_MEDAL_REVIEW_REFUSED: {exc}\n")
    print(f"QA08_MEDAL_LOCAL_REVIEW_OK authentic_capture_count={len(rows)} "
          f"source_shift=0 release_accepted=0 file={args.out}")


if __name__ == "__main__":
    main()
