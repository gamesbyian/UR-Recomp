#!/usr/bin/env python3
"""Compare Mesen CDL execution for two deterministic UR-Recomp fixtures.

This is intentionally a bounded discovery aid, not a new coverage metric.
It answers one question: which ROM bytes were executed/data-read in one
controlled fixture but not the other?
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools" / "run_fixture_mesen.py"
DEFAULT_MESEN_REPO = ROOT / ".tools" / "src" / "mesen-for-ai"
CLIENT = Path("skills/mesen-emulator/scripts/mesen_client.py")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def ranges(indices: list[int]) -> list[tuple[int, int]]:
    if not indices:
        return []
    out: list[tuple[int, int]] = []
    start = prev = indices[0]
    for value in indices[1:]:
        if value == prev + 1:
            prev = value
            continue
        out.append((start, prev))
        start = prev = value
    out.append((start, prev))
    return out


def classify_bytes(entries: list[dict]) -> tuple[set[int], set[int]]:
    code = {i for i, entry in enumerate(entries) if entry.get("code")}
    data = {i for i, entry in enumerate(entries) if entry.get("data")}
    return code, data


def compare_entries(baseline: list[dict], variant: list[dict]) -> dict:
    if len(baseline) != len(variant):
        raise ValueError(
            f"CDL map size mismatch: baseline={len(baseline)} variant={len(variant)}"
        )
    baseline_code, baseline_data = classify_bytes(baseline)
    variant_code, variant_data = classify_bytes(variant)
    variant_only_code = sorted(variant_code - baseline_code)
    baseline_only_code = sorted(baseline_code - variant_code)
    variant_only_data = sorted(variant_data - baseline_data)
    baseline_only_data = sorted(baseline_data - variant_data)
    return {
        "code": {
            "baseline": len(baseline_code),
            "variant": len(variant_code),
            "variant_only": len(variant_only_code),
            "baseline_only": len(baseline_only_code),
            "variant_only_ranges": [
                {"start": lo, "end": hi, "length": hi - lo + 1}
                for lo, hi in ranges(variant_only_code)
            ],
            "baseline_only_ranges": [
                {"start": lo, "end": hi, "length": hi - lo + 1}
                for lo, hi in ranges(baseline_only_code)
            ],
        },
        "data": {
            "baseline": len(baseline_data),
            "variant": len(variant_data),
            "variant_only": len(variant_only_data),
            "baseline_only": len(baseline_only_data),
            "variant_only_ranges": [
                {"start": lo, "end": hi, "length": hi - lo + 1}
                for lo, hi in ranges(variant_only_data)
            ],
            "baseline_only_ranges": [
                {"start": lo, "end": hi, "length": hi - lo + 1}
                for lo, hi in ranges(baseline_only_data)
            ],
        },
    }


def run_fixture(rom: Path, fixture: Path, mesen_repo: Path, export: Path):
    runner = load_module(RUNNER_PATH, "ur_fixture_runner")
    client = load_module(mesen_repo / CLIENT, "ur_mesen_client")
    commands = runner.parse_fixture(fixture)
    with client.Mesen(repo=str(mesen_repo)) as mesen:
        mesen.load_rom(str(rom.resolve()), timeout=300)
        mesen.tool("cdl.start")
        runner.FixtureRunner(
            mesen, Path(tempfile.mkdtemp(prefix="ur-cdl-dumps-"))
        ).execute(commands)
        mesen.tool("cdl.stop")
        return mesen.tool(
            "cdl.export", memoryType="snesPrgRom", path=str(export.resolve())
        )


def render_markdown(baseline: Path, variant: Path, result: dict) -> str:
    code = result["code"]
    data = result["data"]
    lines = [
        "# Fixture execution-coverage A/B",
        "",
        f"Baseline: `{baseline}`  ",
        f"Variant: `{variant}`",
        "",
        "This artifact is a discovery aid. It does not measure semantic completeness.",
        "",
        "## Summary",
        "",
        "| Metric | Baseline | Variant | Variant only | Baseline only |",
        "|---|---:|---:|---:|---:|",
        f"| Executed/code bytes | {code['baseline']} | {code['variant']} | {code['variant_only']} | {code['baseline_only']} |",
        f"| Data bytes | {data['baseline']} | {data['variant']} | {data['variant_only']} | {data['baseline_only']} |",
        "",
        "## Variant-only executed ranges",
        "",
        "| ROM offset start | End | Bytes |",
        "|---:|---:|---:|",
    ]
    for item in code["variant_only_ranges"]:
        lines.append(
            f"| `0x{item['start']:06X}` | `0x{item['end']:06X}` | {item['length']} |"
        )
    if not code["variant_only_ranges"]:
        lines.append("| _none_ | _none_ | 0 |")
    lines += [
        "",
        "## Baseline-only executed ranges",
        "",
        "| ROM offset start | End | Bytes |",
        "|---:|---:|---:|",
    ]
    for item in code["baseline_only_ranges"]:
        lines.append(
            f"| `0x{item['start']:06X}` | `0x{item['end']:06X}` | {item['length']} |"
        )
    if not code["baseline_only_ranges"]:
        lines.append("| _none_ | _none_ | 0 |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("variant", type=Path)
    ap.add_argument(
        "--mesen-for-ai-repo",
        type=Path,
        default=Path(os.environ.get("MESEN_FOR_AI_REPO", DEFAULT_MESEN_REPO)),
    )
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--md-out", type=Path, required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="ur-cdl-") as temp:
        temp_path = Path(temp)
        baseline_export = temp_path / "baseline.json"
        variant_export = temp_path / "variant.json"
        baseline_summary = run_fixture(
            args.rom, args.baseline, args.mesen_for_ai_repo, baseline_export
        )
        variant_summary = run_fixture(
            args.rom, args.variant, args.mesen_for_ai_repo, variant_export
        )
        baseline_entries = json.loads(baseline_export.read_text())["bytes"]
        variant_entries = json.loads(variant_export.read_text())["bytes"]

    result = compare_entries(baseline_entries, variant_entries)
    payload = {
        "schema_version": 1,
        "baseline": str(args.baseline),
        "variant": str(args.variant),
        "baseline_summary": baseline_summary,
        "variant_summary": variant_summary,
        **result,
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n")
    args.md_out.write_text(render_markdown(args.baseline, args.variant, result))
    print(args.md_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
