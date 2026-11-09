#!/usr/bin/env python3
"""Verify the French parody wordmark reuses canonical English logo glyphs.

Run: python3 tools/verify_french_wordmark_glyphs.py
Only uses Python's standard library. No art pixels are generated or compared.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "assets" / "branding"
NS = {"svg": "http://www.w3.org/2000/svg"}
TITLE = "l'inéluctable esseulement de la roue unique."
LETTER_IDS = ("u", "n", "i", "r", "a", "c", "e", "s", "l")
NEW_IDS = ("b", "d", "m", "o", "q", "t")
ACCENTS = ("accent", "apostrophe", "period")
SPIRAL_IDS = ("spiral-1-3", "spiral-3-11")
TRANSFORM = re.compile(
    r"^translate\((-?(?:\d+\.)?\d+) (-?(?:\d+\.)?\d+)\) "
    r"scale\((\d+(?:\.\d+)?)\)$"
)

def get_path(root: ET.Element, name: str) -> str:
    node = root.find(f".//svg:path[@id='{name}']", NS)
    assert node is not None, f"Missing path: {name}"
    value = node.get("d")
    assert value and value.strip().endswith(("Z", "z")), name
    return value

def main() -> None:
    french = ET.parse(BRAND / "unirally-french-wordmark.svg").getroot()
    usa = ET.parse(BRAND / "uniracers-box-wordmark-traced.svg").getroot()
    pal = ET.parse(BRAND / "unirally-box-wordmark-traced.svg").getroot()
    shared = ET.parse(BRAND / "shared" / "unira-shared-glyph-master.svg").getroot()
    actual_title = french.find("svg:title", NS)
    assert actual_title is not None and actual_title.text == TITLE

    for glyph in ("u", "n", "i", "r", "a", "spiral"):
        assert get_path(french, f"shape-{glyph}") == get_path(shared, f"shared-{glyph}")
        assert get_path(french, f"shape-{glyph}") == get_path(usa, f"shared-{glyph}")
        assert get_path(french, f"shape-{glyph}") == get_path(pal, f"shared-{glyph}")
    for glyph in ("c", "e", "s"):
        assert get_path(french, f"shape-{glyph}") == get_path(usa, glyph)
    assert get_path(french, "shape-l") == get_path(pal, "l-first")
    for glyph in (*NEW_IDS, *ACCENTS):
        get_path(french, f"shape-{glyph}")

    placed = french.find(".//svg:g[@id='letter-placements']", NS)
    spiral_group = french.find(".//svg:g[@id='spiral-placements']", NS)
    assert placed is not None and spiral_group is not None
    glyph_counts: Counter[str] = Counter()
    for group in (placed, spiral_group):
        for node in group.findall("svg:use", NS):
            href = node.get("href")
            assert href and href.startswith("#shape-")
            glyph = href.removeprefix("#shape-")
            assert french.find(f".//svg:path[@id='shape-{glyph}']", NS) is not None
            assert TRANSFORM.fullmatch(node.get("transform", "")), node.attrib
            glyph_counts[glyph] += 1
    assert sum(glyph_counts.values()) == 42, glyph_counts
    assert glyph_counts["spiral"] == 2
    assert glyph_counts["accent"] == 1
    assert glyph_counts["apostrophe"] == 1
    assert glyph_counts["period"] == 1
    assert sum(glyph_counts[g] for g in LETTER_IDS) == 30
    assert sum(glyph_counts[g] for g in NEW_IDS) == 7

    # Every layer must reference the same placements, never independently
    # approximate glyph silhouettes, and must use the canonical family palette.
    expected = {
        "offset-black-border": ("#letter-placements", "#090409", "8", "translate(2 2)"),
        "uniform-black-keyline": ("#letter-placements", "none", "2.4", None),
        "yellow-letter-faces": ("#letter-placements", "#ffea00", None, None),
        "spiral-offset-black-border": (
            "#spiral-placements", "#090409", "5", "translate(1.25 1.25)"
        ),
        "spiral-uniform-black-keyline": (
            "#spiral-placements", "none", "1.5", None
        ),
        "spiral-yellow-letter-face": ("#spiral-placements", "#ffea00", None, None),
    }
    for name, (href, fill, stroke_width, translation) in expected.items():
        node = french.find(f".//svg:use[@id='{name}']", NS)
        assert node is not None, name
        assert node.get("href") == href, name
        assert node.get("fill") == fill, name
        assert node.get("stroke-width") == stroke_width, name
        assert node.get("transform") == translation, name

    print("PASS: exact shared Uniracers/Unirally letter contours (30 uses)")
    print("PASS: exact shared spiral twice, unique French additions and lowercase title")
    print("PASS: matched yellow, black and lighter spiral borders; no warped placement")

if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ET.ParseError, OSError, ValueError) as err:
        print(f"FAIL: {err}", file=sys.stderr)
        raise SystemExit(1)
