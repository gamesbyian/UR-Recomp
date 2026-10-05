#!/usr/bin/env python3
"""Promote the accepted Widescreen preparation provider into a generated product.

A freshly scaffolded project owns its seed CFG but has not emitted AOT yet.
Widescreen adds the accepted race-frame root before the single generation pass,
then applies the validated presentation hook to that output. Keep those two
operations together so every shipping native workflow gets the same fail-closed
contract without paying for a throwaway first generation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from apply_native_widescreen_hook import apply as apply_widescreen_hook
from patch_challenge_generation_writer import patch_sources as patch_challenge_generation_writer
from seed_native_widescreen_aot import ensure_seed


def generation_command(framework: Path, project: Path, rom: Path) -> list[str]:
    return [
        sys.executable,
        str(framework / "snesrecomp_cli.py"),
        "generate",
        "--rom",
        str(rom),
        "--project-root",
        str(project),
        "--cfg-dir",
        "recomp",
        "--out-dir",
        "src/gen",
        "--funcs-h",
        "recomp/funcs.h",
        "--cfg-roots",
    ]


def prepare(
    framework: Path,
    project: Path,
    rom: Path,
    *,
    run=subprocess.run,
    regression_baseline: bool = False,
) -> dict:
    framework = framework.resolve()
    project = project.resolve()
    rom = rom.resolve()

    cli = framework / "snesrecomp_cli.py"
    cfg = project / "recomp"
    generated = project / "src" / "gen"
    if not cli.is_file():
        raise ValueError(f"SNESRecomp CLI missing: {cli}")
    if not cfg.is_dir():
        raise ValueError(f"generated project cfg missing: {cfg}")
    if not rom.is_file():
        raise ValueError(f"ROM missing: {rom}")

    seeded = ensure_seed(cfg)
    run(generation_command(framework, project, rom), check=True)
    if not generated.is_dir():
        raise ValueError(f"regenerated AOT directory missing: {generated}")
    if regression_baseline:
        # The 4:3 regression gate's reference: the identical generated program
        # with no Widescreen presentation hook. Never a shipping product.
        return {
            "schema_version": 1,
            "seeded": seeded,
            "regression_baseline": True,
            "product_ready": False,
        }
    hook = apply_widescreen_hook(generated)
    challenge_generation_source = patch_challenge_generation_writer(generated)

    if not hook.get("margin72_supported"):
        raise ValueError("accepted Widescreen provider did not retain +72 capacity")
    return {
        "schema_version": 1,
        "seeded": seeded,
        "hook": hook,
        "challenge_generation_writer": str(
            challenge_generation_source.relative_to(project)),
        "product_ready": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--framework", type=Path, required=True)
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument(
        "--regression-baseline",
        action="store_true",
        help="seed and generate only, without the presentation hook (4:3 regression gate reference)",
    )
    args = ap.parse_args()

    report = prepare(args.framework, args.project, args.rom,
                     regression_baseline=args.regression_baseline)
    payload = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
