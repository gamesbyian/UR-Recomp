"""Source-bound visibility check for the unapproved articulated tire blockout."""
from __future__ import annotations

import math
import re
import unittest
from pathlib import Path

SCAD = Path(__file__).resolve().parents[2] / "tools/art/candidates/unicycle_shared_rig.scad"
NUMBER = r"([0-9]+(?:\.[0-9]+)?)"


def tire_parameters(source: str):
    body = re.search(r"module\s+tire\(\)\s*\{([^{}]*)\}", source)
    if not body:
        raise ValueError("missing or unsupported tire module")
    text = body.group(1)
    rubber = re.search(r"color\(\[0\.075,0\.083,0\.09\]\)\s*torus\(" + NUMBER + "," + NUMBER + r"\)", text)
    accent = re.search(r"translate\(\[0,(-?[0-9.]+),0\]\)\s*color\(\[0\.14,0\.16,0\.16\]\)\s*torus\(" + NUMBER + "," + NUMBER + r"\)", text)
    if not rubber or not accent:
        raise ValueError("tire material geometry changed; inspect the surface before accepting")
    main_r, main_t = map(float, rubber.groups())
    y, accent_r, accent_t = map(float, accent.groups())
    return main_r, main_t, y, accent_r, accent_t


class TireAccentVisibility(unittest.TestCase):
    def test_front_sidewall_accent_intersects_and_protrudes(self):
        main_r, main_t, y, accent_r, accent_t = tire_parameters(SCAD.read_text())
        offset = accent_r - main_r
        near = math.hypot(offset, abs(y) - accent_t)
        far = math.hypot(offset, abs(y) + accent_t)
        self.assertLess(near, main_t, "accent is detached from the rubber sidewall")
        self.assertGreater(far, main_t, "accent is entirely buried in opaque rubber")
        self.assertLess(y, 0, "accent must remain on the camera-facing tire sidewall")

    def test_unshifted_previous_blockout_is_not_accepted(self):
        source = SCAD.read_text().replace("translate([0,-0.15,0])", "translate([0,0,0])")
        main_r, main_t, y, accent_r, accent_t = tire_parameters(source)
        far = math.hypot(accent_r - main_r, abs(y) + accent_t)
        self.assertLess(far, main_t, "negative control should be completely buried")


if __name__ == "__main__":
    unittest.main()
