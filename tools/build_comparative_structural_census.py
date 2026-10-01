#!/usr/bin/env python3
"""Build the comparative structural census from recovered structural-island artifacts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

DEFAULT_SOURCES = (
    ("racer-update", "analysis/generated/racer-update-structure-island.json", True),
    ("object-collision", "analysis/generated/object-collision-structure-island.json", True),
    ("course-materialization", "analysis/generated/course-materialization-structure-island.json", False),
    ("racer-oam", "analysis/generated/racer-oam-structure-island.json", False),
    ("course-surface-sampler", "analysis/generated/course-surface-sampler-structure-island.json", False),
    ("race-frame-orchestrator", "analysis/generated/race-frame-orchestrator-structure-island.json", False),
    ("checkpoint-finish", "analysis/generated/checkpoint-finish-structure-island.json", False),
    ("stunt-finalizer", "analysis/generated/stunt-finalizer-structure-island.json", False),
    ("stunt-message-pipeline", "analysis/generated/stunt-message-pipeline-structure-island.json", False),
    ("input-normalization", "analysis/generated/input-normalization-structure-island.json", False),
    ("camera-control", "analysis/generated/camera-control-structure-island.json", False),
    ("race-timer", "analysis/generated/race-timer-structure-island.json", False),
    ("player-state-marshal", "analysis/generated/player-state-marshal-structure-island.json", False),
    ("collision-response", "analysis/generated/collision-response-structure-island.json", False),
)

def build(root: Path) -> dict:
    rows = []
    sources = []
    for source_id, rel, required in DEFAULT_SOURCES:
        path = root / rel
        if not path.exists():
            if required:
                raise FileNotFoundError(path)
            continue
        data = json.loads(path.read_text())
        sources.append({"id": source_id, "path": rel})
        for region in data["regions"]:
            builds = region.get("builds", {})
            usa = builds.get("usa-retail", {})
            rows.append({
                "source": source_id,
                "source_path": rel,
                "name": region["name"],
                "kind": region["kind"],
                "usa_start": region["usa_start"],
                "usa_end": region["usa_end"],
                "size": region["size"],
                "usa_opcode_bytes": usa.get("opcode_bytes", 0),
                "usa_operand_bytes": usa.get("operand_bytes", 0),
                "usa_unreached_or_data_bytes": usa.get("unreached_or_data_bytes", 0),
                "homologs": {
                    name: {
                        "start": item["start"],
                        "end": item["end"],
                        "shift": item["shift"],
                        "similarity": item["similarity"],
                        "size": item.get("size", region["size"]),
                        "size_delta": item.get("size_delta", 0),
                    }
                    for name, item in builds.items()
                },
            })
    rows.sort(key=lambda row: row["usa_start"])
    code = [row for row in rows if row["kind"] == "code"]
    data = [row for row in rows if row["kind"] == "data"]
    totals = {
        "regions": len(rows),
        "code_regions": len(code),
        "data_regions": len(data),
        "bounded_bytes": sum(row["size"] for row in rows),
        "bounded_code_region_bytes": sum(row["size"] for row in code),
        "bounded_data_region_bytes": sum(row["size"] for row in data),
        "analyzer_opcode_bytes": sum(row["usa_opcode_bytes"] for row in code),
        "analyzer_operand_bytes": sum(row["usa_operand_bytes"] for row in code),
        "analyzer_unreached_or_data_bytes": sum(row["usa_unreached_or_data_bytes"] for row in rows),
        "banks": sorted({row["usa_start"][:2] for row in rows}),
    }
    return {
        "schema_version": 1,
        "purpose": "Machine-queryable census of confidently bounded program structure recovered by the comparative four-ROM lane.",
        "scope_note": "This census is a conservative floor, not a whole-ROM coverage claim. It contains only regions whose boundaries/code-data role have already been independently recovered in accepted structural-island analyses.",
        "sources": sources,
        "totals": totals,
        "regions": rows,
    }

def render(census: dict) -> str:
    t = census["totals"]
    lines = [
        "# Comparative structural census", "",
        "This is the first machine-queryable census for the comparative structure-recovery phase. It aggregates only already-supported boundaries, so the counts below are a **floor**, not a whole-ROM coverage percentage.", "",
        f"- bounded regions: **{t['regions']}** ({t['code_regions']} code, {t['data_regions']} data)",
        f"- bounded bytes: **{t['bounded_bytes']}** ({t['bounded_code_region_bytes']} code-region bytes, {t['bounded_data_region_bytes']} data bytes)",
        f"- analyzer-classified USA opcode bytes inside code regions: **{t['analyzer_opcode_bytes']}**",
        f"- represented USA banks: **{', '.join(t['banks'])}**", "",
        "| USA range | Kind | Bytes | Source | Region | PAL prototype | Europe retail | Legacy beta |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    def cell(row: dict, build: str) -> str:
        h = row["homologs"].get(build)
        if not h:
            return "—"
        return f"{h['start']}..{h['end']} ({h['shift']:+d}; size {h['size']}; sim {h['similarity']:.3f})"
    for row in census["regions"]:
        lines.append(
            f"| `{row['usa_start']}..{row['usa_end']}` | {row['kind']} | {row['size']} | "
            f"{row['source']} | {row['name']} | {cell(row, 'pal-prototype-1994-11-29')} | "
            f"{cell(row, 'europe-retail')} | {cell(row, 'legacy-beta')} |"
        )
    lines += [
        "", "## Selection rule for the next island", "",
        "Grow this census by choosing a different executed/high-connectivity subsystem where comparative evidence can recover multiple boundaries or relationships at once. Prefer a candidate with direct call/table structure and shipping relevance. Do not extend an existing island merely to increase byte totals.",
        "", "The JSON form is the authoritative query surface: `analysis/generated/comparative-structural-census.json`.", ""
    ]
    return "\n".join(lines)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    census = build(args.root)
    outj = args.root / "analysis/generated/comparative-structural-census.json"
    outm = args.root / "analysis/generated/comparative-structural-census.md"
    outj.write_text(json.dumps(census, indent=2) + "\n")
    outm.write_text(render(census))
    print(render(census))

if __name__ == "__main__":
    main()
