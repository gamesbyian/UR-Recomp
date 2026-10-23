#!/usr/bin/env python3
"""Independent, read-only two-resolution witness for a retained Windows SDL root.

Usage: python verify_cross_resolution.py BASELINE_ARTIFACT_ZIP SIZE_ARTIFACT_ZIP
Needs Pillow and NumPy. No ROM or original source images are distributed by this script.
An exact native log is needed for source-stage attestation; this pixel-only
cross-resolution discriminator is not a substitute for source provenance.
"""
from __future__ import annotations
import hashlib
import io
import json
import sys
import zipfile
import numpy as np
from PIL import Image

ROOT_LINE = 'UR_BALDOSA_MODERN_DESTINATION stage=root raster=342x224 root=11,10,320,204 source=modern_product_view'
CAPTURE_856 = 'UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 guest_frame=40 output=856x480 source=SDL_RenderReadPixels backend=sdl3'
CAPTURE_1280 = 'UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 guest_frame=40 output=1280x720 source=SDL_RenderReadPixels backend=sdl3'


def get(z, path, digest):
    raw = z.read(path)
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('source artifact hash mismatch: ' + path)
    return raw


def viewport(width, height, logical_width):
    par = 7 / 6
    scale = min(width / (logical_width * par), height / 224)
    sx, sy = scale * par, scale
    return sx, sy, (width - logical_width * sx) / 2, (height - 224 * sy) / 2


def candidate(reference, observed, logical_width, inset=.75):
    sh, sw = reference.shape[:2]
    oh, ow = observed.shape[:2]
    sx, sy, vx, vy = viewport(sw, sh, logical_width)
    xx = np.clip([int(vx + (x + .5) * sx) for x in range(logical_width)], 0, sw - 1)
    yy = np.clip([int(vy + (y + .5) * sy) for y in range(224)], 0, sh - 1)
    source = reference[np.asarray(yy)[:, None], np.asarray(xx)[None, :]]
    sx, sy, vx, vy = viewport(ow, oh, logical_width)
    fx = (np.arange(ow) + .5 - vx) / sx
    fy = (np.arange(oh) + .5 - vy) / sy
    xx = np.clip(np.floor(fx).astype(int), 0, logical_width - 1)
    yy = np.clip(np.floor(fy).astype(int), 0, 223)
    predicted = source[yy[:, None], xx[None, :]]
    # Exclude boundary-adjacent output pixels rather than relaxing the
    # diagnostic's global 0.2% per-block tolerance. This is a separate test.
    x_safe = np.minimum(fx % 1, 1 - fx % 1) * sx >= inset
    y_safe = np.minimum(fy % 1, 1 - fy % 1) * sy >= inset
    mask = y_safe[:, None] & x_safe[None, :]
    changed = np.any(predicted != observed, axis=2)
    return {'stable_pixels': int(mask.sum()),
            'different_pixels': int((changed & mask).sum()),
            'all_different_pixels': int(changed.sum())}


def verify(baseline_zip, size_zip):
    with zipfile.ZipFile(baseline_zip) as a, zipfile.ZipFile(size_zip) as b:
        if a.testzip() is not None or b.testzip() is not None:
            raise ValueError('ZIP CRC failed')
        r1 = json.loads(a.read('readback-receipt.json'))
        prefix = 'ur-modern-win32-visual-1280x720/'
        r2 = json.loads(b.read(prefix + 'readback-receipt.json'))
        if (r1['source_sha'] != r2['source_sha'] or
                r1['exe_sha256'] != r2['exe_sha256'] or
                r1['native_semantic_route'] != r2['native_semantic_route'] or
                r1['native_semantic_route'] != 'root-quit' or
                r1['actual_sdl_renderer_output'] != [856, 480] or
                r2['actual_sdl_renderer_output'] != [1280, 720]):
            raise ValueError('not same PE/source/route or output size')
        l1 = get(a, 'capture_observed/native-process.log', r1['native_process_log_sha256']).decode()
        l2 = get(b, prefix + 'probe_first/native-process.log', r2['native_process_log_sha256']).decode()
        if ROOT_LINE not in l1 or ROOT_LINE not in l2 or CAPTURE_856 not in l1 or CAPTURE_1280 not in l2:
            raise ValueError('missing source-verified exact native root/capture stage')
        get(a, 'capture_observed/actual-sdl-drawable.pam', r1['p7_sha256'])
        get(b, prefix + 'probe_first/actual-sdl-drawable.pam', r2['p7_sha256'])
        png1 = get(a, 'actual-sdl-drawable.png', r1['png_sha256'])
        png2 = get(b, prefix + 'actual-sdl-drawable.png', r2['png_sha256'])
        observed = np.asarray(Image.open(io.BytesIO(png1)).convert('RGB'))
        reference = np.asarray(Image.open(io.BytesIO(png2)).convert('RGB'))
        return {'source_sha': r1['source_sha'], 'exe_sha256': r1['exe_sha256'],
                'root_source_log': [342, 224],
                'observed_output': [856, 480], 'reference_output': [1280, 720],
                'stable_pixel_inset': .75,
                'candidate_342': candidate(reference, observed, 342),
                'candidate_256': candidate(reference, observed, 256),
                'scope': 'same-source/PE original Windows SDL RGB, no release gate credit'}

if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print(json.dumps(verify(sys.argv[1], sys.argv[2]), indent=2))
