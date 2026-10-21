#!/usr/bin/env python3
"""Pure rational screenshot ROI proposal, not observed physical Windows output.

Retain the entire SNES 224-row source and 7:6 pixel aspect ratio. This is a
reference to evaluate future screenshots, not a shipping-render acceptance.
"""
from fractions import Fraction as F
import json



def _sampled_coverage(source, output):
    """Exact nearest-neighbour coverage in O(1) time and memory.

    For output < source, successive floor((2*i+1)*source/(2*output))
    indices strictly increase. For output >= source, every source index
    occurs. No allocation proportional to a possibly huge host viewport.
    """
    if type(source) is not int or type(output) is not int or min(source,output)<=0:
        raise ValueError('invalid sample coverage dimensions')
    covered=min(source,output)
    return {'covered':covered,'missing':source-covered}

def source_pixel_at_output_centre(source_length, output_length, output_coordinate):
    """Return the exact native nearest source index for a viewport pixel centre.

    The output coordinate is viewport-local. Mattes are never sampled. This
    helper does not claim to observe a real Windows screenshot.
    """
    if (any(type(v) is not int for v in (source_length, output_length, output_coordinate))
            or not 0 < source_length <= 2147483647
            or not 0 < output_length <= 2147483647
            or not 0 <= output_coordinate < output_length):
        raise ValueError('invalid viewport sampling coordinate')
    return ((2*output_coordinate+1)*source_length)//(2*output_length)


def source_pixel_at_host_coordinate(roi, host_x, host_y):
    """Map an absolute host pixel centre to native nearest source; None for matte.

    This is a screenshot-review oracle only, not a rendered observation.
    """
    if (type(host_x) is not int or type(host_y) is not int or
            type(roi) is not dict):
        raise ValueError('invalid host pixel coordinate')
    host_w,host_h=roi['host']
    x,y,width,height=roi['roi_xywh']
    source_w,source_h=roi['source']
    if not (0<=host_x<host_w and 0<=host_y<host_h):
        raise ValueError('host coordinate out of bounds')
    if not (x<=host_x<x+width and y<=host_y<y+height):
        return None
    return (source_pixel_at_output_centre(source_w,width,host_x-x),
            source_pixel_at_output_centre(source_h,height,host_y-y))

def source_pixel_at_host_centre(source_length, host_coordinate, roi_origin, roi_length):
    """Sample a host-space coordinate only when inside the registered viewport.

    This is a screenshot reference, not an assertion of physical GPU output.
    It never treats side mattes or top/bottom bars as source pixels.
    """
    if (any(type(v) is not int for v in (source_length, host_coordinate, roi_origin, roi_length))
            or not 0 < source_length <= 2147483647
            or not 0 < roi_length <= 2147483647
            or not 0 <= roi_origin <= 2147483647
            or not 0 <= host_coordinate <= 2147483647
            or not roi_origin <= host_coordinate < roi_origin + roi_length):
        raise ValueError('host pixel lies outside registered source viewport')
    return source_pixel_at_output_centre(source_length, roi_length, host_coordinate - roi_origin)


