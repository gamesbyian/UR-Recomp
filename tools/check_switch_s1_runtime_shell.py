#!/usr/bin/env python3
"""Validate the Switch S1 runtime-shell contract without making hardware claims."""

from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    contract_path = root / "analysis/switch-s1-runtime-shell-contract.json"
    source_path = root / "platform/switch/s1_runtime_shell/source/main.c"
    makefile_path = root / "platform/switch/s1_runtime_shell/Makefile"
    workflow_path = root / ".github/workflows/switch-s1-runtime-shell.yml"
    for path in (contract_path, source_path, makefile_path, workflow_path):
        if not path.is_file():
            errors.append(f"missing S1 runtime-shell file: {path.relative_to(root)}")
    if errors:
        return errors

    contract = json.loads(contract_path.read_text())
    source = source_path.read_text()
    makefile = makefile_path.read_text()
    workflow = workflow_path.read_text()

    if contract.get("gate") != "S1-runtime-shell":
        errors.append("contract gate must be S1-runtime-shell")
    image = contract.get("toolchain", {}).get("container", "")
    if not re.fullmatch(r"devkitpro/devkita64:\d{8}", image):
        errors.append("S1 toolchain must use a dated devkitPro image")
    if image not in workflow:
        errors.append("workflow image must match S1 contract")

    required_source = (
        "SDL_CreateWindow",
        "SDL_CreateRenderer",
        "SDL_OpenAudioDevice",
        "padConfigureInput",
        "padInitializeDefault",
        "padGetStyleSet",
        "appletGetOperationMode",
        "appletMainLoop",
        "SDL_APP_WILLENTERBACKGROUND",
        "SDL_APP_DIDENTERFOREGROUND",
        "fopen(",
        "ur-recomp-s1-capability-report.txt",
    )
    for token in required_source:
        if token not in source:
            errors.append(f"S1 shell missing capability token: {token}")

    forbidden = ("Uniracers_USA.sfc", "common_rtl.h", "SNESRecomp", "native/product/")
    combined = source + "\n" + makefile + "\n" + workflow
    for token in forbidden:
        if token in combined:
            errors.append(f"S1 shell must remain guest/product independent: {token}")

    if "hardware-observation-only" not in source:
        errors.append("S1 report must label itself hardware-observation-only")
    if "pull_request:" not in workflow or "workflow_dispatch:" not in workflow:
        errors.append("S1 workflow must support PR validation and manual dispatch")
    if "timeout-minutes:" not in workflow or "concurrency:" not in workflow:
        errors.append("S1 workflow must be bounded and cancel superseded runs")
    if "test -s platform/switch/s1_runtime_shell/ur-recomp-switch-s1.nro" not in workflow:
        errors.append("S1 workflow must assert NRO output identity")
    if "$(DEVKITPRO)/libnx/switch_rules" not in makefile:
        errors.append("S1 Makefile must use libnx switch_rules")
    if "sdl2-config --libs" not in makefile:
        errors.append("S1 Makefile must link Switch SDL2")

    non_claims = contract.get("non_claims", [])
    if len(non_claims) < 5:
        errors.append("S1 contract must retain explicit CI non-claims")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = check(args.root.resolve())
    if errors:
        for error in errors:
            print(f"SWITCH_S1_ERROR: {error}")
        return 1
    print("SWITCH_S1_RUNTIME_SHELL_CONTRACT_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
