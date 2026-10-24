"""Synthetic full-frame screenshot witness; never substitutes for GPU capture.

Recovered from Evidence Library archive 142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ
(h26.zip -> evidence/agent5-h25.zip -> work/agent4-h25.zip ->
h25/qa06_rgba_admission.py, 1,637 bytes, full SHA-256 verified on a runner).
Compares an RGBA host frame against the nearest-neighbour composition of an
opaque source frame plus an opaque matte using the existing span certificate and
raster ROI reference. No physical GPU, original/native, art or release credit.
"""
try:
    from .qa06_span_certificate import certify
    from .qa06_raster_roi_reference import source_pixel_at_output_centre
except ImportError:  # direct script / tests that put tools/ on sys.path
    from qa06_span_certificate import certify
    from qa06_raster_roi_reference import source_pixel_at_output_centre


def audit_rgba(mode, width, height, source_rgba, host_rgba, *, matte_rgba):
    geometry=certify(mode,width,height)
    sw,sh=geometry['source']
    if (type(source_rgba) is not bytes or len(source_rgba)!=sw*sh*4 or
        type(host_rgba) is not bytes or len(host_rgba)!=width*height*4 or
        type(matte_rgba) is not bytes or len(matte_rgba)!=4 or matte_rgba[3]!=255):
        raise ValueError('incomplete RGBA buffers or nonopaque matte')
    if any(source_rgba[i]!=255 for i in range(3,len(source_rgba),4)):
        raise ValueError('transparent source pixels cannot prove opaque composition')
    x0,y0,rw,rh=geometry['roi_xywh']
    mismatches=0
    for y in range(height):
        in_y=y0<=y<y0+rh
        sy=source_pixel_at_output_centre(sh,rh,y-y0) if in_y else 0
        for x in range(width):
            offset=4*(y*width+x)
            if in_y and x0<=x<x0+rw:
                sx=source_pixel_at_output_centre(sw,rw,x-x0)
                expected=source_rgba[4*(sy*sw+sx):4*(sy*sw+sx)+4]
            else:
                expected=matte_rgba
            if host_rgba[offset:offset+4]!=expected:
                mismatches+=1
    return {'schema':'ur-qa06-opaque-rgba-audit/1','mode':mode,'geometry':geometry,
            'pixels_examined':width*height,'pixel_mismatches':mismatches,
            'exact_rgba_match':mismatches==0,'physical_gpu_accepted':False,
            'character_art_approved':False,'release_gate_credit':0}
