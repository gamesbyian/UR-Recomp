#!/usr/bin/env python3
"""Assemble and verify the portable Windows x64 UR-Recomp package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

SCHEMA_VERSION = 1
PACKAGE_FORMAT = "ur-recomp-windows-x64-portable-v1"
EXE_NAME = "UniracersSNESRecomp.exe"
ROM_NAME = "Uniracers_USA.sfc"
MANIFEST_NAME = "PACKAGE-MANIFEST.json"
LAUNCHER_NAME = "run-uniracers.cmd"
README_NAME = "README.txt"
ARCHIVE_ROOT = "UR-Recomp-Windows-x64"
ARCHIVE_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


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
        f"if not exist \"{EXE_NAME}\" (echo UR-Recomp cannot start: required file missing: {EXE_NAME} 1>&2 & exit /b 2)\r\n"
        f"if not exist \"{ROM_NAME}\" (echo UR-Recomp cannot start: required file missing: {ROM_NAME} 1>&2 & exit /b 2)\r\n"
        "if not exist \"rom.cfg\" (echo UR-Recomp cannot start: required file missing: rom.cfg 1>&2 & exit /b 2)\r\n"
        f"\"{EXE_NAME}\" \"{ROM_NAME}\" %*\r\n"
        "exit /b %ERRORLEVEL%\r\n",
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


def create_archive(package: Path, archive: Path) -> dict[str, object]:
    package = package.resolve()
    archive = archive.resolve()
    manifest = verify(package)
    if archive.exists():
        archive.unlink()
    archive.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as output:
        for path in sorted(p for p in package.rglob("*") if p.is_file()):
            relative = path.relative_to(package).as_posix()
            info = zipfile.ZipInfo(
                f"{ARCHIVE_ROOT}/{relative}", date_time=ARCHIVE_TIMESTAMP
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, path.read_bytes(), compresslevel=9)
    return manifest


def verify_archive(archive: Path) -> dict[str, object]:
    archive = archive.resolve()
    if not archive.is_file():
        raise ValueError(f"package archive missing: {archive}")

    manifest_name = f"{ARCHIVE_ROOT}/{MANIFEST_NAME}"
    try:
        with zipfile.ZipFile(archive, "r") as source:
            names = source.namelist()
            if len(names) != len(set(names)):
                raise ValueError("package archive contains duplicate paths")
            if any(
                name.startswith("/") or "\\" in name or ".." in Path(name).parts
                for name in names
            ):
                raise ValueError("package archive contains unsafe paths")
            if manifest_name not in names:
                raise ValueError("package archive manifest missing")
            try:
                manifest = json.loads(
                    source.read(manifest_name).decode("utf-8")
                )
            except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"cannot read package archive manifest: {exc}"
                ) from exc

            if (
                manifest.get("schema_version") != SCHEMA_VERSION
                or manifest.get("package_format") != PACKAGE_FORMAT
                or not isinstance(manifest.get("files"), list)
            ):
                raise ValueError("unsupported or malformed package archive manifest")

            expected_names = {manifest_name}
            for entry in manifest["files"]:
                if not isinstance(entry, dict):
                    raise ValueError("malformed package archive file entry")
                relative = entry.get("path")
                expected_size = entry.get("size")
                expected_hash = entry.get("sha256")
                if (
                    not isinstance(relative, str)
                    or not isinstance(expected_size, int)
                    or not isinstance(expected_hash, str)
                ):
                    raise ValueError("malformed package archive file entry")
                name = f"{ARCHIVE_ROOT}/{relative}"
                expected_names.add(name)
                try:
                    payload = source.read(name)
                except KeyError as exc:
                    raise ValueError(
                        f"package archive payload missing: {relative}"
                    ) from exc
                if len(payload) != expected_size:
                    raise ValueError(
                        f"package archive size mismatch: {relative}"
                    )
                if hashlib.sha256(payload).hexdigest() != expected_hash:
                    raise ValueError(
                        f"package archive checksum mismatch: {relative}"
                    )

            if set(names) != expected_names:
                raise ValueError(
                    "package archive contains unmanifested or missing files"
                )
    except zipfile.BadZipFile as exc:
        raise ValueError(f"invalid package archive: {exc}") from exc

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

    archive_parser = subparsers.add_parser("archive")
    archive_parser.add_argument("--package", type=Path, required=True)
    archive_parser.add_argument("--output", type=Path, required=True)

    verify_archive_parser = subparsers.add_parser("verify-archive")
    verify_archive_parser.add_argument("--archive", type=Path, required=True)

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
        elif args.command == "verify":
            manifest = verify(args.package)
            print(
                f"WINDOWS_PACKAGE_VERIFIED files={len(manifest['files'])} "
                f"package={args.package}"
            )
        elif args.command == "archive":
            manifest = create_archive(args.package, args.output)
            print(
                f"WINDOWS_PACKAGE_ARCHIVED files={len(manifest['files'])} "
                f"archive={args.output}"
            )
        else:
            manifest = verify_archive(args.archive)
            print(
                f"WINDOWS_PACKAGE_ARCHIVE_VERIFIED files={len(manifest['files'])} "
                f"archive={args.archive}"
            )
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
