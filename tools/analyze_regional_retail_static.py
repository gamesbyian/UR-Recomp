#!/usr/bin/env python3
"""Static USA-retail vs Europe-retail regional presentation inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
USA = Path("reference/roms/retail/Uniracers_USA.sfc")
EUROPE = Path("reference/roms/retail/Unirally_Europe.sfc")
COURSES = Path("analysis/data/course-corpus.json")
RESOURCES = Path("analysis/data/course-resource-catalog.json")

EXPECTED = {
    "usa": {
        "size": 2097152,
        "crc32": "383858c7",
        "sha1": "cb249cf7301bdd985e6fe4bc4c942bf4f86d7d83",
        "sha256": "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
        "header_title": "UNIRACERS",
        "region": 0x01,
    },
    "europe": {
        "size": 2097152,
        "crc32": "d8583ed7",
        "sha1": "d39ec113ef153ec9b7bacf12ed4a47f1a6d63a06",
        "sha256": "a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e",
        "header_title": "UNIRALLY",
        "region": 0x02,
    },
}

ASCII_RE = re.compile(rb"[ -~]{4,}")


def digest(data: bytes) -> dict[str, Any]:
    header = data[0x7FC0:0x8000]
    return {
        "size": len(data),
        "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08x}",
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "header_title": header[:21].decode("ascii", "replace").rstrip(),
        "region": header[0x19],
        "reset_vector": int.from_bytes(header[0x3C:0x3E], "little"),
    }


def validate_identity(label: str, facts: dict[str, Any]) -> None:
    for key, value in EXPECTED[label].items():
        if facts.get(key) != value:
            raise ValueError(
                f"{label} retail identity mismatch for {key}: "
                f"{facts.get(key)!r} != {value!r}"
            )


def rnc_streams(data: bytes) -> list[dict[str, Any]]:
    streams: list[dict[str, Any]] = []
    pos = 0
    while True:
        off = data.find(b"RNC", pos)
        if off < 0:
            break
        if off + 18 <= len(data) and data[off + 3] in (1, 2):
            unpacked = int.from_bytes(data[off + 4:off + 8], "big")
            packed = int.from_bytes(data[off + 8:off + 12], "big")
            end = off + 18 + packed
            if unpacked > 0 and packed > 0 and end <= len(data):
                raw = data[off:end]
                streams.append({
                    "offset": off,
                    "method": data[off + 3],
                    "unpacked": unpacked,
                    "packed": packed,
                    "packed_sha256": hashlib.sha256(raw).hexdigest(),
                })
        pos = off + 1
    return streams


def printable_strings(data: bytes) -> list[dict[str, Any]]:
    out = []
    for match in ASCII_RE.finditer(data):
        text = match.group().decode("ascii")
        if len(set(text)) == 1:
            continue
        out.append({"offset": match.start(), "text": text})
    return out


def unique_strings(left, right):
    right_text = {entry["text"] for entry in right}
    return [entry for entry in left if entry["text"] not in right_text]


def build_report(root: Path = ROOT) -> dict[str, Any]:
    usa = (root / USA).read_bytes()
    europe = (root / EUROPE).read_bytes()

    usa_identity = digest(usa)
    eur_identity = digest(europe)
    validate_identity("usa", usa_identity)
    validate_identity("europe", eur_identity)

    usa_rnc = rnc_streams(usa)
    eur_rnc = rnc_streams(europe)
    if len(usa_rnc) != 45 or len(eur_rnc) != 45:
        raise ValueError(
            f"expected 45 RNC streams per retail ROM, got "
            f"{len(usa_rnc)} and {len(eur_rnc)}"
        )

    changed = []
    for ordinal, pair in enumerate(zip(usa_rnc, eur_rnc), 1):
        u, e = pair
        if u["packed_sha256"] != e["packed_sha256"]:
            changed.append({
                "stream_index": ordinal,
                "usa": u,
                "europe": e,
                "decoded_size_delta": e["unpacked"] - u["unpacked"],
                "packed_size_delta": e["packed"] - u["packed"],
            })

    course_data = json.loads((root / COURSES).read_text(encoding="utf-8"))
    by_stream = {
        int(course["stream_index"]): course for course in course_data["courses"]
    }
    resource_data = json.loads((root / RESOURCES).read_text(encoding="utf-8"))
    deltas = resource_data["europe_retail_changed_course_resource_deltas"]
    changed_resource = {
        int(item["stream_index"]): item for item in deltas["changed_resource_lists"]
    }
    header_delta = {
        int(item["stream_index"]): item for item in deltas["other_header_deltas"]
    }

    for item in changed:
        idx = int(item["stream_index"])
        course = by_stream[idx]
        item["course"] = {
            "id": course["id"],
            "name": course["name"],
            "tour": course["tour"],
            "track_kind": course["track_kind"],
        }
        item["resource_list_status"] = (
            "changed" if idx in changed_resource else "unchanged"
        )
        if idx in changed_resource:
            item["resource_delta"] = changed_resource[idx]["edit"]
        if idx in header_delta:
            item["known_header_delta"] = header_delta[idx]["fields"]

    usa_strings = printable_strings(usa)
    eur_strings = printable_strings(europe)

    return {
        "schema_version": 1,
        "scope": "USA retail versus Europe retail static regional presentation inventory",
        "authority_note": (
            "Static differences are candidates only. Executable, timing, collision, "
            "or course-topology differences do not become regional-presentation "
            "features without independent player-visible evidence."
        ),
        "roms": {"usa": usa_identity, "europe": eur_identity},
        "rnc": {
            "usa_count": len(usa_rnc),
            "europe_count": len(eur_rnc),
            "byte_identical_count": 45 - len(changed),
            "changed_stream_indices": [x["stream_index"] for x in changed],
            "changed_streams": changed,
        },
        "known_resource_catalog_crosscheck": {
            "known_changed_streams": deltas["known_changed_streams"],
            "matches_rnc_scan": [x["stream_index"] for x in changed]
                == list(deltas["known_changed_streams"]),
        },
        "printable_strings": {
            "minimum_length": 4,
            "usa_candidate_count": len(usa_strings),
            "europe_candidate_count": len(eur_strings),
            "usa_only": unique_strings(usa_strings, eur_strings),
            "europe_only": unique_strings(eur_strings, usa_strings),
            "warning": (
                "Printable ROM strings are only candidates. Cross-check against "
                "framebuffer captures before classifying any as rendered UI/legal text."
            ),
        },
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Retail Regional Static Difference Inventory",
        "",
        "Generated by tools/analyze_regional_retail_static.py.",
        "",
        report["authority_note"],
        "",
        "## Verified retail identities",
        "",
        "| Release | CRC32 | SHA-1 | Header title | Region | Reset |",
        "|---|---|---|---|---:|---:|",
    ]
    for key, label in (("usa", "USA"), ("europe", "Europe")):
        item = report["roms"][key]
        lines.append(
            f"| {label} | {item['crc32']} | {item['sha1']} | "
            f"{item['header_title']} | 0x{item['region']:02X} | "
            f"0x{item['reset_vector']:04X} |"
        )

    rnc = report["rnc"]
    lines += [
        "",
        "## RNC/course payload differences",
        "",
        f"- byte-identical RNC streams by ordinal: {rnc['byte_identical_count']}/45",
        f"- changed ordinals: {', '.join(str(x) for x in rnc['changed_stream_indices'])}",
        f"- normalized catalog cross-check: "
        f"{'PASS' if report['known_resource_catalog_crosscheck']['matches_rnc_scan'] else 'FAIL'}",
        "",
        "| # | Course | Tour | Kind | decoded delta | resources | known structural delta |",
        "|---:|---|---|---|---:|---|---|",
    ]
    for item in rnc["changed_streams"]:
        structural = ""
        if "known_header_delta" in item:
            structural += "header: " + json.dumps(
                item["known_header_delta"], separators=(",", ":")
            )
        if "resource_delta" in item:
            if structural:
                structural += "; "
            structural += "resources: " + json.dumps(
                item["resource_delta"], separators=(",", ":")
            )
        if not structural:
            structural = "none promoted yet"
        lines.append(
            f"| {item['stream_index']} | {item['course']['name']} | "
            f"{item['course']['tour']} | {item['course']['track_kind']} | "
            f"{item['decoded_size_delta']:+d} | {item['resource_list_status']} | "
            f"{structural} |"
        )

    strings = report["printable_strings"]
    lines += [
        "",
        "## Candidate printable-string differences",
        "",
        f"- USA printable candidates: {strings['usa_candidate_count']}",
        f"- Europe printable candidates: {strings['europe_candidate_count']}",
        f"- USA-only exact strings: {len(strings['usa_only'])}",
        f"- Europe-only exact strings: {len(strings['europe_only'])}",
        "",
        strings["warning"],
        "",
        "### USA-only candidates",
        "",
    ]
    for item in strings["usa_only"][:100]:
        text = item["text"].replace("|", "\\|")
        lines.append(f"- 0x{item['offset']:06X}: {text}")
    lines += ["", "### Europe-only candidates", ""]
    for item in strings["europe_only"][:100]:
        text = item["text"].replace("|", "\\|")
        lines.append(f"- 0x{item['offset']:06X}: {text}")
    lines += [
        "",
        "Markdown candidate lists are capped at 100 entries; JSON retains all candidates.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()
    report = build_report()
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(markdown(report), encoding="utf-8")
    if not args.json_out and not args.md_out:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
