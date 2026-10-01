#!/usr/bin/env python3
"""Build cross-build semantic symbol correspondences from trusted structural evidence.

Function correspondences come from the trusted semantic-anchor matcher.
RAM correspondences join named USA symbols to the WRAM motion atlas.

This is intentionally conservative:
- exact/strong function matches are exported with their matcher evidence;
- RAM mappings seen in >=2 trusted anchors are "strong";
- RAM mappings seen in one trusted anchor are "candidate";
- conflicting mappings are never promoted.
"""
from __future__ import annotations

from pathlib import Path
import json
import re

try:
    from tools.compare_semantic_anchors import build_output
except ModuleNotFoundError:
    from compare_semantic_anchors import build_output

ROOT = Path(__file__).resolve().parents[1]
SO_SYMBOLS = ROOT / "analysis" / "generated" / "symbols.json"
WRAM = ROOT / "analysis" / "generated" / "wram-motion-atlas.json"
OUT_JSON = ROOT / "analysis" / "generated" / "cross-build-symbol-correspondence.json"
OUT_MD = ROOT / "analysis" / "generated" / "cross-build-symbol-correspondence.md"

BUILD_LABELS = {
    "legacy-beta": "Legacy beta",
    "pal-prototype-1994-11-29": "PAL prototype",
    "europe-retail": "Europe retail",
}


def parse_usa_ram_address(value: str) -> str | None:
    m = re.fullmatch(r"7E:([0-9A-Fa-f]{4})", value.strip("` "))
    return m.group(1).upper() if m else None


def named_ram_symbols(symbol_doc: dict) -> dict[str, dict]:
    out = {}
    for entry in symbol_doc["entries"]:
        if entry.get("kind") != "ram":
            continue
        addr = parse_usa_ram_address(entry.get("address", ""))
        if addr is None:
            continue
        out[addr] = entry
    return out


def build_ram_correspondences(symbol_doc: dict, atlas: dict) -> list[dict]:
    names = named_ram_symbols(symbol_doc)
    rows = []
    for item in atlas["field_consistency"]:
        if not item["consistent"]:
            continue
        usa = item["usa_word"].upper()
        symbol = names.get(usa)
        if symbol is None:
            continue
        candidate = item["candidate_words"][0].upper()
        anchor_count = len(item["anchors"])
        rows.append({
            "name": symbol["name"],
            "usa": f"7E:{usa}",
            "build": item["build"],
            "candidate": f"7E:{candidate}",
            "delta": item["deltas"][0],
            "source_confidence": symbol.get("confidence"),
            "anchor_count": anchor_count,
            "anchors": item["anchors"],
            "evidence_tier": "strong" if anchor_count >= 2 else "candidate",
        })
    rows.sort(key=lambda x: (x["build"], x["evidence_tier"] != "strong", x["name"]))
    return rows


def build_function_correspondences(corpus: dict) -> list[dict]:
    rows = []
    for anchor in corpus["anchors"]:
        for build, matches in anchor["matches"].items():
            if not matches:
                continue
            top = matches[0]
            sim = top["byte_similarity"]
            if build == "legacy-beta":
                tier = "exact" if sim == 1.0 else "strong"
            elif sim >= 0.90:
                tier = "strong"
            elif sim >= 0.72:
                tier = "supported"
            else:
                tier = "candidate"
            rows.append({
                "name": anchor["name"],
                "usa": anchor["cpu_address"],
                "build": build,
                "candidate": top["cpu_address"],
                "byte_similarity": sim,
                "same_address": top["same_address"],
                "evidence_tier": tier,
            })
    rows.sort(key=lambda x: (x["build"], x["name"]))
    return rows


def build_report() -> dict:
    symbols = json.loads(SO_SYMBOLS.read_text(encoding="utf-8"))
    atlas = json.loads(WRAM.read_text(encoding="utf-8"))
    corpus = build_output()
    ram = build_ram_correspondences(symbols, atlas)
    functions = build_function_correspondences(corpus)
    return {
        "schema_version": 1,
        "method": {
            "functions": "top trusted semantic-anchor structural match",
            "ram": "named USA RAM symbol joined to consistent WRAM-motion projection",
            "ram_tiers": {
                "strong": "same USA field projected consistently in >=2 trusted anchors",
                "candidate": "consistent projection observed in one trusted anchor",
            },
            "warning": "cross-build correspondence does not imply identical behavior or field semantics",
        },
        "functions": functions,
        "ram": ram,
    }


def render_md(report: dict) -> str:
    lines = [
        "# Cross-build semantic symbol correspondence",
        "",
        "This surface joins named USA semantics to the strongest currently available PAL prototype and Europe retail structural correspondences. It is intended for debugging, decompilation, runtime probes, and future regional fidelity work.",
        "",
        "A mapped address means the structurally corresponding build-specific location supported by current evidence, not that the builds behave identically.",
        "",
        "## Trusted function anchors",
        "",
        "| Symbol | USA | Build | Candidate | Similarity | Tier |",
        "|---|---|---|---|---:|---|",
    ]
    for row in report["functions"]:
        if row["build"] == "legacy-beta":
            continue
        lines.append(
            f"| {row['name']} | `{row['usa']}` | {BUILD_LABELS[row['build']]} | "
            f"`{row['candidate']}` | {row['byte_similarity']:.3f} | {row['evidence_tier']} |"
        )

    lines += [
        "",
        "## Named RAM fields with repeated cross-anchor support",
        "",
        "| Symbol | USA | Build | Candidate | Delta | Anchors |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in report["ram"]:
        if row["build"] == "legacy-beta" or row["evidence_tier"] != "strong":
            continue
        lines.append(
            f"| {row['name']} | `{row['usa']}` | {BUILD_LABELS[row['build']]} | "
            f"`{row['candidate']}` | {row['delta']:+d} | {row['anchor_count']} |"
        )

    lines += [
        "",
        "## Single-anchor named RAM candidates",
        "",
        "These are useful search/probe targets, but should not be copied into authoritative build-specific symbol maps without another discriminator.",
        "",
        "| Symbol | USA | Build | Candidate | Delta | Source anchor |",
        "|---|---|---|---|---:|---|",
    ]
    for row in report["ram"]:
        if row["build"] == "legacy-beta" or row["evidence_tier"] != "candidate":
            continue
        lines.append(
            f"| {row['name']} | `{row['usa']}` | {BUILD_LABELS[row['build']]} | "
            f"`{row['candidate']}` | {row['delta']:+d} | {row['anchors'][0]} |"
        )

    lines += [
        "",
        "## Operational rule",
        "",
        "Use repeated-support mappings directly for build-specific watch/probe configuration. Use single-anchor candidates to target the cheapest independent check before semantic promotion.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(report), encoding="utf-8")
    print(OUT_JSON)
    print(OUT_MD)
    print("functions", len(report["functions"]))
    print("ram", len(report["ram"]))
    print("strong_ram", sum(r["evidence_tier"] == "strong" for r in report["ram"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
