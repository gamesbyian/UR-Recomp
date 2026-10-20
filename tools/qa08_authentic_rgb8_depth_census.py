#!/usr/bin/env python3
"""Read-only QA08 RGB5-vs-RGB8 census across all 263 genuine source frames.

Historic Snes9x video callback f-1 is stored as BGRX8888 after an RGB565
framebuffer, while the separately compiled Win32 source is PAM P7 RGBA. Byte
differences do not by themselves qualify as PPU register-state errors.
All source identities and the original 890205 RGB5 error budget are pinned.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

try:
    from tools import qa08_verify_112field_grey_pixel_budget as source
except ModuleNotFoundError:
    import qa08_verify_112field_grey_pixel_budget as source

FRAMES = tuple(range(1280, 5473, 16))
WIDTH, HEIGHT = 256, 224
PIXELS = WIDTH * HEIGHT
BENCH_RGB8_WRONG = 13293424
BENCH_RGB5_EXACT_RGB8_WRONG = 12403219
BENCH_RGB8_EXACT_FRAMES = 18


def compare(original: bytes, native: bytes) -> dict:
    """Count original BGRX versus native P7 RGB, without shifts or cropping."""
    if (len(original) != PIXELS * 4 or
        len(native) != len(source.P7_HEADER) + PIXELS * 4 or
        not native.startswith(source.P7_HEADER)):
        raise ValueError("uncropped original/native raster shape or P7 header differs")
    raw = native[len(source.P7_HEADER):]
    wrong8 = wrong5 = both5_exact8_wrong = 0
    for i in range(0, len(original), 4):
        b, g, r, a = original[i:i+4]
        nr, ng, nb, na = raw[i:i+4]
        if a or na:
            raise ValueError("source pixel fourth channel not zero")
        changed8 = r != nr or g != ng or b != nb
        changed5 = (r >> 3) != (nr >> 3) or (g >> 3) != (ng >> 3) or (b >> 3) != (nb >> 3)
        wrong8 += changed8
        wrong5 += changed5
        both5_exact8_wrong += changed8 and not changed5
    if wrong8 != wrong5 + both5_exact8_wrong:
        raise ValueError("RGB5 and RGB8 mismatch sets do not conserve")
    return {
        "wrong_RGB5": wrong5,
        "wrong_RGB8": wrong8,
        "RGB5_exact_but_RGB8_different": both5_exact8_wrong,
        "exact_RGB5": PIXELS - wrong5,
        "exact_RGB8": PIXELS - wrong8,
    }


def analyze(original: Path, native: Path) -> dict:
    # The inherited full-source verifier already checks original/native
    # immutable ZIP identities, source P7 fingerprints and the 263 RGB5 baseline.
    baseline = source.verify(original, native)
    if baseline["entire_263_source_wrong_RGB5"] != 890205:
        raise ValueError("base original/native source RGB5 census changed")
    original_raw = original.read_bytes()
    native_raw = native.read_bytes()
    if (source.sha(original_raw) != source.ORIGINAL_INNER_SHA or
        source.sha(native_raw) != source.NATIVE_OUTER_SHA):
        raise ValueError("source archives changed during comparison")
    result = {
        "schema": "QA08-263frame-fullsource-RGB5-versus-RGB8-census/1",
        "original_2014_Snes9x_inner_sha256": source.ORIGINAL_INNER_SHA,
        "native_legacy_Win32_outer_sha256": source.NATIVE_OUTER_SHA,
        "native_nested_P7_sha256": source.NATIVE_INNER_SHA,
        "original_callback_to_guest_registration": "source_callback=f-1, native_guest=f",
        "total_genuine_source_frames": len(FRAMES),
        "total_source_pixel_positions": len(FRAMES)*PIXELS,
        "frame_census": [],
        "source_raw_8bit_identical_DAC_proven": False,
        "same_2014_SNESC_hardware_color_implementation_proven": False,
        "native_effective_CGRAM_causality_proven": False,
        "global_recolor_or_brightness_fix_authorized": False,
        "QA08_QA10_or_release_accepted": False,
    }
    with zipfile.ZipFile(io.BytesIO(original_raw)) as o, \
         zipfile.ZipFile(io.BytesIO(native_raw)) as outer:
        p7_inner = outer.read("qa08-premath-source-images.zip")
        if source.sha(p7_inner) != source.NATIVE_INNER_SHA:
            raise ValueError("actual native P7 image ZIP changed")
        report_raw = outer.read("qa08-premath-full263-ab.json")
        if source.sha(report_raw) != source.NATIVE_REPORT_SHA:
            raise ValueError("actual native 263-source comparison report changed")
        report = json.loads(report_raw)
        reported = report["per_frame"]
        if [row["guest"] for row in reported] != list(FRAMES):
            raise ValueError("historical 263-frame source registration changed")
        with zipfile.ZipFile(io.BytesIO(p7_inner)) as n:
            for guest, recorded in zip(FRAMES, reported):
                a = o.read(f"frames/frame_{guest-1:06}_256x224.raw")
                b = n.read(f"source/ur-baldosa-original-source-{guest:06}.pam")
                if source.sha(b) != recorded["experimental_P7_sha256"]:
                    raise ValueError("native frame member source SHA mismatch")
                row = compare(a,b)
                if row["wrong_RGB5"] != recorded["experimental_wrong"]:
                    raise ValueError("original/native 263-frame RGB5 census disagrees")
                result["frame_census"].append({
                    "native_guest": guest, "original_callback": guest-1, **row,
                })
    rows = result["frame_census"]
    result["wrong_RGB5_positions"] = sum(r["wrong_RGB5"] for r in rows)
    result["wrong_RGB8_positions"] = sum(r["wrong_RGB8"] for r in rows)
    result["RGB5_exact_but_RGB8_different"] = sum(
        r["RGB5_exact_but_RGB8_different"] for r in rows)
    result["RGB5_exact_frames"] = sum(r["wrong_RGB5"]==0 for r in rows)
    result["RGB8_exact_frames"] = sum(r["wrong_RGB8"]==0 for r in rows)
    result["both_precision_exact_pixel_positions"] = sum(r["exact_RGB8"] for r in rows)
    if (result["wrong_RGB5_positions"] != 890205 or
        result["wrong_RGB8_positions"] != BENCH_RGB8_WRONG or
        result["RGB5_exact_but_RGB8_different"] != BENCH_RGB5_EXACT_RGB8_WRONG or
        result["RGB5_exact_frames"] != 132 or
        result["RGB8_exact_frames"] != BENCH_RGB8_EXACT_FRAMES or
        result["wrong_RGB8_positions"] !=
        result["wrong_RGB5_positions"] + result["RGB5_exact_but_RGB8_different"]):
        raise ValueError("RGB8 source census does not match original reference")
    return result


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-inner",type=Path,required=True)
    p.add_argument("--native-outer",type=Path,required=True)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    try:
        result=analyze(a.original_inner,a.native_outer)
        payload=json.dumps(result,sort_keys=True,indent=2)+"\n"
        if a.out:
            if a.out.exists():
                raise ValueError("refuse replacing prior source receipt")
            a.out.write_text(payload,encoding="utf-8")
        else:
            print(payload)
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:
        p.exit(2,"QA08_FULL_RGB8_SOURCE_REFUSED: "+str(exc)+"\n")
    print("QA08_FULL_RGB8_SOURCE_ONLY no_recolour=1 QA10_release=HOLD")


if __name__=="__main__":
    main()
