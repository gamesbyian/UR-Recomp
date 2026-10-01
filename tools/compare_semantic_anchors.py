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
        (0x0302, 0x0313, 0x033B, 0x033D,
         0x0411, 0x0413, 0x0415, 0x0417, 0x04B7, 0x04B9, 0x04BB, 0x04BD,
         0x04C7, 0x04C9, 0x04F5, 0x04F7, 0x0545,
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
         0x04C7, 0x04C9, 0x04F5, 0x04F7,
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
        "State053B_VramGate",
        "81:D2AA",
        0x28,
        (0x053B, 0x2116, 0x2118),
        "Bounded recovered VRAM/state gate beginning at 81:D2AA; used only to track unnamed $053B across builds.",
    ),
    Anchor(
        "Camera_StateQuantizeP2Tail",
        "81:B1CD",
        0x33,
        (0x050F, 0x0513, 0x0535, 0x0539),
        "Bounded recovered camera-state quantization tail through the join at 81:B1FF; used to discriminate the upper edge of the +4 WRAM family.",
    ),
    Anchor(
        "Camera_StateQuantizeP1",
        "81:AEF1",
        0xD2,
        (0x04F5, 0x0505, 0x0507, 0x0509, 0x050D, 0x050F, 0x0511, 0x051D,
         0x0521, 0x052B, 0x052F, 0x0533, 0x0537),
        "Bounded Nitrodon player-1 camera-state quantization path through RTS at 81:AFC2; spans the suspected +4→+6 WRAM lineage boundary and includes both sides of the internal quantization state.",
    ),
    Anchor(
        "Camera_MapGeometrySetup",
        "81:A50E",
        0x1D,
        (0x04F1, 0x04F3, 0x0553, 0x0DD9),
        "Recovered Nitrodon setup block: map-width geometry and derived camera/map state through RTS at 81:A52A.",
    ),
    Anchor(
        "Camera_UpdatePersistentState",
        "81:A52F",
        0x70,
        (0x0419, 0x041B, 0x041D, 0x041F, 0x04F5, 0x04F7, 0x04F9, 0x04FB,
         0x0BE9, 0x0BEB, 0x0D49, 0x0DDB),
        "Recovered camera-position update block spanning both player camera state paths.",
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
        (0x0230, 0x0232, 0x0234, 0x0236, 0x0260, 0x0262, 0x0264, 0x0266, 0x026A,
         0x033B, 0x033D, 0x042B, 0x042F, 0x0545,
         0x0F61, 0x11F9, 0x11FD, 0x1201, 0x1205, 0x12AF, 0x1361),
        "Landing-time stunt classification, messages, counters, and score path.",
    ),
    Anchor(
        "Input_CaptureAutoJoypad",
        "80:85E4",
        0x20,
        (0x030D, 0x030E, 0x030F, 0x0310,
         0x4218, 0x4219, 0x421A, 0x421B, 0x421C, 0x421D, 0x421E, 0x421F),
        "Recovered auto-joypad capture sequence; tracks whether Europe expanded the four-byte raw-controller capture area or added extra controller-register reads.",
    ),
    Anchor(
        "Text_TestCharacterMetadataBit7",
        "80:8C41",
        0x0D,
        (0xC6F8,),
        "Recovered shared text/layout helper: indexes the character-metadata table and tests bit 7.",
    ),
    Anchor(
        "Player_ApplyVerticalAcceleration",
        "82:A968",
        0x44,
        (0x0F41, 0x0FEF, 0x0541, 0x0FA1),
        "Recovered Nitrodon routine: bounded vertical-acceleration update through RTS at 82:A9AB.",
    ),
    Anchor(
        "State0309_TextLoopCounter",
        "81:BF6D",
        0x50,
        (0x0309, 0x1283, 0x12A5, 0x0E9D, 0x0EDD),
        "Bounded recovered text/state loop through the first return path; used only to track unnamed $0309 across builds.",
    ),
    Anchor(
        "State0306_DmaGate",
        "82:B8AB",
        0x40,
        (0x0306, 0x420B, 0x2115, 0x2116),
        "Bounded recovered routine beginning at 82:B8AB; used only to track the unnamed $0306 state slot across builds without assigning semantics.",
    ),
    Anchor(
        "Input_DecodePlayer1Buttons",
        "82:AA6E",
        0x200,
        (0x12D5, 0x0325, 0x0329, 0x0319, 0x032D, 0x0321, 0x031D,
         0x0331, 0x0335, 0x0315, 0x030D, 0x030F, 0x0311),
        "Recovered Nitrodon input decoder; 0x200-byte structural window covers the P1 decode and mirrored P2 setup.",
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


def semantic_word_projection(source: bytes, candidate: bytes, words: tuple[int, ...]) -> dict[str, dict]:
    """Project known USA word operands through a structurally aligned candidate window.

    For every occurrence of a known semantic LE16 word in the USA window, read
    the candidate word at the same relative offset. Repeated agreement on a new
    value is evidence for a build-specific address translation, even when the
    original literal address disappears.
    """
    out = {}
    for word in words:
        token = word.to_bytes(2, "little")
        positions = []
        pos = source.find(token)
        while pos >= 0:
            if pos + 2 <= len(candidate):
                positions.append(pos)
            pos = source.find(token, pos + 1)
        if not positions:
            continue
        vals = Counter(int.from_bytes(candidate[pos:pos+2], "little") for pos in positions)
        out[f"{word:04X}"] = {
            "source_occurrences": len(positions),
            "candidate_values": {
                f"{value:04X}": count
                for value, count in vals.most_common()
            },
            "dominant_candidate": f"{vals.most_common(1)[0][0]:04X}",
            "dominant_count": vals.most_common(1)[0][1],
        }
    return out


def similarity(a: bytes, b: bytes) -> float:
    n = min(len(a), len(b))
    if not n:
        return 0.0
    return sum(x == y for x, y in zip(a[:n], b[:n])) / n


def compact_diff_runs(a: bytes, b: bytes, *, max_runs: int = 24) -> list[dict]:
    """Return bounded relative byte-difference runs for structural inspection."""
    n = min(len(a), len(b))
    runs = []
    i = 0
    while i < n:
        if a[i] == b[i]:
            i += 1
            continue
        start = i
        while i < n and a[i] != b[i]:
            i += 1
        end = i
        runs.append({
            "relative_start": start,
            "relative_end_exclusive": end,
            "length": end - start,
            "usa_hex": a[start:end].hex(),
            "candidate_hex": b[start:end].hex(),
        })
        if len(runs) >= max_runs:
            break
    return runs


def changed_le16_pairs(a: bytes, b: bytes, *, max_pairs: int = 32) -> list[dict]:
    """Surface changed little-endian word-sized operands without claiming semantics."""
    out = []
    n = min(len(a), len(b))
    seen = set()
    for i in range(n - 1):
        if a[i:i+2] == b[i:i+2]:
            continue
        # Prefer windows where at least one adjacent byte survives, which is common
        # for relocated addresses/constants and avoids flooding on long rewrites.
        if i and a[i-1] != b[i-1] and i + 2 < n and a[i+2] != b[i+2]:
            continue
        key = (i, a[i:i+2], b[i:i+2])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "relative_offset": i,
            "usa_le16": int.from_bytes(a[i:i+2], "little"),
            "candidate_le16": int.from_bytes(b[i:i+2], "little"),
            "usa_hex": a[i:i+2].hex(),
            "candidate_hex": b[i:i+2].hex(),
        })
        if len(out) >= max_pairs:
            break
    return out


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
            "semantic_word_projection": semantic_word_projection(
                source, region, anchor.semantic_words
            ),
            "diff_runs": compact_diff_runs(source, region),
            "changed_le16_pairs": changed_le16_pairs(source, region),
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




