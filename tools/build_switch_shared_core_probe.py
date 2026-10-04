#!/usr/bin/env python3
"""Validate and cross-compile the Switch-shared modern product core."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "analysis/switch-shared-core-contract.json"


def load_contract(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_contract(root: Path, contract: dict) -> list[str]:
    errors: list[str] = []
    units = contract.get("portable_translation_units", [])
    excluded = {entry.get("path") for entry in contract.get("excluded_adapters", [])}
    forbidden = contract.get("forbidden_portable_tokens", [])

    if contract.get("gate") != "S0-shared-core":
        errors.append("gate must be S0-shared-core")
    if not units:
        errors.append("portable_translation_units must not be empty")
    if len(units) != len(set(units)):
        errors.append("portable_translation_units contains duplicates")

    for rel in units:
        if rel in excluded:
            errors.append(f"portable/excluded overlap: {rel}")
            continue
        path = root / rel
        if not path.is_file():
            errors.append(f"missing portable translation unit: {rel}")
            continue
        text = path.read_text(errors="replace")
        for token in forbidden:
            if token in text:
                errors.append(f"desktop/platform leak in {rel}: {token}")

    for entry in contract.get("excluded_adapters", []):
        rel = entry.get("path", "")
        if not rel or not (root / rel).is_file():
            errors.append(f"missing excluded adapter: {rel}")

    for rel in contract.get("include_dirs", []):
        if not (root / rel).is_dir():
            errors.append(f"missing include directory: {rel}")

    return errors


def compile_units(root: Path, contract: dict, out_dir: Path) -> list[Path]:
    devkitpro = os.environ.get("DEVKITPRO")
    if not devkitpro:
        raise RuntimeError("DEVKITPRO is not set; load the devkitPro Switch environment first")

    cpp = "aarch64-none-elf-g++"
    cc = "aarch64-none-elf-gcc"
    include_args = []
    for rel in contract.get("include_dirs", []):
        include_args += ["-I", str(root / rel)]

    common = [
        "-D__SWITCH__",
        "-march=armv8-a+crc+crypto",
        "-mtune=cortex-a57",
        "-mtp=soft",
        "-fPIE",
        "-Wall",
        "-Wextra",
        "-Wpedantic",
        "-ffunction-sections",
        "-fdata-sections",
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for rel in contract["portable_translation_units"]:
        source = root / rel
        stem = rel.replace("/", "__").rsplit(".", 1)[0]
        output = out_dir / f"{stem}.o"
        if source.suffix == ".c":
            command = [cc, "-std=gnu11", *common, *include_args, "-c", str(source), "-o", str(output)]
        else:
            command = [cpp, f"-std={contract['toolchain']['cpp_standard']}", *common, *include_args, "-c", str(source), "-o", str(output)]
        print("SWITCH_SHARED_COMPILE", rel)
        subprocess.run(command, cwd=root, check=True)
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"compiler did not emit object: {output}")
        outputs.append(output)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=ROOT / ".build/switch-shared-core")
    args = parser.parse_args()

    contract = load_contract(args.contract)
    errors = validate_contract(ROOT, contract)
    if errors:
        for error in errors:
            print(f"SWITCH_SHARED_CORE_ERROR: {error}")
        return 1
    print(f"SWITCH_SHARED_CORE_CONTRACT_OK units={len(contract['portable_translation_units'])}")

    if args.check_only:
        return 0

    outputs = compile_units(ROOT, contract, args.out_dir)
    total = sum(path.stat().st_size for path in outputs)
    print(f"SWITCH_SHARED_CORE_COMPILE_OK objects={len(outputs)} bytes={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
