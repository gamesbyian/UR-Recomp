#!/usr/bin/env python3
"""Build a first-pass comparative code atlas across the four preserved Uniracers ROMs.

This deliberately separates three questions that were previously easy to conflate:
1. Can SNESRecomp execute a region?
2. Can independent/static analysis locate the same region across builds?
3. Do we understand the region semantically?

Known USA function symbols are fingerprinted directly from ROM bytes.  Other builds
are matched first at the corresponding LoROM file offset and then by a unique exact
byte-window search.  Exact-window matching is conservative by design: failure to
match means "needs structural analysis", not "different function".

Explicit analyzer/runtime holes live in analysis/decompilation-gaps.json and are
carried into the atlas as first-class research targets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROM_NAMES = ("usa", "europe", "beta", "prototype")
DEFAULT_ROMS = {
    "usa": Path("reference/roms/retail/Uniracers_USA.sfc"),
    "europe": Path("reference/roms/retail/Unirally_Europe.sfc"),
    "beta": Path("reference/roms/prototypes/Uniracers_Beta_legacy.sfc"),
    "prototype": Path("reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"),
}
ADDRESS_RE = re.compile(r"(?i)([0-9a-f]{2}):?([0-9a-f]{4})")


def parse_cpu_address(text: str) -> int | None:
    m = ADDRESS_RE.search(text)
    if not m:
        return None
    return (int(m.group(1), 16) << 16) | int(m.group(2), 16)


def canonical_cpu(value: int) -> str:
    return f"{(value >> 16) & 0xFF:02X}:{value & 0xFFFF:04X}"


def lorom_cpu_to_file(cpu: int) -> int | None:
    bank = (cpu >> 16) & 0xFF
    addr = cpu & 0xFFFF
    if addr < 0x8000:
        return None
    return ((bank & 0x7F) * 0x8000) + (addr - 0x8000)


def file_to_lorom_cpu(offset: int) -> int:
    bank = offset // 0x8000
    addr = 0x8000 + (offset % 0x8000)
    return ((0x80 | bank) << 16) | addr


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def all_occurrences(haystack: bytes, needle: bytes, limit: int = 16) -> list[int]:
    if not needle:
        return []
    out: list[int] = []
    pos = 0
    while len(out) < limit:
        pos = haystack.find(needle, pos)
        if pos < 0:
            break
        out.append(pos)
        pos += 1
    return out


def match_build(data: bytes, usa_offset: int, window: bytes) -> dict[str, Any]:
    if usa_offset + len(window) <= len(data) and data[usa_offset:usa_offset + len(window)] == window:
        return {
            "status": "exact_same_offset",
            "file_offset": usa_offset,
            "cpu_address": canonical_cpu(file_to_lorom_cpu(usa_offset)),
            "match_count_capped": 1,
        }
    hits = all_occurrences(data, window)
    if len(hits) == 1:
        off = hits[0]
        return {
            "status": "exact_unique_relocated",
            "file_offset": off,
            "cpu_address": canonical_cpu(file_to_lorom_cpu(off)),
            "match_count_capped": 1,
        }
    return {
        "status": "unmatched" if not hits else "exact_ambiguous",
        "file_offset": None,
        "cpu_address": None,
        "match_count_capped": len(hits),
        "candidate_offsets": hits,
    }


def semantic_status(symbol: dict[str, Any]) -> str:
    confidence = symbol.get("confidence")
    try:
        score = int(confidence)
    except (TypeError, ValueError):
        score = 0
    if score >= 4:
        return "corroborated"
    if score >= 2:
        return "candidate"
    return "named_unverified"


def build_atlas(
    rom_paths: dict[str, Path],
    symbols_path: Path,
    gaps_path: Path,
    *,
    window_size: int = 32,
) -> dict[str, Any]:
    if window_size < 8:
        raise ValueError("window_size must be >= 8")
    roms = {name: rom_paths[name].read_bytes() for name in ROM_NAMES}
    symbols_payload = json.loads(symbols_path.read_text(encoding="utf-8"))
    gaps_payload = json.loads(gaps_path.read_text(encoding="utf-8"))

    functions: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for symbol in symbols_payload.get("entries", []):
        if symbol.get("kind") != "function":
            continue
        cpu = parse_cpu_address(str(symbol.get("address", "")))
        if cpu is None:
            skipped.append({"name": symbol.get("name"), "reason": "unparseable_address"})
            continue
        off = lorom_cpu_to_file(cpu)
        if off is None or off >= len(roms["usa"]):
            skipped.append({
                "name": symbol.get("name"),
                "address": canonical_cpu(cpu),
                "reason": "non_rom_or_out_of_range",
            })
            continue
        window = roms["usa"][off:off + window_size]
        if len(window) < window_size:
            skipped.append({
                "name": symbol.get("name"),
                "address": canonical_cpu(cpu),
                "reason": "short_fingerprint_window",
            })
            continue
        matches = {
            "usa": {
                "status": "canonical",
                "file_offset": off,
                "cpu_address": canonical_cpu(cpu),
                "match_count_capped": 1,
            }
        }
        for name in ROM_NAMES[1:]:
            matches[name] = match_build(roms[name], off, window)

        functions.append({
            "id": f"fn_{cpu:06X}",
            "name": symbol.get("name"),
            "usa_cpu_address": canonical_cpu(cpu),
            "usa_file_offset": off,
            "fingerprint": {
                "window_size": window_size,
                "sha256": sha256(window),
                "hex_prefix": window[:8].hex(),
            },
            "semantic_status": semantic_status(symbol),
            "confidence": symbol.get("confidence"),
            "evidence": symbol.get("evidence_/_notes") or symbol.get("evidence") or symbol.get("notes"),
            "build_matches": matches,
            "needs_structural_alignment": any(
                m["status"] in {"unmatched", "exact_ambiguous"}
                for name, m in matches.items() if name != "usa"
            ),
        })

    match_counts: dict[str, dict[str, int]] = {}
    for name in ROM_NAMES[1:]:
        counts: dict[str, int] = {}
        for fn in functions:
            status = fn["build_matches"][name]["status"]
            counts[status] = counts.get(status, 0) + 1
        match_counts[name] = dict(sorted(counts.items()))

    semantic_counts: dict[str, int] = {}
    for fn in functions:
        status = fn["semantic_status"]
        semantic_counts[status] = semantic_counts.get(status, 0) + 1

    gaps = gaps_payload.get("gaps", [])
    gap_counts: dict[str, int] = {}
    for gap in gaps:
        kind = str(gap.get("kind", "unknown"))
        gap_counts[kind] = gap_counts.get(kind, 0) + 1

    return {
        "schema_version": 1,
        "description": "UR-Recomp comparative code atlas; exact fingerprints are conservative correspondence evidence, not semantic proof.",
        "inputs": {
            "symbols": str(symbols_path),
            "gaps": str(gaps_path),
            "roms": {
                name: {
                    "path": str(rom_paths[name]),
                    "size": len(roms[name]),
                    "sha256": sha256(roms[name]),
                }
                for name in ROM_NAMES
            },
        },
        "coverage": {
            "known_function_symbols_atlased": len(functions),
            "skipped_function_symbols": len(skipped),
            "semantic_status_counts": dict(sorted(semantic_counts.items())),
            "cross_build_match_status_counts": match_counts,
            "explicit_gap_count": len(gaps),
            "gap_kind_counts": dict(sorted(gap_counts.items())),
            "note": (
                "These counts measure current queryable evidence only. They are intentionally "
                "not percentages of total game code and must not be conflated with SNESRecomp AOT coverage."
            ),
        },
        "functions": functions,
        "explicit_gaps": gaps,
        "skipped": skipped,
    }


def render_markdown(atlas: dict[str, Any]) -> str:
    c = atlas["coverage"]
    lines = [
        "# Comparative Code Atlas",
        "",
        "Generated by `tools/build_comparative_code_atlas.py`.",
        "",
        "This is a correspondence and research-queue surface. Exact byte-window matches are strong",
        "evidence that a known USA routine survived unchanged in another build; unmatched routines",
        "are queued for structural/CFG analysis rather than assumed to be absent.",
        "",
        "## Coverage",
        "",
        f"- known function symbols atlased: **{c['known_function_symbols_atlased']}**",
        f"- skipped function symbols: **{c['skipped_function_symbols']}**",
        f"- explicit decompilation/runtime gaps: **{c['explicit_gap_count']}**",
        "",
        "These are evidence counts, not a decompilation-completeness percentage.",
        "",
        "## Cross-build exact correspondence",
        "",
        "| Build | Same offset | Unique relocated | Ambiguous | Unmatched |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in ROM_NAMES[1:]:
        x = c["cross_build_match_status_counts"].get(name, {})
        lines.append(
            f"| {name} | {x.get('exact_same_offset', 0)} | "
            f"{x.get('exact_unique_relocated', 0)} | {x.get('exact_ambiguous', 0)} | "
            f"{x.get('unmatched', 0)} |"
        )

    lines += ["", "## Explicit gaps", ""]
    for gap in atlas["explicit_gaps"]:
        loc = gap.get("address") or gap.get("site") or gap.get("region") or "n/a"
        lines.append(
            f"- **{gap.get('id', 'gap')}** — `{loc}`: {gap.get('summary', gap.get('kind', 'unknown'))}"
        )

    lines += [
        "",
        "## Functions needing structural alignment",
        "",
        "| USA address | Symbol | Europe | Beta | Prototype |",
        "|---|---|---|---|---|",
    ]
    unresolved = [f for f in atlas["functions"] if f["needs_structural_alignment"]]
    for fn in unresolved:
        def state(build: str) -> str:
            return fn["build_matches"][build]["status"]
        lines.append(
            f"| `{fn['usa_cpu_address']}` | {fn['name']} | {state('europe')} | "
            f"{state('beta')} | {state('prototype')} |"
        )
    if not unresolved:
        lines.append("| — | No exact-fingerprint alignment gaps in current symbol set | — | — | — |")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ROM_NAMES:
        ap.add_argument(f"--{name}", type=Path, default=DEFAULT_ROMS[name])
    ap.add_argument("--symbols", type=Path, default=Path("analysis/generated/symbols.json"))
    ap.add_argument("--gaps", type=Path, default=Path("analysis/decompilation-gaps.json"))
    ap.add_argument("--window-size", type=int, default=32)
    ap.add_argument("--json-out", type=Path, default=Path("analysis/generated/comparative-code-atlas.json"))
    ap.add_argument("--md-out", type=Path, default=Path("analysis/generated/comparative-code-atlas.md"))
    args = ap.parse_args()
    rom_paths = {name: getattr(args, name) for name in ROM_NAMES}
    atlas = build_atlas(rom_paths, args.symbols, args.gaps, window_size=args.window_size)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(atlas, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(atlas), encoding="utf-8")
    print(json.dumps(atlas["coverage"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
