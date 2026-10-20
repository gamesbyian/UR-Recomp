#!/usr/bin/env python3
"""Pure rational screenshot ROI proposal, not observed physical Windows output.

Retain the entire SNES 224-row source and 7:6 pixel aspect ratio. This is a
reference to evaluate future screenshots, not a shipping-render acceptance.
"""
from fractions import Fraction as F
import json


def raster_roi(source_w, source_h, host_w, host_h, par=F(7, 6)):
    if min(source_w, source_h, host_w, host_h) <= 0 or par <= 0:
        raise ValueError("invalid source or host dimensions")
    physical_w = F(source_w) * par
    scale = min(F(host_w) / physical_w, F(host_h, source_h))
    ideal_w, ideal_h = physical_w * scale, F(source_h) * scale
    width, height = round(ideal_w), round(ideal_h)
    if not (0 < width <= host_w and 0 < height <= host_h):
        raise ValueError("invalid rounded viewport")
    x, y = (host_w - width) // 2, (host_h - height) // 2
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
        "max_aspect_error": str(abs(F(width, height) - F(source_w, source_h) * par)),
        "full_source_interval": [0, source_w, 0, source_h],
        "source_center_endpoints": [str(v) for v in endpoints],
        "reference_only": True,
        "physical_acceptance": False,
    }


def report():
    hosts = [(1920, 1080), (3840, 2160), (7680, 4320),
             (1365, 768), (3440, 1440)]
    return {
        "schema": "qa06-proposed-screenshot-roi/1",
        "policy": "exact 7:6 PAR, nearest-integer centered ROI, no 216-row crop",
        "render_observed": False, "release_gate_credit": 0,
        "cases": {
            f"{w}x{h}": {
                "original": raster_roi(256, 224, w, h),
                "world342": raster_roi(342, 224, w, h),
            }
            for w, h in hosts
        },
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
