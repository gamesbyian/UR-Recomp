#!/usr/bin/env python3
"""Legacy output-name adapter for current owner-approved recruitment artwork.

Previous graph-paper source JPEGs and painted cards are retired. Historical
filename compatibility remains, but only the fully compliant canonical
flagship generator can be used for new films.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
from pathlib import Path

import graph_paper_trailer_art_direction as art
import build_flagship_recruitment_20261019 as film

NAMING = {
    "ur-recomp-blue-action-80s-1080p.mp4": "ur-recomp-graphpaper-action-80s-1080p.mp4",
    "ur-recomp-blue-action-27s-vertical.mp4": "ur-recomp-graphpaper-action-27s-vertical.mp4",
    "ur-recomp-blue-action-poster.png": "ur-recomp-graphpaper-action-poster.png",
}
APPROVED = {
    "landscape": "blueprint-16x9-logo-right.png",
    "portrait": "blueprint-9x16-portrait-2160x3840.png",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def render(out: Path, cards_only: bool = False) -> None:
    out = Path(out)
    if cards_only:
        art.produce(out, aspect="16x9", logo_corner="right")
        return
    # Fail BEFORE any encoding if an older checkout would draw the old 9:16
    # matte or use its 16:9 title cards. The current flagship exposes an
    # explicit dedicated portrait plate and provenance fields.
    current = inspect.getsource(film.main)
    if 'produce_blue_assets(tmp / "portrait-art", aspect="portrait")' not in current:
        raise RuntimeError("Retired card generator would be used; update the canonical flagship exporter")
    old_argv = sys.argv
    sys.argv = ["build_flagship_recruitment_20261019.py", "--outdir", str(out)]
    try:
        film.main()
    finally:
        sys.argv = old_argv

    manifest_path = out / "flagship-provenance.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("approved_visual_assets") != APPROVED:
        raise RuntimeError("Current flagship did not attest approved landscape and portrait art")
    for old, new in NAMING.items():
        (out / old).rename(out / new)
    manifest["build_edition"] = "2026-10-26 canonical owner-approved art (legacy filenames)"
    manifest["editorial_art_sources"] = {
        "policy": "assets/promo/canonical/README.md",
        "only_owner_approved_plates": True,
        "landscape": APPROVED["landscape"],
        "portrait": APPROVED["portrait"],
        "original_generated_cards_retired": True,
    }
    manifest["claims_and_exclusions"]["visual_redesign"] = (
        "Owner-approved canonical backgrounds; no historical graph-paper cards"
    )
    manifest["output_sha256"] = {new: sha(out / new) for new in NAMING.values()}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--cards-only", action="store_true")
    args = parser.parse_args()
    render(args.outdir, args.cards_only)
