#!/usr/bin/env python3
"""WIDE-07 independent two-checkpoint spatial-motion comparator.

Input frames must come from separately qualified original-USA and native captures.
Matching motion masks alone never proves absolute guest phase or a whole course.
"""
import argparse
import json
from pathlib import Path

def bgrx(data, width, height):
    if len(data) != width * height * 4:
        raise ValueError("ORIGINAL_FRAME_SIZE")
    return [tuple(data[i+j] for j in (2,1,0)) for i in range(0,len(data),4)]

def bmp(data, width, height):
    import struct
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError("BMP_HEADER")
    offset = struct.unpack_from("<I",data,10)[0]
    dib = struct.unpack_from("<I",data,14)[0]
    w,h,planes,bpp,compression = struct.unpack_from("<iiHHI",data,18)
    if dib < 40 or offset < 14+dib or planes != 1 or bpp != 24 or compression:
        raise ValueError("BMP_FORMAT")
    if w != width or abs(h) != height or h == 0:
        raise ValueError("BMP_DIMENSIONS")
    stride = (width*3+3)&~3
    if offset+stride*height > len(data):
        raise ValueError("BMP_TRUNCATED")
    pixels=[]
    for y in range(height):
        row = y if h < 0 else height-1-y
        start=offset+row*stride
        pixels.extend(tuple(data[i+j] for j in (2,1,0)) for i in range(start,start+width*3,3))
    return pixels

def measure(o0,o1,n0,n1):
    if not (len(o0)==len(o1)==len(n0)==len(n1)):
        raise ValueError("FRAME_LENGTH")
    original={i for i,(a,b) in enumerate(zip(o0,o1)) if a!=b}
    native={i for i,(a,b) in enumerate(zip(n0,n1)) if a!=b}
    intersection=len(original&native)
    union=len(original|native)
    return {
        "schema":"wide07-motion-mask/1",
        "pixels":len(o0),
        "original_changed":len(original),
        "native_changed":len(native),
        "intersection":intersection,
        "union":union,
        "original_only":len(original-native),
        "native_only":len(native-original),
        "jaccard":intersection/union if union else 1.0,
        "motion_masks_equal":original==native,
        "phase_equivalence_proven":False,
        "course_acceptance":0
    }

def selftest():
    a=[(0,0,0)]*4
    b=[(1,0,0),(0,0,0),(0,0,0),(0,1,0)]
    c=[(0,0,0)]*4
    d=[(0,0,1),(0,0,0),(0,0,0),(1,0,0)]
    r=measure(a,b,c,d)
    assert r["motion_masks_equal"] and r["intersection"]==2 and r["jaccard"]==1
    d[1]=(1,1,1)
    r=measure(a,b,c,d)
    assert not r["motion_masks_equal"] and r["native_only"]==1 and r["jaccard"]==2/3
    assert measure(a,a,c,c)["jaccard"]==1
    try: measure(a,b,c,d[:-1])
    except ValueError: pass
    else: raise AssertionError("SIZE_NOT_REJECTED")
    import struct
    def encode(rows,topdown):
        h=len(rows);w=len(rows[0]);stride=(w*3+3)&~3
        body=b"".join(b"".join(bytes((b,g,r)) for r,g,b in row).ljust(stride,bytes([0])) for row in (rows if topdown else reversed(rows)))
        return b"BM"+struct.pack("<IHHI",54+len(body),0,0,54)+struct.pack("<IiiHHIIiiII",40,w,-h if topdown else h,1,24,0,len(body),0,0,0,0)+body
    rows=[[(1,2,3),(4,5,6)],[(7,8,9),(10,11,12)]]
    for topdown in (True,False):
        assert bmp(encode(rows,topdown),2,2)==sum(rows,[])
    print("WIDE07_MOTION_MASK_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--original-before",type=Path)
    p.add_argument("--original-after",type=Path)
    p.add_argument("--native-before",type=Path)
    p.add_argument("--native-after",type=Path)
    p.add_argument("--width",type=int,default=256)
    p.add_argument("--height",type=int,default=224)
    p.add_argument("--json-out",type=Path)
    a=p.parse_args()
    if a.selftest:
        selftest();return
    if a.width<=0 or a.height<=0 or not all((a.original_before,a.original_after,a.native_before,a.native_after)):
        p.error("four real frame paths and positive dimensions required")
    w,h=a.width,a.height
    report=measure(bgrx(a.original_before.read_bytes(),w,h),bgrx(a.original_after.read_bytes(),w,h),bmp(a.native_before.read_bytes(),w,h),bmp(a.native_after.read_bytes(),w,h))
    output=json.dumps(report,sort_keys=True,indent=2)+"\n"
    if a.json_out:a.json_out.write_text(output)
    print(output,end="")
if __name__=="__main__":main()