def build_translation_summary(output: dict) -> dict:
    summary = {}
    for anchor in output["anchors"]:
        for build_name, matches in anchor["matches"].items():
            if not matches:
                continue
            top = matches[0]
            if top["byte_similarity"] < 0.60:
                continue
            b = summary.setdefault(build_name, {
                "pairs": {},
                "delta_counts": {},
                "evidence": [],
            })
            for usa_hex, proj in top["semantic_word_projection"].items():
                cand_hex = proj["dominant_candidate"]
                if proj["dominant_count"] < 1:
                    continue
                usa = int(usa_hex, 16)
                cand = int(cand_hex, 16)
                delta = (cand - usa) & 0xFFFF
                key = f"{usa_hex}->{cand_hex}"
                b["pairs"][key] = b["pairs"].get(key, 0) + proj["dominant_count"]
                dkey = f"{delta:04X}"
                b["delta_counts"][dkey] = b["delta_counts"].get(dkey, 0) + proj["dominant_count"]
                b["evidence"].append({
                    "anchor": anchor["name"],
                    "usa_word": usa_hex,
                    "candidate_word": cand_hex,
                    "delta": dkey,
                    "count": proj["dominant_count"],
                    "candidate_cpu": top["cpu_address"],
                    "byte_similarity": top["byte_similarity"],
                })
    return summary

