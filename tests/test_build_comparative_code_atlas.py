#!/usr/bin/env python3
"""ROM-free regression for tools/build_comparative_code_atlas.py."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "build_comparative_code_atlas.py"
SPEC = importlib.util.spec_from_file_location("comparative_code_atlas", TOOL)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # 4 LoROM-like blobs, two banks. Function A is unchanged at the same
        # offset. Function B is moved in Europe, unchanged in beta and modified
        # beyond exact matching in prototype.
        size = 0x10000
        usa = bytearray([0xEA] * size)
        europe = bytearray([0xEA] * size)
        beta = bytearray([0xEA] * size)
        prototype = bytearray([0xEA] * size)

        a_off = 0x0100
        b_off = 0x8200
        a = bytes(range(32))
        b = bytes(range(32, 64))
        usa[a_off:a_off+32] = a
        usa[b_off:b_off+32] = b
        europe[a_off:a_off+32] = a
        beta[a_off:a_off+32] = a
        prototype[a_off:a_off+32] = a
        beta[b_off:b_off+32] = b
        moved = 0x9000
        europe[b_off:b_off+32] = bytes([0xCC] * 32)
        europe[moved:moved+32] = b
        prototype[b_off:b_off+32] = bytes([0xAB] * 32)

        paths = {}
        for name, blob in {
            "usa": usa, "europe": europe, "beta": beta, "prototype": prototype
        }.items():
            p = td / f"{name}.sfc"
            p.write_bytes(blob)
            paths[name] = p

        # offset 0x0100 -> 80:8100; offset 0x8200 -> 81:8200
        symbols = td / "symbols.json"
        symbols.write_text(json.dumps({
            "entries": [
                {"kind": "function", "address": "80:8100", "name": "A", "confidence": 5},
                {"kind": "function", "address": "81:8200", "name": "B", "confidence": 3},
                {"kind": "ram", "address": "7E:0000", "name": "RAM"},
            ]
        }))
        gaps = td / "gaps.json"
        gaps.write_text(json.dumps({"gaps": [
            {"id": "g1", "kind": "unresolved_indirect_dispatch", "site": "80:9000"}
        ]}))
        correspondence = td / "cross-build-symbol-correspondence.json"
        correspondence.write_text(json.dumps({
            "functions": [{
                "name": "B",
                "build": "pal-prototype-1994-11-29",
                "candidate": "81:8300",
                "evidence_tier": "supported",
                "byte_similarity": 0.8,
                "matcher_score": 0.75,
                "semantic_reference_recall": 0.5,
                "independent_evidence": "fixture structural edge"
            }]
        }))

        atlas = mod.build_atlas(
            paths, symbols, gaps, window_size=32, correspondence_path=correspondence
        )
        by_name = {x["name"]: x for x in atlas["functions"]}
        assert by_name["A"]["build_matches"]["europe"]["status"] == "exact_same_offset"
        assert by_name["B"]["build_matches"]["europe"]["status"] == "exact_unique_relocated"
        assert by_name["B"]["build_matches"]["europe"]["file_offset"] == moved
        assert by_name["B"]["build_matches"]["prototype"]["status"] == "unmatched"
        assert by_name["B"]["build_matches"]["prototype"]["structural_correspondence"]["evidence_tier"] == "supported"
        assert by_name["B"]["needs_structural_alignment"] is False
        assert atlas["coverage"]["structurally_resolved_exact_misses"]["prototype"] == 1
        assert by_name["A"]["semantic_status"] == "corroborated"
        assert by_name["B"]["semantic_status"] == "candidate"
        assert atlas["coverage"]["explicit_gap_count"] == 1
        assert atlas["coverage"]["known_function_symbols_atlased"] == 2
        md = mod.render_markdown(atlas)
        assert "Comparative Code Atlas" in md
        assert "unresolved_indirect_dispatch" in json.dumps(atlas)
        assert "Structurally resolved exact-fingerprint misses" in md
        assert "81:8300" in md
    print("PASS: comparative code atlas matching, coverage and gap contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
