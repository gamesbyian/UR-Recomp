#!/usr/bin/env python3
"""Regression guard for the owner-approved Uniracers/Unirally shared glyphs.

Run: python3 tools/verify_shared_wordmark_glyphs.py
No dependencies beyond the Python standard library.
"""
from __future__ import annotations

from pathlib import Path
import math
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BRANDING = ROOT / "assets" / "branding"
FILES = (
    BRANDING / "shared" / "unira-shared-glyph-master.svg",
    BRANDING / "uniracers-box-wordmark-traced.svg",
    BRANDING / "unirally-box-wordmark-traced.svg",
)
NS = {"s": "http://www.w3.org/2000/svg"}
GLYPHS = ("u", "n", "i", "r", "a", "spiral")
INSTANCES = (
    ("u", "u"),
    ("n", "n"),
    ("i", "i"),
    ("r", "first-r"),
    ("a", "a"),
    ("spiral", "i-spiral-dot"),
)
RALLY_INSTANCES = (
    ("u", "u"),
    ("n", "n"),
    ("i", "i"),
    ("r", "r"),
    ("a", "a"),
    ("spiral", "i-spiral"),
)
DECORATION = ("#ffea00", "#090409")
TRANSLATE_SCALE = re.compile(
    r"^translate\((-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)\) "
    r"scale\((\d+(?:\.\d+)?)\)$"
)

def check() -> None:
    roots = [ET.parse(filename).getroot() for filename in FILES]
    masters = []
    for root in roots:
        master = {}
        for name in GLYPHS:
            path = root.find(f".//s:path[@id='shared-{name}']", NS)
            assert path is not None, f"Missing shared-{name}"
            master[name] = path.get("d")
            assert master[name] and master[name].strip().endswith("Z")
        masters.append(master)
    assert masters[0] == masters[1] == masters[2], (
        "The two wordmarks and shared glyph library have diverged"
    )

    for root, mapping in zip(roots[1:], (INSTANCES, RALLY_INSTANCES)):
        contours = root.find(".//s:g[@id='wordmark-contours']", NS)
        spiral_contours = root.find(".//s:g[@id='spiral-contours']", NS)
        assert contours is not None and spiral_contours is not None
        for glyph, element_id in mapping:
            group = spiral_contours if glyph == "spiral" else contours
            use = group.find(f"s:use[@id='{element_id}']", NS)
            assert use is not None, f"Missing {element_id}"
            assert use.get("href") == f"#shared-{glyph}", (
                f"{element_id} points at a noncanonical glyph"
            )
            # Only similarity transforms, no independent X/Y stretch or rotation.
            m = TRANSLATE_SCALE.fullmatch(use.get("transform") or "")
            assert m, f"Nonuniform or unsupported transform for {element_id}"
            values = [float(x) for x in m.groups()]
            assert all(math.isfinite(x) for x in values) and values[2] > 0
            assert not any(
                p.get("id") == element_id
                for p in group.findall("s:path", NS)
            ), f"Old standalone path remains for {element_id}"
        for role in (
            "offset-black-border",
            "uniform-black-keyline",
            "yellow-letter-faces",
        ):
            use = root.find(f".//s:use[@id='{role}']", NS)
            assert use is not None
            assert use.get("href") == "#wordmark-contours"
        faces = root.find(".//s:use[@id='yellow-letter-faces']", NS)
        assert faces.get("fill") == DECORATION[0]
        border = root.find(".//s:use[@id='offset-black-border']", NS)
        assert border.get("fill") == DECORATION[1]
        assert border.get("stroke") == DECORATION[1]
        assert border.get("stroke-width") == "8"
        assert border.get("transform") == "translate(2 2)"
        rim = root.find(".//s:use[@id='uniform-black-keyline']", NS)
        assert rim.get("stroke-width") == "2.4"
        assert rim.get("stroke") == DECORATION[1]
        # The spiral is a fine detail: preserve the same shape but give its
        # own, lighter presentation outline. Catch any return to body weight.
        spiral_style = {
            "spiral-offset-black-border": (
                "#spiral-contours", DECORATION[1], "5",
                "translate(1.25 1.25)"
            ),
            "spiral-uniform-black-keyline": (
                "#spiral-contours", "none", "1.5", None
            ),
            "spiral-yellow-letter-face": (
                "#spiral-contours", DECORATION[0], None, None
            ),
        }
        for role, (href, fill, stroke_width, transform) in spiral_style.items():
            use = root.find(f".//s:use[@id='{role}']", NS)
            assert use is not None, f"Missing {role}"
            assert use.get("href") == href
            assert use.get("fill") == fill
            assert use.get("stroke-width") == stroke_width
            assert use.get("transform") == transform
        assert contours.find("s:use[@href='#shared-spiral']", NS) is None
    assert "M 383.202 65.294" in masters[0]["spiral"], (
        "Spiral no longer comes from the owner-supplied source"
    )
    print("PASS: shared u, n, i, r, a, spiral identical in library and both wordmarks")
    print("PASS: instances use uniform scale; body and lighter spiral border styles match")

if __name__ == "__main__":
    try:
        check()
    except (AssertionError, ET.ParseError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