def build_output(*, top: int = 5, ngram: int = 6, stride: int = 3) -> dict:
    """Build the machine-readable correspondence corpus without writing files."""
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
                top=top,
                k=ngram,
                stride=stride,
            )
        output["anchors"].append(item)

    output["translation_summary"] = build_translation_summary(output)
    return output


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5, help="candidate matches per anchor/build")
    ap.add_argument("--ngram", type=int, default=6, help="byte n-gram length")
    ap.add_argument("--stride", type=int, default=3, help="anchor n-gram sampling stride")
    args = ap.parse_args()

    output = build_output(top=args.top, ngram=args.ngram, stride=args.stride)

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

    lines += [
        "## Cross-build semantic-word translation summary",
        "",
        "These are mechanically projected USA LE16 semantic operands from each "
        "top structurally aligned candidate. Repeated deltas across unrelated "
        "anchors are useful evidence of build-specific WRAM layout shifts; "
        "individual pairs are not promoted without context.",
        "",
    ]
    for build_name, translation in output["translation_summary"].items():
        deltas = sorted(
            translation["delta_counts"].items(),
            key=lambda kv: kv[1],
            reverse=True,
        )
        lines += [f"### {build_name}", "", "| Delta | Evidence count |", "|---:|---:|"]
        for delta, count in deltas[:12]:
            signed = int(delta, 16)
            if signed >= 0x8000:
                signed -= 0x10000
            lines.append(f"| `{signed:+d}` (`0x{delta}`) | {count} |")
        lines.append("")

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
        # Only the top candidate gets byte-delta detail in Markdown. JSON retains
        # bounded delta summaries for every reported candidate.
        for build_name, matches in anchor["matches"].items():
            if not matches:
                continue
            top_match = matches[0]
            lines += [
                f"### {build_name} top-candidate deltas",
                "",
                f"Top candidate: `{top_match['cpu_address']}`; "
                f"byte similarity {top_match['byte_similarity']:.3f}; "
                f"semantic-reference recall {top_match['semantic_reference_recall']:.3f}.",
                "",
                "| Rel | Len | USA | Candidate |",
                "|---:|---:|---|---|",
            ]
            for run in top_match["diff_runs"]:
                lines.append(
                    f"| `+0x{run['relative_start']:X}` | {run['length']} | "
                    f"`{run['usa_hex']}` | `{run['candidate_hex']}` |"
                )
            lines.append("")
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_JSON)
    print(OUT_MD)


if __name__ == "__main__":
    main()
