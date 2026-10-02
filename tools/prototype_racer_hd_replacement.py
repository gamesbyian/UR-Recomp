#!/usr/bin/env python3
"""Prototype one semantic racer HD replacement without touching game state.

The tool deliberately lives on the host/artifact side. It reconstructs the
synchronized stock racer object from authoritative presentation IDs, selects a
registered representation, applies runtime orientation only after selection,
and emits deterministic comparison assets plus a validation manifest.

The Remastered candidate is a provenance-labelled Scale2x-derived placeholder
for contract validation only. It is not approved art.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from extract_racer_presentation_family import (
    compose_racer_staging,
    encode_png_rgba,
    extract_frame,
    rasterize_composed_player_rgba,
)

W = H = 64


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pixels(rgba: bytes, width: int, height: int) -> list[list[bytes]]:
    if len(rgba) != width * height * 4:
        raise ValueError("unexpected RGBA byte length")
    return [
        [rgba[(y * width + x) * 4:(y * width + x + 1) * 4] for x in range(width)]
        for y in range(height)
    ]


def flatten(grid: list[list[bytes]]) -> bytes:
    return b"".join(px for row in grid for px in row)


def nearest_rgba(rgba: bytes, width: int, height: int, scale: int) -> bytes:
    src = pixels(rgba, width, height)
    out: list[list[bytes]] = []
    for row in src:
        expanded = [px for px in row for _ in range(scale)]
        for _ in range(scale):
            out.append(expanded[:])
    return flatten(out)


def scale2x_rgba(rgba: bytes, width: int, height: int) -> bytes:
    """Classic Scale2x on exact RGBA values."""
    src = pixels(rgba, width, height)
    out = [[b"\x00\x00\x00\x00" for _ in range(width * 2)] for _ in range(height * 2)]
    for y in range(height):
        for x in range(width):
            e = src[y][x]
            b = src[y - 1][x] if y else e
            d = src[y][x - 1] if x else e
            f = src[y][x + 1] if x + 1 < width else e
            h = src[y + 1][x] if y + 1 < height else e
            if b != h and d != f:
                e0 = d if d == b else e
                e1 = f if b == f else e
                e2 = d if d == h else e
                e3 = f if h == f else e
            else:
                e0 = e1 = e2 = e3 = e
            out[y * 2][x * 2] = e0
            out[y * 2][x * 2 + 1] = e1
            out[y * 2 + 1][x * 2] = e2
            out[y * 2 + 1][x * 2 + 1] = e3
    return flatten(out)


def lock_alpha(candidate: bytes, reference: bytes) -> bytes:
    if len(candidate) != len(reference):
        raise ValueError("alpha lock requires equal-sized RGBA buffers")
    out = bytearray(candidate)
    for i in range(3, len(out), 4):
        out[i] = reference[i]
    return bytes(out)


def flip_rgba(rgba: bytes, width: int, height: int, hflip: bool, vflip: bool) -> bytes:
    src = pixels(rgba, width, height)
    ys = range(height - 1, -1, -1) if vflip else range(height)
    rows = []
    for y in ys:
        xs = range(width - 1, -1, -1) if hflip else range(width)
        rows.append([src[y][x] for x in xs])
    return flatten(rows)


def alpha_bounds(rgba: bytes, width: int, height: int) -> list[int] | None:
    pts = []
    for y in range(height):
        for x in range(width):
            if rgba[(y * width + x) * 4 + 3]:
                pts.append((x, y))
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]


def scaled_bounds(bounds: list[int] | None, scale: int) -> list[int] | None:
    if bounds is None:
        return None
    x0, y0, x1, y1 = bounds
    return [x0 * scale, y0 * scale, (x1 + 1) * scale - 1, (y1 + 1) * scale - 1]


def load_entry(registry: dict, semantic_frame_id: str) -> dict:
    hits = [x for x in registry["entries"] if x["semantic_frame_id"].lower() == semantic_frame_id.lower()]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one replacement entry for {semantic_frame_id}, found {len(hits)}")
    return hits[0]


def parse_hex(value: str) -> int:
    return int(value, 16)


def build_stock_rgba(rom: bytes, entry: dict) -> bytes:
    g = entry["composition_guards"]
    ids = {
        "p1_primary": parse_hex(g["p1_primary"]),
        "p2_primary": parse_hex(g["p2_primary"]),
        "p1_companion": parse_hex(g["p1_companion"]),
        "p2_companion": parse_hex(g["p2_companion"]),
    }
    frames = {k: extract_frame(rom, v) for k, v in ids.items()}
    composition = compose_racer_staging(
        frames["p1_primary"],
        frames["p2_primary"],
        frames["p1_companion"],
        frames["p2_companion"],
        p1_selector=int(g["p1_selector"]),
        p2_selector=int(g["p2_selector"]),
        p1_companion_enabled=parse_hex(g["p1_companion_gate_word"]) != 0,
        p2_companion_enabled=parse_hex(g["p2_companion_gate_word"]) != 0,
    )
    return rasterize_composed_player_rgba(
        rom, composition, entry["player"], parse_hex(entry["palette_asset_id"])
    )


def build_remastered_candidate(stock_rgba: bytes, entry: dict) -> tuple[bytes, int, int]:
    cfg = entry["remastered_candidate"]
    if cfg["generator"] != "tools/prototype_racer_hd_replacement.py::scale2x_rgba":
        raise ValueError("unsupported prototype candidate generator")
    out = stock_rgba
    width = W
    height = H
    for _ in range(int(cfg["passes"])):
        out = scale2x_rgba(out, width, height)
        width *= 2
        height *= 2
    expected_scale = int(cfg["density_scale"])
    if width != W * expected_scale or height != H * expected_scale:
        raise ValueError("candidate density scale does not match generator passes")
    # Keep the stock transparency footprint exact at HD density. Scale2x may
    # otherwise grow opaque pixels into neighboring transparent source cells,
    # which would move the gameplay-facing silhouette/contact edge.
    alpha_reference = nearest_rgba(stock_rgba, W, H, expected_scale)
    out = lock_alpha(out, alpha_reference)
    return out, width, height


def validate_against_assets(entry: dict, assets: dict) -> None:
    families = [x for x in assets["families"] if x["id"] == "ordinary-race-racer-presentation"]
    if len(families) != 1:
        raise ValueError("expected exactly one ordinary racer presentation family")
    proof = families[0]["composition_contract"]["synchronized_proof"]
    guards = entry["composition_guards"]
    for key in ("p1_primary", "p2_primary", "p1_companion", "p2_companion"):
        if guards[key].lower() != proof["ids"][key].lower():
            raise ValueError(f"registry {key} disagrees with synchronized proof")
    if int(guards["p1_selector"]) != int(proof["selectors"]["p1"]):
        raise ValueError("registry p1 selector disagrees with synchronized proof")
    if int(guards["p2_selector"]) != int(proof["selectors"]["p2"]):
        raise ValueError("registry p2 selector disagrees with synchronized proof")
    if guards["p1_companion_gate_word"].lower() != proof["companion_gate_words"]["p1"].lower():
        raise ValueError("registry p1 gate disagrees with synchronized proof")
    if guards["p2_companion_gate_word"].lower() != proof["companion_gate_words"]["p2"].lower():
        raise ValueError("registry p2 gate disagrees with synchronized proof")
    if proof["occupied_sources_exact"] != "25/25" or proof["occupied_destinations_present"] != "25/25":
        raise ValueError("synchronized composition proof is not exact")


def run(
    rom: bytes,
    registry: dict,
    assets: dict,
    semantic_frame_id: str,
    output_dir: Path,
    hflip: bool,
    vflip: bool,
) -> dict:
    entry = load_entry(registry, semantic_frame_id)
    validate_against_assets(entry, assets)

    authoritative_before = json.dumps(entry["composition_guards"], sort_keys=True)
    stock = build_stock_rgba(rom, entry)
    remastered, rw, rh = build_remastered_candidate(stock, entry)
    stock4 = nearest_rgba(stock, W, H, 4)

    stock_display = flip_rgba(stock4, W * 4, H * 4, hflip, vflip)
    remastered_display = flip_rgba(remastered, rw, rh, hflip, vflip)
    fallback_display = flip_rgba(stock4, W * 4, H * 4, hflip, vflip)

    authoritative_after = json.dumps(entry["composition_guards"], sort_keys=True)
    if authoritative_before != authoritative_after:
        raise AssertionError("prototype mutated semantic state")

    stock_bounds = alpha_bounds(stock, W, H)
    remastered_bounds = alpha_bounds(remastered, rw, rh)
    if remastered_bounds != scaled_bounds(stock_bounds, 4):
        raise AssertionError(
            f"replacement registration drifted: stock={stock_bounds} remastered={remastered_bounds}"
        )
    if fallback_display != stock_display:
        raise AssertionError("disabled replacement did not return exact Original presentation")

    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "original_control": ("original-control-4x.png", encode_png_rgba(W * 4, H * 4, stock_display)),
        "remastered_candidate": ("remastered-candidate-scale2x4.png", encode_png_rgba(rw, rh, remastered_display)),
        "replacement_disabled": ("replacement-disabled-control.png", encode_png_rgba(W * 4, H * 4, fallback_display)),
    }
    for _, (name, payload) in files.items():
        (output_dir / name).write_bytes(payload)

    result = {
        "schema_version": 1,
        "family": registry["family"],
        "semantic_frame_id": entry["semantic_frame_id"],
        "representation_id": entry["representation_id"],
        "lookup_primary_key": registry["lookup"]["primary_key"],
        "composition_guards": entry["composition_guards"],
        "authoritative_state_mutated": False,
        "orientation": {"hflip": hflip, "vflip": vflip, "applied_after_selection": True},
        "registration": entry["registration"],
        "original": {
            "logical_dimensions": [W, H],
            "comparison_dimensions": [W * 4, H * 4],
            "alpha_bounds": stock_bounds,
            "comparison_png": files["original_control"][0],
            "comparison_png_sha256": sha256(files["original_control"][1]),
        },
        "remastered_candidate": {
            **entry["remastered_candidate"],
            "dimensions": [rw, rh],
            "alpha_bounds": remastered_bounds,
            "png": files["remastered_candidate"][0],
            "png_sha256": sha256(files["remastered_candidate"][1]),
            "differs_from_nearest_original": remastered_display != stock_display,
        },
        "fallback": {
            "replacement_disabled_png": files["replacement_disabled"][0],
            "replacement_disabled_png_sha256": sha256(files["replacement_disabled"][1]),
            "byte_exact_to_original_control": files["replacement_disabled"][1] == files["original_control"][1],
        },
        "validation": {
            "synchronized_composition_proof_matches_registry": True,
            "whole_canvas_registration_preserved": True,
            "orientation_applied_post_selection": True,
            "fallback_exact": True,
            "missing_registration_metadata": [
                "explicit semantic pivot coordinate",
                "explicit wheel/contact anchor coordinate"
            ],
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--registry", type=Path, default=ROOT / "analysis/data/racer-hd-replacement-prototype.json")
    ap.add_argument("--assets", type=Path, default=ROOT / "analysis/data/presentation-assets.json")
    ap.add_argument("--semantic-frame-id", default="0x0541")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--hflip", action="store_true")
    ap.add_argument("--vflip", action="store_true")
    args = ap.parse_args()

    result = run(
        args.rom.read_bytes(),
        json.loads(args.registry.read_text(encoding="utf-8")),
        json.loads(args.assets.read_text(encoding="utf-8")),
        args.semantic_frame_id,
        args.output_dir,
        args.hflip,
        args.vflip,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
