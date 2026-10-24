"""Source-free nearest-neighbour Original presentation consistency witness.

Tests whether host pixels mapping to one guest source pixel are identical. This
can detect subpixel tearing inside a nearest-neighbour block even when the
original source raster is unavailable. It cannot establish the right colour,
frame, sprite likeness, GPU output or 4K hardware acceptance.
"""
from fractions import Fraction
from qa06_raster_roi_reference import raster_roi, source_pixel_at_host_coordinate

def verify_blocks(mode, host_w, host_h, rgba, *, matte=None, require_opaque=False):
    modes={'original':(256,224,Fraction(1)), 'world342':(342,224,Fraction(512,513))}
    if type(mode) is not str or mode not in modes:raise ValueError('unknown source policy')
    if any(type(x) is not int or not 1<=x<=8192 for x in (host_w,host_h)):
        raise ValueError('invalid host dimensions')
    if type(rgba) is not bytes or len(rgba)!=host_w*host_h*4:
        raise ValueError('invalid complete RGBA host screenshot')
    if matte is not None and (type(matte) is not bytes or len(matte)!=4):
        raise ValueError('invalid matte')
    if type(require_opaque) is not bool:raise ValueError('invalid alpha policy')
    sw,sh,fit=modes[mode]
    roi=raster_roi(sw,sh,host_w,host_h,horizontal_fit=fit)
    first={};source_samples=0;matte_samples=0
    for y in range(host_h):
        for x in range(host_w):
            k=4*(y*host_w+x);pix=rgba[k:k+4]
            if require_opaque and pix[3]!=255:
                raise ValueError('transparent screenshot pixel under opaque policy')
            loc=source_pixel_at_host_coordinate(roi,x,y)
            if loc is None:
                matte_samples+=1
                if matte is None or pix!=matte:raise ValueError('matte mismatch')
            else:
                source_samples+=1
                if loc in first and first[loc]!=pix:
                    raise ValueError('inconsistent nearest-neighbour source block')
                first[loc]=pix
    return {'schema':'qa06-original-block-consistency/1','mode':mode,
            'distinct_source_pixels':len(first),'source_host_samples':source_samples,
            'matte_samples':matte_samples,'source_frame_verified':False,
            'gpu_observed':False,'art_approved':False,'release_gate_credit':0}
