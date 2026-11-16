#!/usr/bin/env python3
"""WIDE-07 fail-closed motion witness for genuine 256x224 original BGRX/native BMP captures."""
import argparse
import json
import struct
from pathlib import Path

def decode(path, width, height, native):
    data = Path(path).read_bytes()
    if not native:
        if len(data) != width * height * 4:
            raise ValueError("ORIGINAL_FRAME_SIZE")
        return [tuple(data[i+j] for j in (2,1,0)) for i in range(0,len(data),4)]
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError("BMP_HEADER")
    file_size = struct.unpack_from("<I",data,2)[0]
    offset = struct.unpack_from("<I",data,10)[0]
    dib = struct.unpack_from("<I",data,14)[0]
    w,h,planes,bpp,compression = struct.unpack_from("<iiHHI",data,18)
    if dib < 40 or offset < 14+dib or planes != 1 or bpp != 24 or compression != 0:
        raise ValueError("BMP_FORMAT")
    if w != width or abs(h) != height or h == 0:
        raise ValueError("BMP_DIMENSIONS")
    stride = (width*3+3)&~3
    end = offset+stride*height
    if end > len(data) or file_size != len(data):
        raise ValueError("BMP_LENGTH")
    result=[]
    for y in range(height):
        row = y if h < 0 else height-1-y
        start=offset+row*stride
        result.extend(tuple(data[i+j] for j in (2,1,0)) for i in range(start,start+width*3,3))
    return result

def measure(o0,o1,n0,n1):
    if not (len(o0)==len(o1)==len(n0)==len(n1)) or not o0:
        raise ValueError("FRAME_LENGTH")
    original={i for i,(a,b) in enumerate(zip(o0,o1)) if a!=b}
    native={i for i,(a,b) in enumerate(zip(n0,n1)) if a!=b}
    intersection=len(original&native)
    union=len(original|native)
    moving=bool(original) and bool(native)
    return {
        "schema":"wide07-motion-evidence/1",
        "pixels":len(o0),
        "original_changed":len(original),
        "native_changed":len(native),
        "intersection":intersection,
        "union":union,
        "original_only":len(original-native),
        "native_only":len(native-original),
        "jaccard":intersection/union if union else None,
        "motion_observed_in_both":moving,
        "motion_masks_equal":original==native,
        "informative_motion_match":moving and original==native,
        "phase_equivalence_proven":False,
        "course_acceptance":0
    }

def selftest():
    a=[(0,0,0)]*4
    b=[(1,0,0),(0,0,0),(0,0,0),(0,1,0)]
    c=[(0,0,0)]*4
    d=[(0,0,1),(0,0,0),(0,0,0),(1,0,0)]
    assert measure(a,b,c,d)["informative_motion_match"]
    assert not measure(a,a,c,c)["informative_motion_match"]
    assert measure(a,a,c,c)["jaccard"] is None
    assert not measure(a,b,c,c)["informative_motion_match"]
    d[1]=(1,1,1)
    assert measure(a,b,c,d)["native_only"]==1
    try: measure(a,b,c,d[:-1])
    except ValueError: pass
    else: raise AssertionError("LENGTH_GUARD")
    print("WIDE07_MOTION_EVIDENCE_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    for arg in ("original-before","original-after","native-before","native-after"):
        p.add_argument("--"+arg,type=Path)
    p.add_argument("--width",type=int,default=256)
    p.add_argument("--height",type=int,default=224)
    p.add_argument("--json-out",type=Path)
    a=p.parse_args()
    if a.selftest:
        selftest();return
    paths=[a.original_before,a.original_after,a.native_before,a.native_after]
    if any(v is None for v in paths) or a.width<=0 or a.height<=0:
        p.error("four actual capture paths and positive dimensions required")
    frames=[decode(path,a.width,a.height,i>=2) for i,path in enumerate(paths)]
    output=json.dumps(measure(*frames),indent=2,sort_keys=True)+"\n"
    if a.json_out:a.json_out.write_text(output)
    print(output,end="")
if __name__=="__main__":main()