def raster_roi(source_w, source_h, host_w, host_h, par=F(7, 6), horizontal_fit=F(1)):
    if any(type(v) is not int or v > 2147483647 for v in (source_w, source_h, host_w, host_h)):
        raise ValueError("native viewport requires integer dimensions in positive int32 range")
    if type(par) is not F or type(horizontal_fit) is not F:
        raise ValueError("native viewport requires exact rational PAR and fit")
    if (min(source_w, source_h, host_w, host_h) <= 0 or
            par <= 0 or horizontal_fit <= 0):
        raise ValueError("invalid source or host dimensions")

    # Mirror native/product/widescreen_output_composition.cpp exactly: the
    # largest centered 16:9 canvas is resolved *before* fitting the source.
    # All divisions are positive integer half-up, not Python round-to-even.
    canvas_w = host_w
    canvas_h = (canvas_w * 9 + 8) // 16
    if canvas_h > host_h:
        canvas_h = host_h
        canvas_w = (canvas_h * 16 + 4) // 9
    if canvas_w < 1 or canvas_h < 1:
        raise ValueError("invalid 16:9 canvas")

    aspect = F(source_w, source_h) * par * horizontal_fit
    source_num, source_den = aspect.numerator, aspect.denominator
    width = canvas_w
    height = (width * source_den + source_num // 2) // source_num
    if height > canvas_h:
        height = canvas_h
        width = (height * source_num + source_den // 2) // source_den
    width, height = max(1, width), max(1, height)
    canvas_x, canvas_y = (host_w - canvas_w) // 2, (host_h - canvas_h) // 2
    x = canvas_x + (canvas_w - width) // 2
    y = canvas_y + (canvas_h - height) // 2
    if not (0 < width <= host_w and 0 < height <= host_h):
        raise ValueError("invalid rounded viewport")

    # Ideal unrounded extent inside the native canvas is diagnostic only.
    scale = min(F(canvas_w) / aspect, F(canvas_h))
    ideal_w, ideal_h = aspect * scale, scale
    endpoints = (
        F(1, 2) * source_w / width,
        (F(width) - F(1, 2)) * source_w / width,
        F(1, 2) * source_h / height,
        (F(height) - F(1, 2)) * source_h / height,
    )
    if not (0 < endpoints[0] < source_w and 0 < endpoints[1] < source_w
            and 0 < endpoints[2] < source_h and 0 < endpoints[3] < source_h):
        raise ValueError("source center escaped bounds")
    return {
        "source": [source_w, source_h], "host": [host_w, host_h],
        "roi_xywh": [x, y, width, height],
        "pixel_margin_lr": [x, host_w - x - width],
        "pixel_margin_tb": [y, host_h - y - height],
        "ideal_extent": [str(ideal_w), str(ideal_h)],
        "max_aspect_error": str(abs(F(width, height) - F(source_w, source_h) * par * horizontal_fit)),
        "full_source_interval": [0, source_w, 0, source_h],
        "source_center_endpoints": [str(v) for v in endpoints],
        "source_centre_coverage": {
            "horizontal": _sampled_coverage(source_w,width),
            "vertical": _sampled_coverage(source_h,height),
        },
        "reference_only": True,
        "physical_acceptance": False,
    }


def _typed_receipt_equal(actual, expected):
    """JSON-style equality with exact Python types, so 0 != False and 1 != True.

    Only compares in-memory independent screenshot receipts. Does not confer
    physical display or original/native pixel acceptance.
    """
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return (set(actual) == set(expected) and
                all(_typed_receipt_equal(actual[k], expected[k]) for k in expected))
    if type(expected) is list:
        return (len(actual) == len(expected) and
                all(_typed_receipt_equal(a, b) for a, b in zip(actual, expected)))
    return actual == expected


def validated_source_pixel_at_host_coordinate(roi, host_x, host_y, *, horizontal_fit=F(1)):
    """Refuse forged/partial ROI receipts before interpreting screenshot pixels.

    The independent screenshot reference remains diagnostic, never a physical
    or shipping-art acceptance. Recompute geometry from exact source/host
    dimensions, rather than trusting caller-supplied offsets or gate flags.
    """
    if type(roi) is not dict or set(roi) != set(raster_roi(256,224,1920,1080)):
        raise ValueError('noncanonical ROI receipt fields')
    if type(roi.get('source')) is not list or type(roi.get('host')) is not list or \
            len(roi['source']) != 2 or len(roi['host']) != 2:
        raise ValueError('invalid source/host ROI receipt dimensions')
    source_w,source_h=roi['source'];host_w,host_h=roi['host']
    expected=raster_roi(source_w,source_h,host_w,host_h,horizontal_fit=horizontal_fit)
    if not _typed_receipt_equal(roi, expected):
        raise ValueError('ROI receipt contradicts exact native-equivalent geometry')
    return source_pixel_at_host_coordinate(expected,host_x,host_y)


def source_pixel_host_span(source_length, output_length, source_index):
    """Exact half-open output-pixel interval sampling one source pixel.

    Useful for comparing a host screenshot against an independently captured
    source raster without looping over all 4K pixels. Empty spans identify
    source pixels skipped by downscaling. This remains a diagnostic oracle.
    """
    if (any(type(v) is not int for v in (source_length, output_length, source_index))
            or not 0 < source_length <= 2147483647
            or not 0 < output_length <= 2147483647
            or not 0 <= source_index < source_length):
        raise ValueError('invalid inverse source sampling coordinate')
    # f(i) = floor((2*i+1)*S/(2*O)); solve f(i)==source_index.
    def ceil_div(a,b):
        return -((-a)//b)
    lo=ceil_div(2*source_index*output_length-source_length,2*source_length)
    hi=ceil_div(2*(source_index+1)*output_length-source_length,2*source_length)
    return [max(0,min(output_length,lo)), max(0,min(output_length,hi))]


def validated_policy_source_pixel_at_host_coordinate(roi, host_x, host_y, *, mode):
    """Interpret screenshots only under an explicitly named native policy mode.

    The lower-level geometric helper accepts arbitrary exact rational fits for
    engineering experiments. Release-facing screenshot reviewers must not let
    a caller supply an arbitrary fit and then self-validate a forged ROI.
    This remains a diagnostic mapping, not physical 4K or art acceptance.
    """
    modes={'original':(256,224,F(1)), 'world342':(342,224,F(512,513))}
    if type(mode) is not str or mode not in modes:
        raise ValueError('unknown source presentation mode')
    if type(roi) is not dict or type(roi.get('host')) is not list or len(roi['host'])!=2:
        raise ValueError('invalid source presentation receipt')
    host_w,host_h=roi['host']
    source_w,source_h,fit=modes[mode]
    expected=raster_roi(source_w,source_h,host_w,host_h,horizontal_fit=fit)
    if not _typed_receipt_equal(roi,expected):
        raise ValueError('screenshot ROI contradicts named native presentation mode')
    return source_pixel_at_host_coordinate(expected,host_x,host_y)

def validated_policy_source_host_span(roi, source_x, source_y, *, mode):
    """Return the exact host-space rectangle sampling a source pixel.

    A half-open empty rectangle means downscaling skipped the source pixel.
    Require the complete named-policy receipt, rather than accepting arbitrary
    caller-controlled fit, origin or dimensions. No physical render claimed.
    """
    modes={'original':(256,224,F(1)), 'world342':(342,224,F(512,513))}
    if type(mode) is not str or mode not in modes:
        raise ValueError('unknown presentation mode')
    if type(roi) is not dict or type(roi.get('host')) is not list or len(roi['host'])!=2:
        raise ValueError('invalid presentation receipt')
    sw,sh,fit=modes[mode]
    if any(type(v) is not int for v in (source_x,source_y)) or \
            not (0<=source_x<sw and 0<=source_y<sh):
        raise ValueError('source pixel out of bounds')
    host_w,host_h=roi['host']
    expected=raster_roi(sw,sh,host_w,host_h,horizontal_fit=fit)
    if not _typed_receipt_equal(roi,expected):
        raise ValueError('source-to-host rectangle contradicts native policy')
    x,y,w,h=expected['roi_xywh']
    left,right=source_pixel_host_span(sw,w,source_x)
    top,bottom=source_pixel_host_span(sh,h,source_y)
    return [x+left,y+top,x+right,y+bottom]


def report():
    hosts = [(1920, 1080), (3840, 2160), (7680, 4320),
             (1365, 768), (3440, 1440)]
    return {
        "schema": "qa06-proposed-screenshot-roi/1",
        "policy": "exact 7:6 PAR; world342 horizontal_fit=512/513 per native compositor; no crop",
        "render_observed": False, "release_gate_credit": 0,
        "cases": {
            f"{w}x{h}": {
                "original": raster_roi(256, 224, w, h),
                "world342": raster_roi(342, 224, w, h, horizontal_fit=F(512, 513)),
            }
            for w, h in hosts
        },
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))


def audit_named_policy_sampling_coverage(roi, *, mode):
    """Analytic source-centre coverage under an exact named native policy.

    Preserving the full logical source interval does not imply every source
    pixel centre is sampled when the output viewport is smaller.
    """
    modes={'original':(256,224,F(1)), 'world342':(342,224,F(512,513))}
    if type(mode) is not str or mode not in modes:
        raise ValueError('unknown presentation mode')
    if type(roi) is not dict or type(roi.get('host')) is not list or len(roi['host']) != 2:
        raise ValueError('invalid named-policy ROI receipt')
    source_w,source_h,fit=modes[mode]
    expected=raster_roi(source_w,source_h,*roi['host'],horizontal_fit=fit)
    if not _typed_receipt_equal(roi,expected):
        raise ValueError('ROI does not match exact named native geometry')
    _,_,output_w,output_h=expected['roi_xywh']
    horizontal=_sampled_coverage(source_w,output_w)
    vertical=_sampled_coverage(source_h,output_h)
    covered=horizontal['covered']*vertical['covered']
    return {'schema':'qa06-analytic-source-centre-coverage/1',
            'mode':mode,'source_pixels':source_w*source_h,
            'sampled_source_pixels':covered,
            'skipped_source_pixels':source_w*source_h-covered,
            'full_source_centre_coverage':covered==source_w*source_h,
            'physical_screenshot_observed':False,'release_gate_credit':0}
