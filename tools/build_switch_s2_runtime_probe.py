#!/usr/bin/env python3
"""Cross-compile the pinned SNESRecomp authoritative runtime floor for Switch."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "analysis/switch-s2-runtime-core-contract.json"


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    return json.loads(path.read_text())


def validate_framework(framework: Path, contract: dict) -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    if contract.get("gate") != "S2-runtime-core-portability":
        errors.append("gate must be S2-runtime-core-portability")

    sources: list[Path] = []
    seen: set[str] = set()
    for rel in contract.get("runtime_sources", []):
        if rel in seen:
            errors.append(f"duplicate runtime source: {rel}")
            continue
        seen.add(rel)
        if rel.startswith("runner/src/desktop/") or "/desktop/" in rel:
            errors.append(f"desktop source leaked into runtime floor: {rel}")
            continue
        path = framework / rel
        if not path.is_file():
            errors.append(f"missing runtime source: {rel}")
            continue
        sources.append(path)

    for rel in contract.get("include_dirs", []):
        if not (framework / rel).is_dir():
            errors.append(f"missing runtime include dir: {rel}")

    return sources, errors


def compile_one(
    source: Path,
    output: Path,
    includes: list[Path],
    definitions: list[str],
    c_standard: str,
) -> tuple[str, int]:
    command = [
        "aarch64-none-elf-gcc",
        f"-std={c_standard}",
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
    command += [f"-D{definition}" for definition in definitions]
    for include in includes:
        command += ["-I", str(include)]
    command += ["-c", str(source), "-o", str(output)]
    subprocess.run(command, check=True)
    return source.as_posix(), output.stat().st_size


def compile_framework(framework: Path, out_dir: Path, jobs: int, contract: dict) -> dict:
    sources, errors = validate_framework(framework, contract)
    if errors:
        raise ValueError("; ".join(errors))

    includes = [framework / rel for rel in contract["include_dirs"]]
    definitions = list(contract["compile_definitions"])
    out_dir.mkdir(parents=True, exist_ok=True)

    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        for index, source in enumerate(sources):
            rel = source.relative_to(framework).as_posix()
            output = out_dir / f"{index:03d}__{rel.replace('/', '__')}.o"
            futures.append(
                pool.submit(
                    compile_one,
                    source,
                    output,
                    includes,
                    definitions,
                    contract["toolchain"]["c_standard"],
                )
            )
        results = [future.result() for future in futures]

    return {
        "schema_version": 1,
        "gate": contract["gate"],
        "source_count": len(results),
        "object_count": len(results),
        "object_bytes": sum(size for _, size in results),
        "sources": [source for source, _ in results],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    contract = load_contract()
    sources, errors = validate_framework(args.framework, contract)
    if errors:
        for error in errors:
            print(f"SWITCH_S2_RUNTIME_ERROR: {error}")
        return 1
    print(f"SWITCH_S2_RUNTIME_CONTRACT_OK sources={len(sources)}")

    if args.check_only:
        return 0

    result = compile_framework(args.framework, args.out_dir, args.jobs, contract)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
