#!/usr/bin/env python3
"""WIDE-07 transition-phase discriminator, robust to a deterministic green LUT.
This is a candidate alignment measurement, never an absolute guest-clock oracle.
"""
import argparse
import json
import struct
from pathlib import Path

def original_rgb(path, width, height):
    raw = Path(path).read_bytes()
    if len(raw) != width * height * 4:
        raise ValueError("ORIGINAL_FRAME_LENGTH")
    return bytes(v for i in range(0, len(raw), 4) for v in (raw[i+2], raw[i+1], raw[i]))

def native_rgb(path, width, height):
    raw = Path(path).read_bytes()
    if len(raw) < 54 or raw[:2] != b"BM":
        raise ValueError("BMP_HEADER")
    size, offset = struct.unpack_from("<II", raw, 2)[0], struct.unpack_from("<I", raw, 10)[0]
    dib = struct.unpack_from("<I", raw, 14)[0]
    w, h, planes, bpp, compression = struct.unpack_from("<iiHHI", raw, 18)
    stride = (width * 3 + 3) & ~3
    if (dib < 40 or offset < 14 + dib or w != width or abs(h) != height or h == 0
        or planes != 1 or bpp != 24 or compression != 0 or size != len(raw)
        or offset + stride * height > len(raw)):
        raise ValueError("BMP_FORMAT")
    return bytes(v for y in range(height) for x in range(width)
                 for v in (raw[offset + (y if h < 0 else height - 1 - y)*stride + 3*x + 2],
                           raw[offset + (y if h < 0 else height - 1 - y)*stride + 3*x + 1],
                           raw[offset + (y if h < 0 else height - 1 - y)*stride + 3*x]))

def transitions(frames):
    if len(frames) < 3 or len({len(f) for f in frames}) != 1 or len(frames[0]) % 3:
        raise ValueError("NEED_THREE_EQUAL_RGB_FRAMES")
    # Only red/blue are used; measured original/native green LUT differences cannot bias alignment.
    return [bytes(int(a[i] != b[i] or a[i+2] != b[i+2])
                  for i in range(0, len(a), 3))
            for a, b in zip(frames, frames[1:])]

def rank(original, native, max_shift=2):
    if max_shift < 0:
        raise ValueError("NEGATIVE_SHIFT")
    o, n = transitions(original), transitions(native)
    candidates = []
    for shift in range(-max_shift, max_shift + 1):
        pairs = [(i, i+shift) for i in range(len(o)) if 0 <= i+shift < len(n)]
        if len(pairs) < 2:
            continue
        intersection = union = mismatches = 0
        for i, j in pairs:
            a, b = o[i], n[j]
            intersection += sum(x & y for x,y in zip(a,b))
            union += sum(x | y for x,y in zip(a,b))
            mismatches += sum(x != y for x,y in zip(a,b))
        candidates.append(dict(shift=shift, paired_transitions=len(pairs),
                               intersection=intersection, union=union,
                               mismatches=mismatches,
                               jaccard=(intersection / union if union else None)))
    informative = [c for c in candidates if c["union"]]
    if not informative:
        return dict(schema="wide07-transition-phase/1", candidates=candidates,
                    best_shift=None, ambiguous=True, informative=False,
                    phase_equivalence_proven=False, course_acceptance=0)
    # Prefer overlap count only as a tie-breaker, not as an implicit timing assumption.
    ordered = sorted(informative, key=lambda c: (-c["jaccard"], -c["paired_transitions"], abs(c["shift"])))
    best = ordered[0]
    tied = [c for c in informative if c["jaccard"] == best["jaccard"]]
    return dict(schema="wide07-transition-phase/1", candidates=candidates,
                best_shift=best["shift"], ambiguous=len(tied) != 1,
                informative=True, phase_equivalence_proven=False, course_acceptance=0)

def selftest():
    def f(k, green=10):
        return bytes((k,green,k+1, k+2,green,k+3))
    o = [f(k) for k in (0, 4, 12, 18, 27)]
    n = [f(99, 200)] + [f(k, 240) for k in (0,4,12,18,27)]
    r = rank(o,n)
    assert r["best_shift"] == 1 and not r["ambiguous"] and r["informative"], r
    static = rank([f(0)]*4, [f(0,200)]*4)
    assert not static["informative"] and static["best_shift"] is None
    assert rank(o,o)["best_shift"] == 0
    try: transitions([b"abc",b"abc"])
    except ValueError: pass
    else: raise AssertionError("SHORT_SEQUENCE_ACCEPTED")
    print("WIDE07_TRANSITION_PHASE_SELFTEST_PASS")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--original", nargs="+", type=Path)
    p.add_argument("--native", nargs="+", type=Path)
    p.add_argument("--width", type=int, default=256)
    p.add_argument("--height", type=int, default=224)
    p.add_argument("--max-shift", type=int, default=2)
    p.add_argument("--json-out", type=Path)
    a = p.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.original or not a.native or a.width < 1 or a.height < 1:
        p.error("ordered original/native frames and positive dimensions required")
    report = rank([original_rgb(f,a.width,a.height) for f in a.original],
                  [native_rgb(f,a.width,a.height) for f in a.native], a.max_shift)
    output = json.dumps(report,indent=2,sort_keys=True)+"\n"
    if a.json_out:
        a.json_out.write_text(output)
    print(output,end="")

if __name__ == "__main__":
    main()
