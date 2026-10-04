#!/usr/bin/env python3
"""Cross-compile generated Uniracers guest/title C for Switch AArch64."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "analysis/switch-s2-guest-aot-contract.json"


def load_contract(path: Path = CONTRACT) -> dict:
    return json.loads(path.read_text())


def validate_bundle(bundle: Path, contract: dict) -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    project = bundle / "project"
    framework = bundle / "framework"

    required = [
        project / "src/game_rtl.c",
        project / "src/host_contract.c",
        project / "src/gen_stubs.c",
        project / "src/game_rtl.h",
        project / "src/variables.h",
        project / "recomp/funcs.h",
        framework / "runner/src/common_cpu_infra.h",
        framework / "runner/src/common_rtl.h",
        framework / "runner/src/snes/snes.h",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing generated-bundle input: {path.relative_to(bundle)}")

    generated = sorted((project / "src/gen").glob("*.c"))
    if not generated:
        errors.append("generated bundle contains no src/gen/*.c files")

    sources = [
        project / "src/game_rtl.c",
        project / "src/host_contract.c",
        project / "src/gen_stubs.c",
        *generated,
    ]
    forbidden = {
        project / "src/main.c",
    }
    for source in sources:
        if source in forbidden or "/desktop/" in source.as_posix():
            errors.append(f"desktop source leaked into S2 guest probe: {source}")

    if contract.get("gate") != "S2-guest-aot-portability":
        errors.append("contract gate must be S2-guest-aot-portability")
    if contract.get("framework_revision") != "cd5875cbdaf19f5e324272b1f8051d671fce9215":
        errors.append("contract framework revision drifted from repository pin")
    return sources, errors


def compile_one(source: Path, out: Path, includes: list[Path], c_standard: str) -> tuple[str, int]:
    rel = source.as_posix()
    command = [
        "aarch64-none-elf-gcc",
        f"-std={c_standard}",
        "-D__SWITCH__",
        "-march=armv8-a+crc+crypto",
        "-mtune=cortex-a57",
        "-mtp=soft",
        "-fPIE",
        "-O2",
        "-Wall",
        "-Wextra",
        "-ffunction-sections",
        "-fdata-sections",
    ]
    for include in includes:
        command += ["-I", str(include)]
    command += ["-c", str(source), "-o", str(out)]
    subprocess.run(command, check=True)
    return rel, out.stat().st_size


def compile_bundle(bundle: Path, out_dir: Path, jobs: int, contract: dict) -> dict:
    sources, errors = validate_bundle(bundle, contract)
    if errors:
        raise ValueError("; ".join(errors))

    project = bundle / "project"
    framework = bundle / "framework"
    includes = [
        framework / "runner/src",
        framework / "runner/src/snes",
        project / "src",
        project / "recomp",
    ]
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        for index, source in enumerate(sources):
            name = source.relative_to(bundle).as_posix().replace("/", "__")
            output = out_dir / f"{index:04d}__{name}.o"
            tasks.append(
                pool.submit(
                    compile_one,
                    source,
                    output,
                    includes,
                    contract["toolchain"]["c_standard"],
                )
            )
        compiled = [future.result() for future in tasks]

    return {
        "schema_version": 1,
        "gate": contract["gate"],
        "source_count": len(sources),
        "generated_count": len(sources) - 3,
        "object_count": len(compiled),
        "object_bytes": sum(size for _, size in compiled),
        "sources": [source for source, _ in compiled],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    contract = load_contract()
    sources, errors = validate_bundle(args.bundle, contract)
    if errors:
        for error in errors:
            print(f"SWITCH_S2_GUEST_ERROR: {error}")
        return 1
    print(f"SWITCH_S2_GUEST_BUNDLE_OK sources={len(sources)}")
    if args.check_only:
        return 0

    result = compile_bundle(args.bundle, args.out_dir, args.jobs, contract)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
