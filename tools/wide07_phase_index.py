#!/usr/bin/env python3
"""Bounded WIDE-07 phase-index discriminator. No frame-time equivalence inferred."""
import argparse
import json
import struct
from pathlib import Path

def decode_original(data, width, height):
    if len(data) != width * height * 4:
        raise ValueError('ORIGINAL_BRGX_LENGTH')
    return bytes(c for i in range(0, len(data), 4) for c in (data[i+2],data[i+1],data[i]))

def decode_native(data, width, height):
    if len(data) < 54 or data[:2] != b'BM':
        raise ValueError('BMP_HEADER')
    size = struct.unpack_from('<I', data, 2)[0]
    offset = struct.unpack_from('<I', data, 10)[0]
    dib = struct.unpack_from('<I', data, 14)[0]
    w,h,planes,bpp,compression = struct.unpack_from('<iiHHI', data, 18)
    stride = (width*3+3)&~3
    if dib < 40 or offset < 14+dib or w != width or abs(h) != height or h == 0 or planes != 1 or bpp != 24 or compression != 0 or size != len(data) or offset + stride*height > len(data):
        raise ValueError('BMP_FORMAT')
    return bytes(c for y in range(height) for x in range(width) for c in (data[offset+(y if h<0 else height-1-y)*stride+x*3+2], data[offset+(y if h<0 else height-1-y)*stride+x*3+1], data[offset+(y if h<0 else height-1-y)*stride+x*3]))

def compare_sequences(original, native, max_shift=2):
    if not original or not native or max_shift < 0:
        raise ValueError("EMPTY_OR_INVALID_SEQUENCE")
    if len({len(x) for x in original + native}) != 1:
        raise ValueError("FRAME_SIZE_MISMATCH")
    candidates = []
    for shift in range(-max_shift, max_shift + 1):
        pairs = [(i, i + shift) for i in range(len(original)) if 0 <= i + shift < len(native)]
        if len(pairs) < 2:
            continue
        equal_bytes = sum(sum(a == b for a, b in zip(original[i], native[j])) for i,j in pairs)
        total = sum(len(original[i]) for i,j in pairs)
        candidates.append({"native_index_minus_original_index": shift,
                           "paired_frames": len(pairs), "equal_bytes": equal_bytes,
                           "total_bytes": total, "fraction_equal": equal_bytes / total})
    if not candidates:
        raise ValueError("NO_OVERLAP")
    ranked = sorted(candidates, key=lambda x: (-x["fraction_equal"], -x["paired_frames"], abs(x["native_index_minus_original_index"])))
    best = ranked[0]
    ties = [x for x in ranked if x["fraction_equal"] == best["fraction_equal"]]
    return {"schema":"wide07-phase-index/1", "candidates":candidates, "best_shift":best["native_index_minus_original_index"],
            "ambiguous":len(ties)>1, "phase_equivalence_proven":False, "course_acceptance":0}

def selftest():
    frames = [bytes([i]*8) for i in range(5)]
    report = compare_sequences(frames, [b"\xff"*8] + frames)
    assert report["best_shift"] == 1 and not report["ambiguous"]
    assert compare_sequences(frames, frames)["best_shift"] == 0
    static = compare_sequences([b"\x00"*8]*4, [b"\x00"*8]*4)
    assert static["ambiguous"] and not static["phase_equivalence_proven"]
    try: compare_sequences([b"a"], [b"aa", b"aa"])
    except ValueError: pass
    else: raise AssertionError("FRAME_SIZE_GUARD")
    print("WIDE07_PHASE_INDEX_SELFTEST_PASS")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--original", nargs="+", type=Path)
    p.add_argument("--native", nargs="+", type=Path)
    p.add_argument("--max-shift", type=int, default=2)
    p.add_argument("--width", type=int, default=256)
    p.add_argument("--height", type=int, default=224)
    p.add_argument("--json-out", type=Path)
    a = p.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.original or not a.native:
        p.error("ordered original and native frame paths required")
    if a.width <= 0 or a.height <= 0:
        p.error("positive dimensions required")
    result = compare_sequences([decode_original(x.read_bytes(), a.width, a.height) for x in a.original], [decode_native(x.read_bytes(), a.width, a.height) for x in a.native], a.max_shift)
    output = json.dumps(result, indent=2, sort_keys=True)+"\n"
    if a.json_out:
        a.json_out.write_text(output)
    print(output, end="")
if __name__ == "__main__":
    main()
