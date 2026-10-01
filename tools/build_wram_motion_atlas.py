#!/usr/bin/env python3
"""Build a bounded cross-build WRAM motion atlas from trusted semantic anchors.

This consumes the same deterministic correspondence corpus as
compare_semantic_anchors.py, then clusters structurally aligned semantic operands
by build-specific displacement and co-occurrence. Clusters are structural
evidence only; they do not promote field semantics by themselves.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json

try:
    from tools.compare_semantic_anchors import build_output
except ModuleNotFoundError:
    from compare_semantic_anchors import build_output

OUT_JSON = Path("analysis/generated/wram-motion-atlas.json")
OUT_MD = Path("analysis/generated/wram-motion-atlas.md")

MIN_SIMILARITY = 0.60
NON_WRAM_ANCHORS = {"Text_TestCharacterMetadataBit7"}


def signed_delta(usa: int, candidate: int) -> int:
    delta = (candidate - usa) & 0xFFFF
    return delta - 0x10000 if delta >= 0x8000 else delta


def collect_motion_rows(corpus: dict, *, min_similarity: float = MIN_SIMILARITY) -> list[dict]:
    rows = []
    for anchor in corpus["anchors"]:
        if anchor["name"] in NON_WRAM_ANCHORS:
            continue
        for build, matches in anchor["matches"].items():
            if not matches:
                continue
            top = matches[0]
            if top["byte_similarity"] < min_similarity:
                continue
            for usa_hex, projection in top["semantic_word_projection"].items():
                candidate_hex = projection["dominant_candidate"]
                usa = int(usa_hex, 16)
                candidate = int(candidate_hex, 16)
                rows.append({
                    "build": build,
                    "anchor": anchor["name"],
                    "anchor_candidate_cpu": top["cpu_address"],
                    "anchor_byte_similarity": top["byte_similarity"],
                    "usa_word": usa_hex,
                    "candidate_word": candidate_hex,
                    "delta": signed_delta(usa, candidate),
                    "evidence_count": projection["dominant_count"],
                    "source_occurrences": projection["source_occurrences"],
                })
    return rows


def summarize(rows: list[dict]) -> dict:
    by_build_delta: dict[tuple[str, int], list[dict]] = defaultdict(list)
    per_field: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        by_build_delta[(row["build"], row["delta"])].append(row)
        per_field[(row["build"], row["usa_word"])].append(row)

    clusters = []
    for (build, delta), members in by_build_delta.items():
        anchors = sorted({m["anchor"] for m in members})
        usa_words = sorted({m["usa_word"] for m in members})
        candidate_words = sorted({m["candidate_word"] for m in members})
        clusters.append({
            "build": build,
            "delta": delta,
            "evidence_count": sum(m["evidence_count"] for m in members),
            "observation_count": len(members),
            "anchor_count": len(anchors),
            "field_count": len(usa_words),
            "anchors": anchors,
            "usa_words": usa_words,
            "candidate_words": candidate_words,
        })
    clusters.sort(
        key=lambda c: (
            c["build"],
            -c["anchor_count"],
            -c["evidence_count"],
            c["delta"],
        )
    )

    field_consistency = []
    for (build, usa_word), members in sorted(per_field.items()):
        candidates = sorted({m["candidate_word"] for m in members})
        deltas = sorted({m["delta"] for m in members})
        anchors = sorted({m["anchor"] for m in members})
        field_consistency.append({
            "build": build,
            "usa_word": usa_word,
            "candidate_words": candidates,
            "deltas": deltas,
            "anchors": anchors,
            "consistent": len(candidates) == 1 and len(deltas) == 1,
        })

    contradictions = [x for x in field_consistency if not x["consistent"]]
    lineage_motion = build_lineage_motion(field_consistency)
    return {
        "schema_version": 2,
        "method": {
            "source": "top structural candidates from tools/compare_semantic_anchors.py",
            "minimum_byte_similarity": MIN_SIMILARITY,
            "interpretation": (
                "shared displacement/co-occurrence is evidence of logical field grouping; "
                "clusters are not semantic-label promotion"
            ),
        },
        "rows": rows,
        "clusters": clusters,
        "field_consistency": field_consistency,
        "contradictions": contradictions,
        "prototype_to_europe_motion": lineage_motion,
    }




def infer_secondary_motion_boundaries(rows: list[dict]) -> list[dict]:
    """Bracket post-prototype displacement changes in USA address order."""
    ordered = sorted(rows, key=lambda r: int(r["usa_word"], 16))
    out = []
    for left, right in zip(ordered, ordered[1:]):
        ld = left["prototype_to_europe_delta"]
        rd = right["prototype_to_europe_delta"]
        if ld == rd:
            continue
        la = int(left["usa_word"], 16)
        ra = int(right["usa_word"], 16)
        # Ignore jumps into MMIO/high address spaces; the useful boundaries are
        # within the low WRAM/state address corpus.
        if la >= 0x2000 or ra >= 0x2000:
            continue
        out.append({
            "from_delta": ld,
            "to_delta": rd,
            "delta_jump": rd - ld,
            "last_known_before": left["usa_word"],
            "first_known_after": right["usa_word"],
            "address_gap_bytes": ra - la,
            "prototype_last_before": left["prototype_word"],
            "prototype_first_after": right["prototype_word"],
            "europe_last_before": left["europe_word"],
            "europe_first_after": right["europe_word"],
        })
    return out


def build_lineage_motion(field_consistency: list[dict]) -> dict:
    """Compare the same USA fields between PAL prototype and Europe retail.

    This isolates layout motion that happened after the 1994-11-29 prototype.
    Only fields with a single consistent candidate in both builds are admitted.
    """
    by_key = {(r["build"], r["usa_word"]): r for r in field_consistency if r["consistent"]}
    rows = []
    for (build, usa_word), proto in sorted(by_key.items()):
        if build != "pal-prototype-1994-11-29":
            continue
        europe = by_key.get(("europe-retail", usa_word))
        if not europe:
            continue
        proto_candidate = int(proto["candidate_words"][0], 16)
        europe_candidate = int(europe["candidate_words"][0], 16)
        secondary = signed_delta(proto_candidate, europe_candidate)
        rows.append({
            "usa_word": usa_word,
            "prototype_word": proto["candidate_words"][0],
            "europe_word": europe["candidate_words"][0],
            "prototype_delta_from_usa": proto["deltas"][0],
            "europe_delta_from_usa": europe["deltas"][0],
            "prototype_to_europe_delta": secondary,
            "prototype_anchors": proto["anchors"],
            "europe_anchors": europe["anchors"],
        })

    clusters: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        clusters[row["prototype_to_europe_delta"]].append(row)

    summary = []
    for delta, members in clusters.items():
        summary.append({
            "prototype_to_europe_delta": delta,
            "field_count": len(members),
            "usa_words": [m["usa_word"] for m in members],
            "prototype_words": [m["prototype_word"] for m in members],
            "europe_words": [m["europe_word"] for m in members],
        })
    summary.sort(key=lambda x: (-x["field_count"], x["prototype_to_europe_delta"]))
    return {
        "rows": rows,
        "clusters": summary,
        "inferred_boundaries": infer_secondary_motion_boundaries(rows),
    }


def render_markdown(atlas: dict) -> str:
    lines = [
        "# Cross-build WRAM Motion Atlas",
        "",
        "Generated by `tools/build_wram_motion_atlas.py` from the trusted semantic-anchor corpus.",
        "",
        "This is a structural clustering surface. Repeated displacement across independent matched routines can support a shared logical-layout hypothesis, but it does not by itself prove field meaning or chronology.",
        "",
        "## High-support displacement clusters",
        "",
        "| Build | Delta | Anchors | Fields | Evidence | Example USA fields |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for c in atlas["clusters"]:
        if c["anchor_count"] < 2:
            continue
        examples = ", ".join(f"`{w}`" for w in c["usa_words"][:8])
        lines.append(
            f"| {c['build']} | {c['delta']:+d} | {c['anchor_count']} | "
            f"{c['field_count']} | {c['evidence_count']} | {examples} |"
        )

    lines += [
        "",
        "## Cross-anchor field consistency",
        "",
        "A field is listed here when the same USA address appears in more than one trusted anchor. Consistent repeated projection is stronger structural evidence than a single occurrence.",
        "",
        "| Build | USA field | Candidate | Delta | Anchors |",
        "|---|---|---|---:|---|",
    ]
    for f in atlas["field_consistency"]:
        if len(f["anchors"]) < 2 or not f["consistent"]:
            continue
        lines.append(
            f"| {f['build']} | `{f['usa_word']}` | `{f['candidate_words'][0]}` | "
            f"{f['deltas'][0]:+d} | {', '.join(f['anchors'])} |"
        )

    lines += [
        "",
        "## PAL prototype → Europe retail secondary motion",
        "",
        "For fields consistently projected in both builds, this subtracts the prototype address from the Europe address. The result isolates layout motion that occurred after the 1994-11-29 prototype.",
        "",
        "| Prototype→Europe delta | Fields | Example USA→prototype→Europe paths |",
        "|---:|---:|---|",
    ]
    lineage_rows = {r["usa_word"]: r for r in atlas["prototype_to_europe_motion"]["rows"]}
    for cluster in atlas["prototype_to_europe_motion"]["clusters"]:
        examples = []
        for usa_word in cluster["usa_words"][:6]:
            r = lineage_rows[usa_word]
            examples.append(
                f"`{usa_word}→{r['prototype_word']}→{r['europe_word']}`"
            )
        lines.append(
            f"| {cluster['prototype_to_europe_delta']:+d} | {cluster['field_count']} | "
            f"{', '.join(examples)} |"
        )

    lines += [
        "",
        "## Inferred post-prototype insertion brackets",
        "",
        "These are address-space brackets, not exact insertion addresses. A displacement jump means some later-added/expanded state lies after the last known field in the old family and no later than the first known field in the new family.",
        "",
        "| From delta | To delta | Jump | Last known before | First known after | USA-address gap |",
        "|---:|---:|---:|---|---|---:|",
    ]
    for b in atlas["prototype_to_europe_motion"]["inferred_boundaries"]:
        lines.append(
            f"| {b['from_delta']:+d} | {b['to_delta']:+d} | {b['delta_jump']:+d} | "
            f"`{b['last_known_before']}` | `{b['first_known_after']}` | "
            f"{b['address_gap_bytes']} |"
        )

    lines += [
        "",
        "## Contradictions / exceptions",
        "",
    ]
    if not atlas["contradictions"]:
        lines.append("No trusted USA field projected to conflicting candidate addresses across the accepted top-match corpus.")
    else:
        lines += [
            "| Build | USA field | Candidate values | Deltas | Anchors |",
            "|---|---|---|---|---|",
        ]
        for f in atlas["contradictions"]:
            lines.append(
                f"| {f['build']} | `{f['usa_word']}` | "
                f"{', '.join(f['candidate_words'])} | "
                f"{', '.join(f'{d:+d}' for d in f['deltas'])} | "
                f"{', '.join(f['anchors'])} |"
            )

    lines += [
        "",
        "## Use",
        "",
        "- Prefer clusters supported by multiple independent anchors when inferring a build-specific logical block.",
        "- Treat structure-specific displacement families as evidence against a single global WRAM relocation.",
        "- Use prototype→Europe secondary motion to infer later insertions/repacking without conflating them with earlier USA→prototype layout changes.",
        "- Investigate exceptions first when they intersect current physics, course, rendering, or fidelity questions.",
        "- Do not transfer semantic labels from USA solely because an address follows a dominant displacement family.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    corpus = build_output()
    atlas = summarize(collect_motion_rows(corpus))
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(atlas, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(atlas), encoding="utf-8")
    print(OUT_JSON)
    print(OUT_MD)


if __name__ == "__main__":
    main()
