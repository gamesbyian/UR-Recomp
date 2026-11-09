#!/usr/bin/env python3
"""Stage public, read-only contributor reference assets into an existing atlas Pages site.

No novel art generation, no box-art exposure, no ROM, no third-party URL fetching.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import shutil
import struct

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools" / "contributor_gallery" / "index.html"
CONCEPT_DIR = ROOT / "assets/branding/concepts"
BRANDING = ROOT / "assets/branding"
NAMES = (
    "regional-wordmark-concept-01.png",
    "regional-wordmark-concept-02.png",
    "regional-wordmark-concept-03.png",
)
SVG_NAMES = (
    "uniracers-box-wordmark-traced.svg",
    "unirally-box-wordmark-traced.svg",
    "uniracers-japanese-katakana-wordmark.svg",
    "unirally-russian-cyrillic-wordmark.svg",
    "unirally-french-wordmark.svg",
)

def png_info(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"{path}: not a PNG with IHDR")
    width, height = struct.unpack(">II", header[16:24])
    if width < 100 or height < 100 or width > 10000 or height > 10000:
        raise ValueError(f"{path}: invalid dimensions")
    if path.stat().st_size > 5_000_000:
        raise ValueError(f"{path}: concept image exceeds public gallery size cap")
    return width, height

def stage(out: Path) -> dict:
    if not out.is_dir() or out.is_symlink():
        raise ValueError("existing nonredirected atlas site required")
    gallery = out / "contributors"
    if gallery.exists() or gallery.is_symlink():
        raise ValueError("refusing to overwrite contributor route")
    if not SOURCE.is_file():
        raise ValueError("missing gallery HTML source")
    all_sources = [(CONCEPT_DIR / n, n) for n in NAMES] + [(BRANDING / n, n) for n in SVG_NAMES]
    for source, name in all_sources:
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"missing/redirected source: {name}")
        if source.suffix == ".png":
            png_info(source)
        else:
            data = source.read_bytes()
            if len(data) > 1_000_000 or b"<svg" not in data:
                raise ValueError(f"invalid/oversized SVG reference: {name}")
    import tempfile
    with tempfile.TemporaryDirectory(prefix="contributor-gallery-", dir=out) as temp:
        intermediate = Path(temp) / "contributors"
        images = intermediate / "images"
        images.mkdir(parents=True)
        shutil.copyfile(SOURCE, intermediate / "index.html")
        report = {}
        for source, name in all_sources:
            destination = images / name
            shutil.copyfile(source, destination)
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            copied = hashlib.sha256(destination.read_bytes()).hexdigest()
            if original != copied:
                raise ValueError(f"asset checksum changed: {name}")
            report[name] = {"sha256": copied, "bytes": destination.stat().st_size}
        intermediate.rename(gallery)
    return report

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True, type=Path)
    args = parser.parse_args()
    rows = stage(args.site)
    print(f"Contributor gallery staged: {len(rows)} exact unmodified image assets; no box art")

if __name__ == "__main__":
    main()
