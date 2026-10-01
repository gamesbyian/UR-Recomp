#!/usr/bin/env python3
"""Match trusted USA semantic anchors across preserved ROM builds without assuming address identity.

Candidate generation is relocation-tolerant: short byte n-grams from a trusted USA
anchor vote for candidate starts in another ROM. Candidate ranking then combines
those votes with byte similarity and the anchor's already-understood WRAM/PPU
reference signature.

This is deliberately a correspondence *proposal* tool, not a semantic oracle.
A high-scoring match should still be corroborated by control flow, callers/callees,
runtime participation, or another project-owned discriminator before labels are
promoted across builds.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import argparse
import hashlib
import json

ROMS = {
    "usa-retail": Path("reference/roms/retail/Uniracers_USA.sfc"),
    "europe-retail": Path("reference/roms/retail/Unirally_Europe.sfc"),
    "legacy-beta": Path("reference/roms/prototypes/Uniracers_Beta_legacy.sfc"),
    "pal-prototype-1994-11-29": Path("reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"),
}

OUT_JSON = Path("analysis/generated/semantic-anchor-cross-build-matches.json")
OUT_MD = Path("analysis/generated/semantic-anchor-cross-build-matches.md")


@dataclass(frozen=True)
class Anchor:
    name: str
    cpu: str
    size: int
    semantic_words: tuple[int, ...]
    note: str


ANCHORS = (
    Anchor(
        "Race_UpdateRacersFrame",
        "82:89B9",
        0x500,
        (0x0411, 0x0413, 0x0415, 0x0417, 0x04B7, 0x04B9, 0x04BB, 0x04BD,
         0x0F49, 0x0F9F, 0x0FA1, 0x0FEF, 0x11CD, 0x11CF, 0x11D1),
        "P1/P2 persistent-state marshal into shared current-player simulation workspace.",
    ),
    Anchor(
        "Course_LoadAndMaterialize",
        "82:E165",
        0x240,
        (0x000B, 0x0E89, 0x0E8B, 0x0E8D, 0x0E8F, 0x0E91, 0x0E93,
         0x15A1, 0x1645, 0x16E9, 0x2100, 0x2115, 0x2116, 0x420B, 0x420C),
        "Decoded-course loader, tail resource-list walker, and A000/C000 materializer.",
    ),
    Anchor(
        "Race_BuildRacerOAMState",
        "82:ACA5",
        0x380,
        (0x0411, 0x0413, 0x0415, 0x0417, 0x0419, 0x041D, 0x0421, 0x0423,
         0x0BA1, 0x0BA3, 0x0D49, 0x1509, 0x150A, 0x150D, 0x150E),
        "World/camera to screen/OAM projection boundary.",
    ),
    Anchor(
        "Race_HandleCheckpointFinish",
        "81:8050",
        0x1E0,
        (0x0EF1, 0x0EF3, 0x1199, 0x119B, 0x119D, 0x119F),
        "Checkpoint/lap/final-finish state machine.",
    ),
    Anchor(
        "HUD_QueueMessage",
        "81:C5B3",
        0xC0,
        (0x0CBB, 0x0CE1, 0x0CE3, 0x0CE5, 0x0D0B, 0x0D0D),
        "Per-player 32-entry stunt/HUD message-ring enqueue path.",
    ),
    Anchor(
        "Collision_BuildContactShape",
        "81:9E2A",
        0x220,
        (0x0F47, 0x0F7B, 0x125B),
        "Orientation-dependent collision/contact-shape construction.",
    ),
    Anchor(
        "Collision_TransformVelocity",
        "81:9546",
        0xE0,
        (0x02C0, 0x02C2, 0x02C4, 0x02C6, 0x0F9F, 0x0FA1),
        "2x2 current-player velocity transform used by collision response.",
    ),
    Anchor(
        "Stunt_FinalizeAndScoreAirTricks",
        "82:9A42",
        0x380,
        (0x042B, 0x042F, 0x0F61, 0x11F9, 0x11FD, 0x1201, 0x1205,
         0x12AF, 0x1361),
        "Landing-time stunt classification, messages, counters, and score path.",
    ),
)


def cpu_to_lorom_file(cpu: str) -> int:
    bank_s, addr_s = cpu.split(":")
    bank = int(bank_s, 16)
    addr = int(addr_s, 16)
    if addr < 0x8000:
        raise ValueError(f"{cpu}: LoROM ROM address must be >= $8000")
    return ((bank & 0x7F) * 0x8000) + (addr & 0x7FFF)


def file_to_lorom_cpu(off: int) -> str:
    bank = (off // 0x8000) | 0x80
    addr = (off % 0x8000) | 0x8000
    return f"{bank:02X}:{addr:04X}"


def semantic_hits(blob: bytes, start: int, size: int, words: tuple[int, ...]) -> dict[str, int]:
    region = blob[start:start + size]
    out = {}
    for word in words:
        token = word.to_bytes(2, "little")
        count = region.count(token)
        if count:
            out[f"{word:04X}"] = count
    return out


def similarity(a: bytes, b: bytes) -> float:
    n = min(len(a), len(b))
    if not n:
        return 0.0
    return sum(x == y for x, y in zip(a[:n], b[:n])) / n


def ngram_votes(anchor: bytes, target: bytes, *, k: int, stride: int, max_hits: int) -> Counter[int]:
    votes: Counter[int] = Counter()
    seen = set()
    for rel in range(0, max(0, len(anchor) - k + 1), stride):
        gram = anchor[rel:rel + k]
        if gram in seen:
            continue
        seen.add(gram)
        if len(set(gram)) <= 2:
            continue

        pos = target.find(gram)
        hits = 0
        while pos >= 0 and hits < max_hits:
            start = pos - rel
            if 0 <= start <= len(target) - len(anchor):
                votes[start] += 1
            hits += 1
            pos = target.find(gram, pos + 1)
    return votes


def score_candidates(anchor: Anchor, usa: bytes, target: bytes, *, top: int, k: int, stride: int) -> list[dict]:
    usa_start = cpu_to_lorom_file(anchor.cpu)
    source = usa[usa_start:usa_start + anchor.size]
    if len(source) != anchor.size:
        raise ValueError(f"{anchor.name}: anchor window exceeds USA ROM")

    source_sem = semantic_hits(usa, usa_start, anchor.size, anchor.semantic_words)
    votes = ngram_votes(source, target, k=k, stride=stride, max_hits=32)

    # Same-offset is always considered, but receives no privileged score.
    votes.setdefault(usa_start, 0)

    candidates = []
    for start, vote_count in votes.most_common(max(top * 12, 48)):
        if start + anchor.size > len(target):
            continue
        region = target[start:start + anchor.size]
        sem = semantic_hits(target, start, anchor.size, anchor.semantic_words)

        source_keys = set(source_sem)
        sem_keys = set(sem)
        sem_recall = (len(source_keys & sem_keys) / len(source_keys)) if source_keys else 1.0
        byte_similarity = similarity(source, region)

        # N-gram votes are candidate-generation evidence; semantic references
        # and byte shape dominate final ranking.
        max_votes = max(votes.values()) if votes else 1
        vote_fraction = vote_count / max_votes if max_votes else 0.0
        score = 0.50 * byte_similarity + 0.35 * sem_recall + 0.15 * vote_fraction

        candidates.append({
            "file_offset": start,
            "cpu_address": file_to_lorom_cpu(start),
            "same_offset_as_usa": start == usa_start,
            "score": round(score, 6),
            "byte_similarity": round(byte_similarity, 6),
            "semantic_reference_recall": round(sem_recall, 6),
            "ngram_vote_fraction": round(vote_fraction, 6),
            "ngram_votes": vote_count,
            "semantic_hits": sem,
            "sha256": hashlib.sha256(region).hexdigest(),
        })

    candidates.sort(
        key=lambda x: (
            x["score"],
            x["semantic_reference_recall"],
            x["byte_similarity"],
            x["ngram_votes"],
        ),
        reverse=True,
    )
    return candidates[:top]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5, help="candidate matches per anchor/build")
    ap.add_argument("--ngram", type=int, default=6, help="byte n-gram length")
    ap.add_argument("--stride", type=int, default=3, help="anchor n-gram sampling stride")
    args = ap.parse_args()

    blobs = {name: path.read_bytes() for name, path in ROMS.items()}
    usa = blobs["usa-retail"]

    output = {
        "schema_version": 1,
        "method": {
            "candidate_generation": "relocation-tolerant byte n-gram voting",
            "corroboration": "byte-shape similarity plus known WRAM/PPU semantic-reference recall",
            "important": "same absolute address is considered but is not privileged",
            "promotion_rule": (
                "top matches are correspondence candidates only; propagate semantic labels "
                "after control-flow/caller/callee/runtime/table corroboration"
            ),
        },
        "anchors": [],
    }

    for anchor in ANCHORS:
        usa_start = cpu_to_lorom_file(anchor.cpu)
        usa_sem = semantic_hits(usa, usa_start, anchor.size, anchor.semantic_words)
        item = {
            "name": anchor.name,
            "usa_cpu_address": anchor.cpu,
            "usa_file_offset": usa_start,
            "window_size": anchor.size,
            "note": anchor.note,
            "semantic_words": [f"{x:04X}" for x in anchor.semantic_words],
            "usa_semantic_hits": usa_sem,
            "matches": {},
        }
        for build_name, blob in blobs.items():
            if build_name == "usa-retail":
                continue
            item["matches"][build_name] = score_candidates(
                anchor,
                usa,
                blob,
                top=args.top,
                k=args.ngram,
                stride=args.stride,
            )
        output["anchors"].append(item)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Cross-build Semantic Anchor Correspondence",
        "",
        "Generated by `tools/compare_semantic_anchors.py`.",
        "",
        "This report deliberately does not equate identity with absolute address. "
        "Short byte n-grams propose relocated candidates; ranking combines byte-shape "
        "similarity with recall of the anchor's already-understood WRAM/PPU references. "
        "Same-offset matches are shown but receive no special weighting.",
        "",
        "Matches are **candidates, not semantic proof**. Promote a label across builds "
        "only after a second structural or runtime discriminator agrees.",
        "",
    ]

    for anchor in output["anchors"]:
        lines += [
            f"## {anchor['name']}",
            "",
            f"USA anchor: `{anchor['usa_cpu_address']}` / file "
            f"`0x{anchor['usa_file_offset']:06X}`; window `0x{anchor['window_size']:X}`.",
            "",
            anchor["note"],
            "",
            "| Build | Rank | Candidate | Same offset? | Score | Byte similarity | Semantic-ref recall | N-gram votes |",
            "|---|---:|---|:---:|---:|---:|---:|---:|",
        ]
        for build_name, matches in anchor["matches"].items():
            for rank, match in enumerate(matches, 1):
                lines.append(
                    f"| {build_name} | {rank} | `{match['cpu_address']}` "
                    f"(`0x{match['file_offset']:06X}`) | "
                    f"{'yes' if match['same_offset_as_usa'] else 'no'} | "
                    f"{match['score']:.3f} | {match['byte_similarity']:.3f} | "
                    f"{match['semantic_reference_recall']:.3f} | {match['ngram_votes']} |"
                )
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_JSON)
    print(OUT_MD)


if __name__ == "__main__":
    main()
