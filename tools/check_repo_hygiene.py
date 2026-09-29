#!/usr/bin/env python3
"""Cheap repository-boundary checks for common agent-generated entropy."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROM_EXTENSIONS = {".sfc", ".smc", ".fig", ".swc", ".rom"}
SAVE_TRACE_EXTENSIONS = {".srm", ".state", ".sav"}
ROM_PREFIX = "reference/roms/"
FORBIDDEN_PREFIXES = (
    "private/",
    "generated/",
    "src/gen/",
    "assets/extracted/",
    "assets/generated/",
    "dump/",
    "dumps/",
    "captures/",
    "trace-output/",
    ".tools/",
    "workbench/",
)
ROOT_BINARY_EXTENSIONS = {".zip", ".rar", ".7z", ".pdf"}
ROOT_TEXT_EXCEPTIONS = {"rom_identity.txt"}
REQUIRED_ENTRYPOINTS = {
    "AGENTS.md",
    "docs/README.md",
    "docs/PERIODIC-REPOSITORY-HYGIENE.md",
    "docs/TOOLCHAIN.md",
    "tools/toolchain.json",
    "tools/bootstrap_toolchain.py",
    "tools/audit_imported_references.py",
    "references/imported/MANIFEST.json",
    "docs/THIRD-PARTY-CODE-AUDIT.md",
    "docs/TOOL-INTEROPERABILITY.md",
    "tools/tool_interop.json",
    "tools/validate_tool_interop.py",
    "tools/export_symbol_adapters.py",
}


def tracked_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], text=True, encoding="utf-8")
    return [line.replace("\\", "/") for line in out.splitlines() if line]


def main() -> int:
    bad: list[tuple[str, str]] = []
    tracked = tracked_files()

    for path in tracked:
        p = Path(path)
        suffix = p.suffix.lower()

        if suffix in ROM_EXTENSIONS and not path.startswith(ROM_PREFIX):
            bad.append((path, "ROM/cartridge image outside intentional reference/roms boundary"))

        if suffix in SAVE_TRACE_EXTENSIONS:
            bad.append((path, "save/state artifact should not be tracked"))

        if path.startswith(FORBIDDEN_PREFIXES):
            bad.append((path, "generated/scratch/workbench path should not be tracked"))

        if "/" not in path and suffix in ROOT_BINARY_EXTENSIONS:
            bad.append((path, "downloaded binary/reference artifact should not live at repository root"))

        if "/" not in path and suffix == ".txt" and path not in ROOT_TEXT_EXCEPTIONS:
            bad.append((path, "unclassified root text file; move into an owning doc/reference path or delete"))

    missing = [path for path in sorted(REQUIRED_ENTRYPOINTS) if not Path(path).exists()]

    if bad or missing:
        if bad:
            print("Repository hygiene violations:")
            for path, reason in bad:
                print(f"  {path}: {reason}")
        if missing:
            print("Missing repository entry points:")
            for path in missing:
                print(f"  {path}")
        return 1

    subprocess.run([sys.executable, str(Path(__file__).with_name("export_symbols.py")), "--check"], check=True)
    subprocess.run([sys.executable, str(Path(__file__).with_name("bootstrap_toolchain.py")), "--validate"], check=True)
    subprocess.run([sys.executable, str(Path(__file__).with_name("audit_imported_references.py"))], check=True)
    subprocess.run([sys.executable, str(Path(__file__).with_name("audit_imported_code.py")), "--check"], check=True)
    subprocess.run([sys.executable, str(Path(__file__).with_name("validate_tool_interop.py"))], check=True)
    subprocess.run([sys.executable, str(Path(__file__).with_name("export_symbol_adapters.py")), "--check"], check=True)

    roms = [p for p in tracked if Path(p).suffix.lower() in ROM_EXTENSIONS]
    print(f"Tracked-file hygiene check passed ({len(roms)} intentional ROM image(s) under {ROM_PREFIX}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
