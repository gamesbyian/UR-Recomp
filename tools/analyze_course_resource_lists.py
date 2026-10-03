#!/usr/bin/env python3
"""Analyze decoded course tail resource lists and build address-independent fingerprints.

This tool deliberately avoids assuming that equivalent resources keep the same
numeric ID or ROM address across builds. It fingerprints resource *usage shape*
across the 45-course corpus so likely equivalents can be proposed from course
incidence, list position, and track-slot context.

Raw decoded payloads are not committed; they are regenerated from the preserved
reference ROMs using the project-owned RNC Method 1 decoder.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path

from analyze_rnc_streams import ROMS, find_streams
from rnc_method1 import unpack_method1

ROOT = Path(__file__).resolve().parents[1]
JSON_OUT = ROOT / "analysis/generated/course-resource-list-manifest.json"
MD_OUT = ROOT / "analysis/generated/course-resource-list-manifest.md"

TRACK_SLOT = {
    1: "race-a",
    2: "circuit-a",
    3: "stunt",
    4: "race-b",
    5: "circuit-b",
}


def le16(data: bytes, off: int) -> int:
    if off < 0 or off + 2 > len(data):
        raise ValueError(f"LE16 out of range at 0x{off:X}")
    return data[off] | (data[off + 1] << 8)


def decode_dim(value: int) -> int:
    return 256 if value == 0 else value


def parse_course_resource_list(decoded: bytes) -> dict:
    if len(decoded) < 16:
        raise ValueError("decoded course payload too short for known header")

    cursor = le16(decoded, 0x0B)
    if not 0 <= cursor < len(decoded):
        raise ValueError(
            f"resource cursor 0x{cursor:04X} outside decoded payload "
            f"of 0x{len(decoded):04X} bytes"
        )

    ids: list[int] = []
    pos = cursor
    while pos < len(decoded):
        value = decoded[pos]
        if value == 0xFF:
            break
        ids.append(value)
        pos += 1
    else:
        raise ValueError(
            f"resource list at 0x{cursor:04X} has no FF terminator before EOF"
        )

    dim_a = decode_dim(decoded[0x0D])
    dim_b = decode_dim(decoded[0x0E])

    return {
        "decoded_size": len(decoded),
        "stunt_time_or_mode": decoded[0x02],
        "spawn_or_landmark_a": [le16(decoded, 0x03), le16(decoded, 0x05)],
        "spawn_or_landmark_b": [le16(decoded, 0x07), le16(decoded, 0x09)],
        "resource_cursor_initial": cursor,
        "resource_ids": ids,
        "resource_count": len(ids),
        "resource_terminator_offset": pos,
        "bytes_after_terminator": len(decoded) - (pos + 1),
        "layout_dims": [dim_a, dim_b],
        "layout_dim_product": dim_a * dim_b,
    }


def usage_fingerprint(occurrences: list[tuple[int, int, int]]) -> str:
    """Fingerprint where a resource appears, independent of the resource ID.

    Each tuple is (course_index, tour_slot, list_position). The resource's
    numeric ID and ROM address are intentionally absent.
    """
    normalized = ";".join(
        f"{course}:{slot}:{position}"
        for course, slot, position in sorted(occurrences)
    )
    return sha256(normalized.encode("ascii")).hexdigest()


def summarize_build(course_entries: list[dict]) -> dict:
    usage: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for course in course_entries:
        for position, resource_id in enumerate(course["resource_ids"]):
            usage[resource_id].append(
                (course["index"], course["tour_slot"], position)
            )

    resources = []
    for resource_id, occurrences in sorted(usage.items()):
        slots = Counter(slot for _, slot, _ in occurrences)
        positions = Counter(pos for _, _, pos in occurrences)
        courses = [course for course, _, _ in sorted(occurrences)]
        resources.append(
            {
                "resource_id": resource_id,
                "resource_id_hex": f"{resource_id:02X}",
                "occurrence_count": len(occurrences),
                "course_indices": courses,
                "tour_slot_counts": {
                    TRACK_SLOT[k]: slots[k] for k in sorted(slots)
                },
                "list_position_counts": {
                    str(k): positions[k] for k in sorted(positions)
                },
                "usage_fingerprint": usage_fingerprint(occurrences),
            }
        )

    return {
        "course_count": len(course_entries),
        "distinct_resource_ids": len(resources),
        "resources": resources,
    }


def build_cross_build_matches(builds: dict[str, dict]) -> list[dict]:
    """Find exact usage-shape matches across builds, allowing IDs to differ."""
    by_build: dict[str, dict[str, list[int]]] = {}
    for build_name, build in builds.items():
        index: dict[str, list[int]] = defaultdict(list)
        for resource in build["resource_usage"]["resources"]:
            index[resource["usage_fingerprint"]].append(resource["resource_id"])
        by_build[build_name] = dict(index)

    names = list(builds)
    matches = []
    for i, left_name in enumerate(names):
        for right_name in names[i + 1 :]:
            left = by_build[left_name]
            right = by_build[right_name]
            for fp in sorted(set(left) & set(right)):
                matches.append(
                    {
                        "left_build": left_name,
                        "right_build": right_name,
                        "left_resource_ids": left[fp],
                        "right_resource_ids": right[fp],
                        "same_numeric_ids": left[fp] == right[fp],
                        "usage_fingerprint": fp,
                    }
                )
    return matches


COMPARISON_FIELDS = (
    "stunt_time_or_mode",
    "spawn_or_landmark_a",
    "spawn_or_landmark_b",
    "resource_ids",
    "layout_dims",
)


def classify_resource_list_change(before: list[int], after: list[int]) -> dict:
    """Describe the cheapest exact edit when one list is a prefix of the other."""
    if before == after:
        return {"kind": "unchanged"}
    if after[: len(before)] == before:
        return {"kind": "append", "values": after[len(before) :]}
    if before[: len(after)] == after:
        return {"kind": "remove_suffix", "values": before[len(after) :]}
    return {"kind": "replace", "before": before, "after": after}


def compare_course_headers(reference: list[dict], candidate: list[dict]) -> list[dict]:
    """Return exact high-level course differences in stream-index order."""
    if len(reference) != len(candidate):
        raise ValueError("course corpora have different lengths")

    changes = []
    for expected, actual in zip(reference, candidate, strict=True):
        if expected["index"] != actual["index"]:
            raise ValueError("course corpora have different stream ordering")
        fields = {
            field: {"before": expected[field], "after": actual[field]}
            for field in COMPARISON_FIELDS
            if expected[field] != actual[field]
        }
        if fields:
            change = {"index": expected["index"], "fields": fields}
            if "resource_ids" in fields:
                change["resource_list_change"] = classify_resource_list_change(
                    expected["resource_ids"], actual["resource_ids"]
                )
            changes.append(change)
    return changes


def build_manifest() -> dict:
    builds: dict[str, dict] = {}

    for build_name, path in ROMS.items():
        rom_path = path if path.is_absolute() else ROOT / path
        rom = rom_path.read_bytes()
        courses = []
        for index, (_off, packed, _header) in enumerate(find_streams(rom), 1):
            decoded = unpack_method1(packed)
            parsed = parse_course_resource_list(decoded)
            tour_slot = ((index - 1) % 5) + 1
            courses.append(
                {
                    "index": index,
                    "tour_index": ((index - 1) // 5) + 1,
                    "tour_slot": tour_slot,
                    "track_kind": TRACK_SLOT[tour_slot],
                    **parsed,
                }
            )

        if len(courses) != 45:
            raise SystemExit(
                f"{build_name}: expected 45 course streams, got {len(courses)}"
            )

        builds[build_name] = {
            "path": str(path),
            "courses": courses,
            "resource_usage": summarize_build(courses),
        }

    reference_name = "usa-retail"
    reference_courses = builds[reference_name]["courses"]
    course_deltas = {
        build_name: compare_course_headers(reference_courses, build["courses"])
        for build_name, build in builds.items()
        if build_name != reference_name
    }

    return {
        "schema_version": 2,
        "method": {
            "resource_identity_rule": (
                "candidate equivalence is based on usage shape across courses, "
                "tour slots, and list positions; numeric IDs and ROM addresses "
                "are not part of the fingerprint"
            ),
            "caution": (
                "matching usage fingerprints are structural equivalence "
                "candidates, not semantic proof; promote only with descriptor, "
                "content, runtime, or behavior corroboration"
            ),
        },
        "builds": builds,
        "course_header_and_resource_deltas": {
            "reference_build": reference_name,
            "fields_compared": list(COMPARISON_FIELDS),
            "builds": course_deltas,
        },
        "cross_build_usage_matches": build_cross_build_matches(builds),
    }

def render_markdown(output: dict) -> str:
    builds = output["builds"]
    lines = [
        "# Course Resource-List Structural Fingerprints",
        "",
        "Generated by `tools/analyze_course_resource_lists.py`.",
        "",
        "This analysis intentionally does **not** require equivalent resources to "
        "share numeric IDs or ROM addresses. Resource candidates are fingerprinted "
        "by their occurrence pattern across courses, tour slots, and list positions.",
        "",
        "A matching fingerprint is a lead, not proof. Descriptor shape, content, "
        "runtime behavior, or another mechanical oracle must corroborate semantic "
        "equivalence before promotion.",
        "",
        "## Build summary",
        "",
        "| Build | Courses | Distinct resource IDs | Resource-count range |",
        "|---|---:|---:|---:|",
    ]

    for build_name, build in builds.items():
        counts = [course["resource_count"] for course in build["courses"]]
        lines.append(
            f"| {build_name} | {len(build['courses'])} | "
            f"{build['resource_usage']['distinct_resource_ids']} | "
            f"{min(counts)}..{max(counts)} |"
        )

    lines += [
        "",
        "## Course header and resource-list deltas",
        "",
        "Compared exactly against USA retail. An empty row means that all tracked "
        "header fields and resource-list IDs match in all 45 stream positions.",
        "",
        "| Build | Changed courses | Exact changes |",
        "|---|---:|---|",
    ]
    deltas = output["course_header_and_resource_deltas"]["builds"]
    for build_name, changes in deltas.items():
        descriptions = []
        for change in changes:
            fields = ", ".join(change["fields"])
            resource_change = change.get("resource_list_change")
            if resource_change and resource_change["kind"] == "append":
                values = " ".join(f"{value:02X}" for value in resource_change["values"])
                fields += f" (append `{values}`)"
            descriptions.append(f"#{change['index']}: {fields}")
        lines.append(
            f"| {build_name} | {len(changes)} | "
            f"{'<br>'.join(descriptions) if descriptions else 'none'} |"
        )

    lines += [
        "",
        "## Course tail lists",
        "",
        "| Build | Course | Slot | Cursor | IDs | FF offset | Bytes after FF | Dims |",
        "|---|---:|---|---:|---|---:|---:|---|",
    ]
    for build_name, build in builds.items():
        for course in build["courses"]:
            ids = " ".join(f"{x:02X}" for x in course["resource_ids"])
            dims = "×".join(str(x) for x in course["layout_dims"])
            lines.append(
                f"| {build_name} | {course['index']} | {course['track_kind']} | "
                f"`0x{course['resource_cursor_initial']:04X}` | `{ids}` | "
                f"`0x{course['resource_terminator_offset']:04X}` | "
                f"{course['bytes_after_terminator']} | {dims} |"
            )

    lines += [
        "",
        "## Cross-build address-independent matches",
        "",
        "Only exact usage-shape matches are listed here. Different numeric IDs with "
        "the same usage fingerprint are especially interesting because they are "
        "equivalence candidates that an address/ID-only pass would miss.",
        "",
        "| Left build | Left IDs | Right build | Right IDs | Same IDs? |",
        "|---|---|---|---|:---:|",
    ]
    for match in output["cross_build_usage_matches"]:
        left_ids = " ".join(f"{x:02X}" for x in match["left_resource_ids"])
        right_ids = " ".join(f"{x:02X}" for x in match["right_resource_ids"])
        lines.append(
            f"| {match['left_build']} | `{left_ids}` | "
            f"{match['right_build']} | `{right_ids}` | "
            f"{'yes' if match['same_numeric_ids'] else '**no**'} |"
        )

    return "\n".join(lines) + "\n"


def generated_contents(output: dict) -> dict[Path, str]:
    """Return every generated artifact and its canonical serialized content."""
    return {
        JSON_OUT: json.dumps(output, indent=2) + "\n",
        MD_OUT: render_markdown(output),
    }


def stale_outputs(expected: dict[Path, str]) -> list[Path]:
    """Return missing or stale artifacts without modifying the filesystem."""
    return [
        path
        for path, content in expected.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate or verify course resource-list manifests."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the checked-in manifests do not match the preserved ROM corpus",
    )
    args = parser.parse_args()

    output = build_manifest()
    expected = generated_contents(output)
    if args.check:
        stale = stale_outputs(expected)
        if stale:
            names = ", ".join(str(path.relative_to(ROOT)) for path in stale)
            raise SystemExit(f"stale course resource-list manifests: {names}")
        for path in expected:
            print(path.relative_to(ROOT))
        return

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")
    print(JSON_OUT)
    print(MD_OUT)


if __name__ == "__main__":
    main()
