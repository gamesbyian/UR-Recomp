#!/usr/bin/env python3
"""Compare decoded frontend screen text between snesref and the native recomp.

Decision served: native UI evidence was harvested without decoding text, so a
screen can look structurally right while missing content. This tool replays the
same route on both engines and compares the BG2 text decoded by the menu
visual-language decoder at each named checkpoint.

Cases (``CASES``):
- ``race-result``: ``tests/input/ui-race-result-route.script`` (1P Dragster finish).
- ``vs-challenger``: ``tests/input/vs-challenger-route.input`` with its observe script.

Native runs use the generated ``UniracersSNESRecomp`` target exactly as the
two-player CI workflow does (fresh ``saves`` directory, ``--script``,
``SNESRECOMP_INPUT_FILE``, ``xvfb-run``). snesref needs the dual-controller patch
for the VS case. ``compare`` is pure and unit-tested.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import extract_menu_visual_language as mvl
import probe_tier_opponents as tier

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "race-result": {"script": "tests/input/ui-race-result-route.script", "input": None,
                    "checkpoints": ["race-results"]},
    "vs-challenger": {"script": "tests/input/vs-challenger-route-observe.script",
                      "input": "tests/input/vs-challenger-route.input",
                      "checkpoints": ["vsc-result", "vsc-champions", "vsc-pick-challenger", "vsc-track-choice", "vsc-next"]},
}


def compare(ref: dict[str, list[str]], native: dict[str, list[str]]) -> dict:
    out = {}
    for cp, texts in ref.items():
        other = native.get(cp, [])
        out[cp] = {"match": texts == other,
                   "missing_on_native": [t for t in texts if t not in other],
                   "extra_on_native": [t for t in other if t not in texts]}
    return out


def texts(work: Path, checkpoints: list[str]) -> dict[str, list[str]]:
    return {cp: tier.screen_texts(mvl.Dump(work, cp)) for cp in checkpoints}


def run_snesref(args, case: dict, work: Path) -> None:
    env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1", SNESREF_WRAM_FILL="0",
               SNESREF_SCRIPT=str(ROOT / case["script"]), SNESREF_DUMP_DIR=str(work))
    if case["input"]:
        env["SNESREF_INPUT_FILE"] = str(ROOT / case["input"])
    with open(work / "engine.log", "w") as log:
        subprocess.run([str(args.snesref), str(args.core), str(args.rom)], env=env, cwd=work,
                       stdout=log, stderr=subprocess.STDOUT, check=True)


def run_native(args, case: dict, work: Path) -> None:
    shutil.rmtree(args.native.parent / "saves", ignore_errors=True)  # same battery baseline per launch
    env = dict(os.environ, SNESRECOMP_DUMP_DIR=str(work), SDL_AUDIODRIVER="dummy")
    if case["input"]:
        env["SNESRECOMP_INPUT_FILE"] = str(ROOT / case["input"])
    with open(work / "engine.log", "w") as log:
        subprocess.run(["xvfb-run", "-a", str(args.native), str(args.rom), "--script", str(ROOT / case["script"])],
                       env=env, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snesref", type=Path, required=True, help="snesref with the dual-controller patch")
    ap.add_argument("--native", type=Path, required=True, help="generated UniracersSNESRecomp executable")
    ap.add_argument("--core", type=Path, default=ROOT / ".tools/src/snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--case", choices=sorted(CASES), action="append")
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/native-screen-text-parity.json")
    args = ap.parse_args()
    report = {"schema_version": 1,
              "purpose": "Decoded BG2 frontend text parity, snesref vs generated native target, per checkpoint.",
              "cases": {}}
    with tempfile.TemporaryDirectory() as td:
        for name in args.case or sorted(CASES):
            case = CASES[name]
            ref_dir, nat_dir = Path(td) / f"{name}-snesref", Path(td) / f"{name}-native"
            ref_dir.mkdir()
            nat_dir.mkdir()
            run_snesref(args, case, ref_dir)
            run_native(args, case, nat_dir)
            ref, nat = texts(ref_dir, case["checkpoints"]), texts(nat_dir, case["checkpoints"])
            report["cases"][name] = {"script": case["script"], "input": case["input"],
                                     "snesref": ref, "native": nat, "comparison": compare(ref, nat)}
    mismatches = [f"{c}/{cp}" for c, v in report["cases"].items() for cp, r in v["comparison"].items() if not r["match"]]
    report["mismatches"] = mismatches
    report["all_match"] = not mismatches
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({"mismatches": mismatches,
                      "details": {m: report["cases"][m.split("/")[0]]["comparison"][m.split("/")[1]] for m in mismatches}}, indent=1))
    return 0 if report["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
