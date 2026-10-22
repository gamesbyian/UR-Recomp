"""Memory-bounded nearest-neighbour source/host coverage certificate (synthetic)."""
from fractions import Fraction as F
from qa06_raster_roi_reference import raster_roi,source_pixel_host_span,source_pixel_at_output_centre
MODES={'original':(256,224,F(1)),'world342':(342,224,F(512,513))}
def certify(mode,host_w,host_h):
    if type(mode) is not str or mode not in MODES:
        raise ValueError('unknown presentation mode')
    if any(type(v) is not int or not 1<=v<=16384 for v in (host_w,host_h)):
        raise ValueError('invalid host dimensions')
    sw,sh,fit=MODES[mode]
    roi=raster_roi(sw,sh,host_w,host_h,horizontal_fit=fit)
    x,y,w,h=roi['roi_xywh']
    def axis(src,out):
        intervals=[source_pixel_host_span(src,out,j) for j in range(src)]
        if intervals[0][0]!=0 or intervals[-1][1]!=out or any(a[1]!=b[0] for a,b in zip(intervals,intervals[1:])):
            raise ValueError('source-to-host intervals leave gaps or overlap')
        if out>=src and any(b<=a for a,b in intervals):
            raise ValueError('host scale omitted a source coordinate')
        for j,(a,b) in enumerate(intervals):
            if a<b and (source_pixel_at_output_centre(src,out,a)!=j or source_pixel_at_output_centre(src,out,b-1)!=j):
                raise ValueError('inverse nearest-neighbour boundary contradiction')
        return len([1 for a,b in intervals if a<b])
    cx,cy=axis(sw,w),axis(sh,h)
    return {'schema':'ur-qa06-geometry-span-certificate/1','mode':mode,'host':[host_w,host_h],
            'source':[sw,sh],'roi_xywh':[x,y,w,h],
            'source_columns_observed':cx,'source_rows_observed':cy,
            'all_224_rows_present':cy==224,'full_source_coverage':cx==sw and cy==sh,
            'left_right_mattes':[x,host_w-x-w],
            'top_bottom_mattes':[y,host_h-y-h],
            'physical_gpu_accepted':False,'character_art_approved':False,'release_gate_credit':0}
