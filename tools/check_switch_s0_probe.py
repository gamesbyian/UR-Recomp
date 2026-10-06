#!/usr/bin/env python3
"""Validate the repository-owned Switch Gate S0 compile-probe contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_contract(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    contract_path = root / "analysis/switch-s0-contract.json"
    makefile_path = root / "platform/switch/s0_probe/Makefile"
    source_path = root / "platform/switch/s0_probe/source/main.c"
    workflow_path = root / ".github/workflows/switch-s0-compile-probe.yml"

    for path in (contract_path, makefile_path, source_path, workflow_path):
        if not path.is_file():
            errors.append(f"missing required S0 file: {path.relative_to(root)}")
    if errors:
        return errors

    contract = json.loads(contract_path.read_text())
    makefile = makefile_path.read_text()
    source = source_path.read_text()
    workflow = workflow_path.read_text()

    if contract.get("gate") != "S0":
        errors.append("contract gate must be S0")
    image = contract.get("toolchain", {}).get("container", "")
    if not re.fullmatch(r"devkitpro/devkita64:\d{8}", image):
        errors.append("toolchain container must use a dated devkitpro/devkita64 tag")
    if ":latest" in workflow:
        errors.append("workflow must not use mutable devkitPro latest tag")
    if image and image not in workflow:
        errors.append("workflow container must match analysis/switch-s0-contract.json")

    required_make_tokens = (
        "$(DEVKITPRO)/libnx/switch_rules",
        "sdl2-config --cflags",
        "sdl2-config --libs",
        "$(PORTLIBS)",
        "$(LIBNX)",
        "$(OUTPUT).nro",
    )
    for token in required_make_tokens:
        if token not in makefile:
            errors.append(f"Makefile missing required token: {token}")

    required_source_tokens = (
        "#include <switch.h>",
        "#include <SDL2/SDL.h>",
        "appletGetOperationMode",
        "SDL_GetVersion",
    )
    for token in required_source_tokens:
        if token not in source:
            errors.append(f"probe source missing required token: {token}")

    forbidden = ("reference/roms", "Uniracers_USA.sfc", "SNESRecomp", "native/product/")
    combined = makefile + "\n" + source + "\n" + workflow
    for token in forbidden:
        if token in combined:
            errors.append(f"S0 probe must remain guest/product independent: {token}")

    if '. "$DEVKITPRO/switchvars.sh"' not in workflow:
        errors.append("S0 workflow must explicitly load the devkitPro Switch environment")
    if "workflow_dispatch:" not in workflow:
        errors.append("S0 workflow must remain manually runnable")
    if "pull_request:" in workflow:
        errors.append("S0 workflow must remain manual-only while Switch work is deferred")
    if "timeout-minutes:" not in workflow:
        errors.append("S0 workflow requires an explicit job timeout")
    if "concurrency:" not in workflow:
        errors.append("S0 manual validation must retain bounded concurrency")
    if "actions/upload-artifact@" not in workflow:
        errors.append("S0 workflow must retain build metadata")

    output = contract.get("link_contract", {}).get("required_output", "")
    if output and output not in workflow:
        errors.append("workflow must assert the contracted NRO output path")

    scope = contract.get("scope", {})
    for key in ("guest_code", "runtime_hardware_acceptance", "simulation_claim", "product_feature_claim"):
        if scope.get(key) is not False:
            errors.append(f"S0 scope flag {key} must remain false")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = check_contract(args.root.resolve())
    if errors:
        for error in errors:
            print(f"SWITCH_S0_ERROR: {error}")
        return 1
    print("SWITCH_S0_CONTRACT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
