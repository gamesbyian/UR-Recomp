"""Bounded, source-independent ROI reference for two observed Modern SDL menu captures.

ROM-free diagnostic only. This never changes or qualifies the gameplay
compositor; its 4:3 rule is tied to one retained Windows capture epoch.
"""
from __future__ import annotations
from typing import Any

SOURCE_WIDTH, SOURCE_HEIGHT = 256, 224
# Agent 5 H26 recovery, QA PR #2041 Windows run 39534714437,
# artifact 12316988012. No general claim for unobserved resolutions.
OBSERVED_MENU_ROI = {
    (1024, 768): (0, 0, 1024, 768),
    (1280, 720): (160, 0, 960, 720),
}


def modern_menu_surface_reference(width: int, height: int) -> dict[str, Any]:
    """Return the observed menu ROI, never an inferred 16:9 gameplay canvas.

    Unknown sizes fail closed. Block-consistent output could still depict the
    wrong source image; this helper gives no physical/art/release acceptance.
    """
    if type(width) is not int or type(height) is not int:
        raise ValueError('menu host dimensions must be integers')
    try:
        x, y, w, h = OBSERVED_MENU_ROI[(width, height)]
    except KeyError as exc:
        raise ValueError('host dimensions lack observed Modern menu evidence') from exc
    if (w < SOURCE_WIDTH or h < SOURCE_HEIGHT or x < 0 or y < 0 or
            x + w > width or y + h > height):
        raise ValueError('menu screenshot source viewport is incomplete')
    return {
        'schema': 'qa06-modern-menu-observed-roi/1',
        'host': [width, height],
        'source': [SOURCE_WIDTH, SOURCE_HEIGHT],
        'roi_xywh': [x, y, w, h],
        'source_pixels': SOURCE_WIDTH * SOURCE_HEIGHT,
        'source_host_samples': w * h,
        'matte_samples': width * height - w * h,
        'source_centre_coverage': True,
        'observation': 'retained Modern SDL menu Windows capture only',
        'gameplay_16x9_resolver_changed': False,
        'independent_source_raster_parity': False,
        'physical_4k_accepted': False,
        'art_approved': False,
        'release_gate_credit': 0,
    }


def menu_source_pixel_at_host(width: int, height: int, host_x: int, host_y: int):
    """Map host pixel centre to nearest source pixel; None for side matte."""
    result = modern_menu_surface_reference(width, height)
    if type(host_x) is not int or type(host_y) is not int:
        raise ValueError('host coordinates must be integers')
    if not (0 <= host_x < width and 0 <= host_y < height):
        raise ValueError('host coordinate outside observed drawable')
    x, y, w, h = result['roi_xywh']
    if not (x <= host_x < x + w and y <= host_y < y + h):
        return None
    return (
        ((2 * (host_x - x) + 1) * SOURCE_WIDTH) // (2 * w),
        ((2 * (host_y - y) + 1) * SOURCE_HEIGHT) // (2 * h),
    )
