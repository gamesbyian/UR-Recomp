#!/usr/bin/env python3
"""QA08 source-authenticated 112-field grayscale pixel budget, read-only.

Use only 2014 Snes9x callback f-1 and genuine integrated Win32 PPU guest f.
RGB5 pixel counting is *diagnostic*, never a permission to rewrite output
colours, shift the video, promote premath #1807 or accept QA08/release.
No emulator builds, guest changes, PNG or ROM-derived pixels emitted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import zipfile

ORIGINAL_INNER_SHA = "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
NATIVE_OUTER_SHA = "832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727"
NATIVE_INNER_SHA = "c36fdd0238735e739219b013d25665e42a008a7827ee97631a322217c9f4f0cd"
NATIVE_REPORT_SHA = "71afe4439a361706d159afe203b67a63845a93866eaeb48bd018adcc3636881d"
NATIVE_CRC_SHA = "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
P7_HEADER = (b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
             b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
SPIKES = tuple(range(4064, 5409, 112))
CYCLE = ((15, 20), (16, 15), (17, 16), (20, 17))
FRAME_PIXELS = 256 * 224

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def measure_frame(original: bytes, native: bytes) -> tuple[int, int, int, Counter]:
    """Compare all genuine visible source RGB5 pixels; both fourth bytes must be zero."""
    if len(original) != FRAME_PIXELS*4 or len(native) != len(P7_HEADER)+len(original):
        raise ValueError("source 256x224 full-raster byte shape changed")
    if not native.startswith(P7_HEADER):
        raise ValueError("source/native P7 channel order changed")
    wrong = gray_both = cycle = 0
    kinds: Counter = Counter()
    for pos in range(0, FRAME_PIXELS*4, 4):
        b, g, r, reserved = original[pos:pos+4]
        nr, ng, nb, alpha = native[len(P7_HEADER)+pos:len(P7_HEADER)+pos+4]
        if reserved != 0 or alpha != 0:
            raise ValueError("source archived fourth channel changed")
        o = (r>>3, g>>3, b>>3)
        n = (nr>>3, ng>>3, nb>>3)
        if o == n:
            continue
        wrong += 1
        if o[0] == o[1] == o[2] and n[0] == n[1] == n[2]:
            gray_both += 1
            kinds[(o[0],n[0])] += 1
            if (o[0], n[0]) in CYCLE:
                cycle += 1
    return wrong, gray_both, cycle, kinds

def verify(original_path: Path, native_path: Path) -> dict:
    if sha(original_path.read_bytes()) != ORIGINAL_INNER_SHA:
        raise ValueError("2014 original inner archive identity changed")
    if sha(native_path.read_bytes()) != NATIVE_OUTER_SHA:
        raise ValueError("genuine integrated Windows source archive identity changed")
    with zipfile.ZipFile(original_path) as original, zipfile.ZipFile(native_path) as outer:
        if original.testzip() or outer.testzip():
            raise ValueError("source ZIP CRC changed")
        original_manifest = json.loads(original.read("qa08-original-2p-fullroute.json"))
        report_blob = outer.read("qa08-premath-full263-ab.json")
        if sha(report_blob) != NATIVE_REPORT_SHA:
            raise ValueError("original/native complete PPU report SHA changed")
        report = json.loads(report_blob)
        native_blob = outer.read("qa08-premath-source-images.zip")
        if sha(native_blob) != NATIVE_INNER_SHA:
            raise ValueError("actual Windows nested source images changed")
        if (original_manifest["actual_callbacks_captured"] != 263 or
            report["all_263_full_logical_256x224_source_frames"] != 263 or
            report["native_actual_5484_guest_CRC_SHA256"] != NATIVE_CRC_SHA or
            report["baseline_wrong_RGB5"] != 890205 or
            report["experimental_wrong_RGB5"] != 890205 or
            report["corrected_real_pixels"] != 0 or
            report["newly_wrong_real_pixels"] != 0):
            raise ValueError("authenticated baseline or guest route changed")
        oi = {e["real_original_snes9x_callback_frame"]: e
              for e in original_manifest["each_authentic_callback"]}
        ni = {e["guest"]:e for e in report["per_frame"]}
        if len(oi) != 263 or len(ni) != 263:
            raise ValueError("original/native callback labels duplicated")
        frames = []
        aggregate = Counter()
        with zipfile.ZipFile(io.BytesIO(native_blob)) as source:
            if source.testzip():
                raise ValueError("nested original PPU capture CRC changed")
            for f in SPIKES:
                callback = f-1
                oref, nref = oi.get(callback),ni.get(f)
                if (not oref or not nref or
                    oref["original_1based_frame"] != f or
                    nref["original_callback"] != callback):
                    raise ValueError("original video f-1/native guest f alignment changed")
                o = original.read(f"frames/frame_{callback:06}_256x224.raw")
                n = source.read(f"source/ur-baldosa-original-source-{f:06}.pam")
                if sha(o) != oref["original_unchanged_BGRX_sha256"] or sha(n) != nref["experimental_P7_sha256"]:
                    raise ValueError("one of the genuine source frame member SHAs changed")
                wrong,gray,cycle,kinds = measure_frame(o,n)
                if wrong != nref["experimental_wrong"] or wrong < 20000 or cycle < 20000:
                    raise ValueError("one source grayscale-cycle field lost its independently observed census")
                aggregate.update(kinds)
                frames.append({"native_guest": f, "original_callback": callback,
                               "total_wrong_rgb5": wrong,
                               "gray_to_gray_wrong_rgb5": gray,
                               "four_cycle_wrong_rgb5": cycle})
    total_wrong = sum(x["total_wrong_rgb5"] for x in frames)
    gray_wrong = sum(x["gray_to_gray_wrong_rgb5"] for x in frames)
    cycle_wrong = sum(x["four_cycle_wrong_rgb5"] for x in frames)
    counts = {f"{a}->{b}":aggregate[(a,b)] for a,b in CYCLE}
    if (len(frames),total_wrong,gray_wrong,cycle_wrong,counts) != (
        13,359013,342086,318775,
        {"15->20":53658,"16->15":107868,"17->16":52716,"20->17":104533}
    ):
        raise ValueError("authentic 13-field grayscale-source budget no longer matches receipt")
    return {
        "schema":"QA08-2014-native-112-field-grayscale-pixel-budget/1",
        "original_callback_zip_sha256":ORIGINAL_INNER_SHA,
        "integrated_windows_source_zip_sha256":NATIVE_OUTER_SHA,
        "original_native_registration":"Snes9x callback f-1 vs Win32 guest f",
        "native_guest_CRC_SHA256":NATIVE_CRC_SHA,
        "entire_263_source_wrong_RGB5":890205,
        "sampled_spike_count":len(frames),
        "spike_total_wrong_RGB5":total_wrong,
        "spike_both_gray_wrong_RGB5":gray_wrong,
        "spike_four_cycle_wrong_RGB5":cycle_wrong,
        "four_cycle_wrong_RGB5_by_pair":counts,
        "four_cycle_fraction_all_errors_ppm":cycle_wrong*1000000//890205,
        "corrected_or_recoloured_source_pixels":0,
        "same_original_native_consumed_input_beam_proven":False,
        "CGRAM_ingestion_root_cause_proven":False,
        "global_palette_remap_or_video_frame_shift_authorized":False,
        "independent_graphics_or_release_acceptance":False,
        "frames":frames,
    }

def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original",type=Path,required=True,help="exact 2014 original inner ZIP")
    ap.add_argument("--native",type=Path,required=True,help="exact compiled integrated Win32 PPU outer ZIP")
    ap.add_argument("--out",type=Path,help="private JSON-only receipt, never source imagery")
    args=ap.parse_args()
    try:
        report=verify(args.original,args.native)
    except (OSError,ValueError,KeyError,UnicodeError,zipfile.BadZipFile) as e:
        ap.exit(2,"QA08_GRAY112_REFUSED: "+str(e)+"\n")
    payload=json.dumps(report,sort_keys=True,indent=2)+"\n"
    if args.out:
        if args.out.exists(): ap.exit(2,"QA08_GRAY112_REFUSED: output exists\n")
        args.out.write_text(payload,encoding="utf-8")
    else:
        print(payload)
    print("QA08_GRAY112_SOURCE_OK cycle=318775 total=890205 qa08_acceptance=0")

if __name__ == "__main__":
    main()
