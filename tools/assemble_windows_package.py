#!/usr/bin/env python3
"""Assemble and verify the portable Windows x64 UR-Recomp package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

SCHEMA_VERSION = 1
PACKAGE_FORMAT = "ur-recomp-windows-x64-portable-v1"
EXE_NAME = "UniracersSNESRecomp.exe"
ROM_NAME = "Uniracers_USA.sfc"
MANIFEST_NAME = "PACKAGE-MANIFEST.json"
LAUNCHER_NAME = "run-uniracers.cmd"
README_NAME = "README.txt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_files(root: Path) -> list[dict[str, object]]:
    files: list[dict[str, object]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative == MANIFEST_NAME:
            continue
        files.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return files


def write_launcher(path: Path) -> None:
    path.write_text(
        "@echo off\r\n"
        "setlocal\r\n"
        "cd /d \"%~dp0\"\r\n"
        f"\"{EXE_NAME}\" \"{ROM_NAME}\" %*\r\n",
        encoding="utf-8",
        newline="",
    )


def write_readme(path: Path) -> None:
    path.write_text(
        "UR-Recomp - Windows x64 portable package\n"
        "\n"
        "This is the portable Windows build. Extract the whole folder to a "
        "normal user-writable location before running it. Do not run directly "
        "from inside the ZIP, and do not install this version under Program "
        "Files.\n"
        "\n"
        f"Start the game with {LAUNCHER_NAME}. Keep {EXE_NAME}, {ROM_NAME}, "
        "rom.cfg and the mods directory together.\n"
        "\n"
        "The current desktop host creates framework config/keybind/save files "
        "relative to this package directory. Modern profile metadata and run "
        "history may additionally use the platform per-user preference "
        "directory. A future installer may move all mutable state to a "
        "per-user data root; this portable package deliberately does not "
        "pretend that migration is complete.\n"
        "\n"
        "Private personal-use preservation/remaster build.\n",
        encoding="utf-8",
    )


def assemble(
    build_dir: Path,
    rom: Path,
    output: Path,
    source_revision: str,
) -> dict[str, object]:
    build_dir = build_dir.resolve()
    rom = rom.resolve()
    output = output.resolve()

    required_files = [build_dir / EXE_NAME, build_dir / "rom.cfg", rom]
    for path in required_files:
        if not path.is_file():
            raise ValueError(f"required package input missing: {path}")
    mods = build_dir / "mods"
    if not mods.is_dir():
        raise ValueError(f"required package input missing: {mods}")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    shutil.copy2(build_dir / EXE_NAME, output / EXE_NAME)
    shutil.copy2(build_dir / "rom.cfg", output / "rom.cfg")
    shutil.copy2(rom, output / ROM_NAME)
    shutil.copytree(mods, output / "mods")
    write_launcher(output / LAUNCHER_NAME)
    write_readme(output / README_NAME)

    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "package_format": PACKAGE_FORMAT,
        "source_revision": source_revision,
        "files": package_files(output),
    }
    (output / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify(package: Path) -> dict[str, object]:
    package = package.resolve()
    manifest_path = package / MANIFEST_NAME
    if not manifest_path.is_file():
        raise ValueError(f"package manifest missing: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read package manifest: {exc}") from exc

    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("package_format") != PACKAGE_FORMAT
        or not isinstance(manifest.get("files"), list)
    ):
        raise ValueError("unsupported or malformed package manifest")

    expected = manifest["files"]
    actual = package_files(package)
    if actual != expected:
        raise ValueError("package contents do not match PACKAGE-MANIFEST.json")

    required = {
        EXE_NAME,
        ROM_NAME,
        "rom.cfg",
        LAUNCHER_NAME,
        README_NAME,
    }
    actual_paths = {entry["path"] for entry in actual}
    missing = sorted(required - actual_paths)
    if missing:
        raise ValueError("required packaged files missing: " + ", ".join(missing))
    if not any(path.startswith("mods/") for path in actual_paths):
        raise ValueError("packaged mods directory is empty")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    assemble_parser = subparsers.add_parser("assemble")
    assemble_parser.add_argument("--build-dir", type=Path, required=True)
    assemble_parser.add_argument("--rom", type=Path, required=True)
    assemble_parser.add_argument("--output", type=Path, required=True)
    assemble_parser.add_argument("--source-revision", default="")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--package", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.command == "assemble":
            manifest = assemble(
                args.build_dir, args.rom, args.output, args.source_revision
            )
            print(
                f"WINDOWS_PACKAGE_ASSEMBLED files={len(manifest['files'])} "
                f"output={args.output}"
            )
        else:
            manifest = verify(args.package)
            print(
                f"WINDOWS_PACKAGE_VERIFIED files={len(manifest['files'])} "
                f"package={args.package}"
            )
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
