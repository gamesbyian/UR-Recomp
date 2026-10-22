"""Archived H26 QA06 source-free whole-block-shift adversarial witness.

A nearest-neighbour block-regularity check cannot bind the actual source
pixel identity: a completely wrong source pixel assigned to every block
can retain perfect within-block uniformity. No screenshot or GPU capture.
"""
from fractions import Fraction as F
from qa06_raster_roi_reference import raster_roi


def qa06_source_free_shift_admission(block_verifier, source_mapper):
    """An entire wrong source block can pass an intra-block consistency test."""
    # Synthetic 512x448 nearest-neighbour host, Original 256x224 logical raster.
    w,h=512,448
    roi=raster_roi(256,224,w,h,horizontal_fit=F(1))
    expected=bytearray(w*h*4);shifted=bytearray(w*h*4)
    for y in range(h):
        for x in range(w):
            k=(y*w+x)*4;pos=source_mapper(roi,x,y)
            if pos is None:
                e=s=b'\x00\x00\x00\xff'
            else:
                sx,sy=pos
                e=bytes((sx%256,sy%256,(sx^sy)%256,255))
                sx2=(sx+1)%256
                s=bytes((sx2%256,sy%256,(sx2^sy)%256,255))
            expected[k:k+4]=e;shifted[k:k+4]=s
    clean=block_verifier('original',w,h,bytes(expected),matte=b'\x00\x00\x00\xff',require_opaque=True)
    bad=block_verifier('original',w,h,bytes(shifted),matte=b'\x00\x00\x00\xff',require_opaque=True)
    if not clean['distinct_source_pixels']==bad['distinct_source_pixels']==256*224:
        raise ValueError('wrong source coverage')
    changed=sum(a!=b for a,b in zip(expected,shifted))
    if not changed:raise ValueError('negative control did not change screenshot')
    return {'schema':'qa06-source-free-shift-negative/1','host':[w,h],
            'source':[256,224],'shifted_host_byte_differences':changed,
            'clean_block_consistency_passes':True,
            'wrong_one_source_pixel_shift_also_passes':True,
            'requires_independently_pinned_source_frame_for_pixel_fidelity':True,
            'physical_capture':False,'art_approval':False,'release_credit':False}
