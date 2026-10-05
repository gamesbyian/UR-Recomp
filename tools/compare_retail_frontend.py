#!/usr/bin/env python3
"""Capture and compare USA-retail vs Europe-retail frontend checkpoints in snesref."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from compare_framebuffers import compare_frames
import extract_menu_visual_language as mvl
import probe_tier_opponents as tier

CASES = {
    "title-transition": {
        "script": "tests/input/title-transition-recon.script",
        "checkpoints": [
            "boot-300",
            "boot-360",
            "boot-420",
            "main-menu-first",
            "main-menu-settled",
        ],
    },
    "startup-main": {
        "script": "tests/input/ui-startup-timeline.script",
        "checkpoints": ["ui-startup-main-menu"],
    },
    "options": {
        "script": "tests/input/ui-options-route.script",
        "checkpoints": [
            "ui-main-menu-1p",
            "ui-main-menu-2p",
            "ui-main-menu-vs",
            "ui-main-menu-league",
            "ui-main-menu-options",
            "ui-options-entry",
            "ui-options-back-main",
        ],
    },
    "main-branches": {
        "script": "tests/input/ui-main-branches.script",
        "checkpoints": [
            "ui-two-player-entry",
            "ui-two-player-back-main",
            "ui-vs-entry",
            "ui-vs-back-main",
            "ui-league-entry",
            "ui-league-back-main",
        ],
    },
    "records": {
        "script": "tests/input/ui-records-explore.script",
        "checkpoints": [
            "ui-records-probe-down-before",
            "ui-records-probe-down-after",
            "ui-records-probe-up-before",
            "ui-records-probe-up-after",
            "ui-records-probe-left-before",
            "ui-records-probe-left-after",
            "ui-records-probe-right-before",
            "ui-records-probe-right-after",
            "ui-records-probe-a-before",
            "ui-records-probe-a-after",
            "ui-records-probe-b-before",
            "ui-records-probe-b-after",
        ],
    },
    "league-naming": {
        "script": "tests/input/ui-name-league-route.script",
        "checkpoints": [
            line.split()[1]
            for line in (ROOT / "tests/input/ui-name-league-route.script").read_text().splitlines()
            if line.startswith("dump ")
        ],
    },
}


def run_reference(
    snesref: Path,
    core: Path,
    rom: Path,
    script: Path,
    out_dir: Path,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / "engine.log"
    env = dict(
        os.environ,
        SNESREF_HEADLESS="1",
        SNESREF_FAST="1",
        SNESREF_WRAM_FILL="0",
        SNESREF_SCRIPT=str(script),
        SNESREF_DUMP_DIR=str(out_dir),
    )
    with log.open("w", encoding="utf-8") as fh:
        proc = subprocess.run(
            [str(snesref), str(core), str(rom)],
            cwd=out_dir,
            env=env,
            stdout=fh,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=300,
        )
    return {
        "returncode": proc.returncode,
        "log": str(log),
    }


def screen_texts(dump_dir: Path, checkpoint: str) -> list[str]:
    try:
        return tier.screen_texts(mvl.Dump(dump_dir, checkpoint))
    except Exception:
        return []


def compare_checkpoint(usa_dir: Path, eur_dir: Path, checkpoint: str) -> dict:
    out = {
        "checkpoint": checkpoint,
        "usa_present": False,
        "europe_present": False,
        "framebuffer": None,
        "text": None,
    }
    usa_fb = usa_dir / f"{checkpoint}.fb.bgrx"
    eur_fb = eur_dir / f"{checkpoint}.fb.bgrx"
    out["usa_present"] = usa_fb.is_file()
    out["europe_present"] = eur_fb.is_file()

    if usa_fb.is_file() and eur_fb.is_file():
        out["framebuffer"] = compare_frames(
            usa_fb.read_bytes(),
            eur_fb.read_bytes(),
            width=256,
            bytes_per_pixel=4,
        )

    usa_text = screen_texts(usa_dir, checkpoint)
    eur_text = screen_texts(eur_dir, checkpoint)
    if usa_text or eur_text:
        out["text"] = {
            "usa": usa_text,
            "europe": eur_text,
            "match": usa_text == eur_text,
            "usa_only": [x for x in usa_text if x not in eur_text],
            "europe_only": [x for x in eur_text if x not in usa_text],
        }
    return out


def compare_existing_dirs(
    usa_dir: Path,
    eur_dir: Path,
    checkpoints: list[str],
) -> dict:
    rows = [compare_checkpoint(usa_dir, eur_dir, cp) for cp in checkpoints]
    return {
        "checkpoints": rows,
        "both_present": sum(
            1 for row in rows if row["usa_present"] and row["europe_present"]
        ),
        "expected": len(rows),
        "frame_differences": sum(
            1
            for row in rows
            if row["framebuffer"] and row["framebuffer"]["changed_pixels"] > 0
        ),
        "text_differences": sum(
            1 for row in rows if row["text"] and not row["text"]["match"]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snesref", type=Path, required=True)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument(
        "--usa-rom",
        type=Path,
        default=ROOT / "reference/roms/retail/Uniracers_USA.sfc",
    )
    parser.add_argument(
        "--europe-rom",
        type=Path,
        default=ROOT / "reference/roms/retail/Unirally_Europe.sfc",
    )
    parser.add_argument("--case", choices=sorted(CASES), action="append")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--retain-dir", type=Path)
    args = parser.parse_args()

    report = {
        "schema_version": 1,
        "purpose": (
            "Matched snesref frontend framebuffer/text evidence for USA retail "
            "versus Europe retail. Route failures are retained as evidence and "
            "do not imply an implementation requirement by themselves."
        ),
        "cases": {},
    }

    root_ctx = (
        tempfile.TemporaryDirectory()
        if args.retain_dir is None
        else None
    )
    work_root = Path(root_ctx.name) if root_ctx else args.retain_dir
    work_root.mkdir(parents=True, exist_ok=True)

    try:
        for name in args.case or sorted(CASES):
            case = CASES[name]
            usa_dir = work_root / name / "usa"
            eur_dir = work_root / name / "europe"
            script = ROOT / case["script"]
            usa_run = run_reference(
                args.snesref, args.core, args.usa_rom, script, usa_dir
            )
            eur_run = run_reference(
                args.snesref, args.core, args.europe_rom, script, eur_dir
            )
            comparison = compare_existing_dirs(
                usa_dir, eur_dir, case["checkpoints"]
            )
            report["cases"][name] = {
                "script": case["script"],
                "usa_run": usa_run,
                "europe_run": eur_run,
                "comparison": comparison,
            }
    finally:
        if root_ctx:
            root_ctx.cleanup()

    report["summary"] = {
        "case_count": len(report["cases"]),
        "route_failures": [
            f"{name}:{region}"
            for name, case in report["cases"].items()
            for region, key in (("usa", "usa_run"), ("europe", "europe_run"))
            if case[key]["returncode"] != 0
        ],
        "matched_checkpoint_count": sum(
            case["comparison"]["both_present"]
            for case in report["cases"].values()
        ),
        "frame_difference_count": sum(
            case["comparison"]["frame_differences"]
            for case in report["cases"].values()
        ),
        "text_difference_count": sum(
            case["comparison"]["text_differences"]
            for case in report["cases"].values()
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
