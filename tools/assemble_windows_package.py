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
        f"if not exist \"{EXE_NAME}\" (echo UR-STARTUP-RUNTIME-DATA: required package file is missing: {EXE_NAME}. Re-extract the complete package. 1>&2 & exit /b 2)\r\n"
        f"if not exist \"{ROM_NAME}\" (echo UR-STARTUP-ROM-MISSING: packaged ROM is missing: {ROM_NAME}. Restore the package or your verified personal dump. 1>&2 & exit /b 2)\r\n"
        "if not exist \"rom.cfg\" (echo UR-STARTUP-RUNTIME-DATA: required package file is missing: rom.cfg. Re-extract the complete package. 1>&2 & exit /b 2)\r\n"
        "if not exist \"mods\\\" (echo UR-STARTUP-RUNTIME-DATA: required package directory is missing: mods. Re-extract the complete package. 1>&2 & exit /b 2)\r\n"
        "for /f \"delims=\" %%I in ('dir /b /s /a-d \"mods\\*\" 2^>nul') do goto mods_payload_ready\r\n"
        "echo UR-STARTUP-RUNTIME-DATA: required package directory is empty: mods. Re-extract the complete package. 1>&2\r\n"
        "exit /b 2\r\n"
        ":mods_payload_ready\r\n"
        "if defined UR_RECOMP_USER_DATA_ROOT goto validate_user_root\r\n"
        "if not defined APPDATA (echo UR-STARTUP-SAVE-ROOT: APPDATA is unavailable. Set UR_RECOMP_USER_DATA_ROOT to a writable absolute directory and retry. 1>&2 & exit /b 3)\r\n"
        "set \"UR_RECOMP_USER_DATA_ROOT=%APPDATA%\\gamesbyian\\UR-Recomp\"\r\n"
        ":validate_user_root\r\n"
        "if \"%UR_RECOMP_USER_DATA_ROOT:~1,2%\"==\":\\\" goto user_root_ready\r\n"
        "if \"%UR_RECOMP_USER_DATA_ROOT:~0,2%\"==\"\\\\\" goto user_root_ready\r\n"
        "echo UR-STARTUP-SAVE-ROOT: resolved user data root must be an absolute Windows path. 1>&2\r\n"
        "exit /b 3\r\n"
        ":user_root_ready\r\n"
        "for %%I in (\"%UR_RECOMP_USER_DATA_ROOT%\") do set \"UR_RECOMP_USER_DATA_ROOT=%%~fI\"\r\n"
        "for %%I in (\"%~dp0.\") do set \"UR_PACKAGE_ROOT=%%~fI\"\r\n"
        "set \"UR_PATH_CHECK=%UR_RECOMP_USER_DATA_ROOT%\"\r\n"
        ":check_user_root_location\r\n"
        "if /I \"%UR_PATH_CHECK%\"==\"%UR_PACKAGE_ROOT%\" goto package_root_rejected\r\n"
        "for %%I in (\"%UR_PATH_CHECK%\\..\") do set \"UR_PATH_PARENT=%%~fI\"\r\n"
        "if /I \"%UR_PATH_PARENT%\"==\"%UR_PATH_CHECK%\" goto user_root_outside_package\r\n"
        "set \"UR_PATH_CHECK=%UR_PATH_PARENT%\"\r\n"
        "goto check_user_root_location\r\n"
        ":package_root_rejected\r\n"
        "echo UR-STARTUP-SAVE-ROOT: user data directory must be outside the extracted package. Choose another absolute location and retry. 1>&2\r\n"
        "exit /b 3\r\n"
        ":user_root_outside_package\r\n"
        "if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\\" mkdir \"%UR_RECOMP_USER_DATA_ROOT%\" 2>nul\r\n"
        "if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\\" (echo UR-STARTUP-SAVE-ROOT: cannot create the configured user data directory. Choose a writable absolute location and retry. 1>&2 & exit /b 3)\r\n"
        "set \"UR_WRITE_PROBE=%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-write-probe-%RANDOM%-%RANDOM%.tmp\"\r\n"
        "> \"%UR_WRITE_PROBE%\" echo writable\r\n"
        "if errorlevel 1 (echo UR-STARTUP-SAVE-ROOT: the configured user data directory is not writable. Check permissions or choose another absolute location. 1>&2 & exit /b 3)\r\n"
        "del /q \"%UR_WRITE_PROBE%\" >nul 2>&1\r\n"
        "del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-config.ini.migrate.tmp\" >nul 2>&1\r\n"
        "del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-keybinds.ini.migrate.tmp\" >nul 2>&1\r\n"
        "del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-mod-state.toml.migrate.tmp\" >nul 2>&1\r\n"
        "rmdir /s /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-saves.migrate.tmp\" >nul 2>&1\r\n"
        "if exist \"config.ini\" if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\config.ini\" (\r\n"
        "  copy /b /y \"config.ini\" \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-config.ini.migrate.tmp\" >nul\r\n"
        "  if errorlevel 1 (del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-config.ini.migrate.tmp\" >nul 2>&1 & echo UR-STARTUP-SAVE-ROOT: could not stage legacy config.ini migration. 1>&2 & exit /b 3)\r\n"
        "  ren \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-config.ini.migrate.tmp\" \"config.ini\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\config.ini\" (del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-config.ini.migrate.tmp\" >nul 2>&1) else (echo UR-STARTUP-SAVE-ROOT: could not commit legacy config.ini migration. 1>&2 & exit /b 3)\r\n"
        ")\r\n"
        "if exist \"keybinds.ini\" if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\keybinds.ini\" (\r\n"
        "  copy /b /y \"keybinds.ini\" \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-keybinds.ini.migrate.tmp\" >nul\r\n"
        "  if errorlevel 1 (del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-keybinds.ini.migrate.tmp\" >nul 2>&1 & echo UR-STARTUP-SAVE-ROOT: could not stage legacy keybinds.ini migration. 1>&2 & exit /b 3)\r\n"
        "  ren \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-keybinds.ini.migrate.tmp\" \"keybinds.ini\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\keybinds.ini\" (del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-keybinds.ini.migrate.tmp\" >nul 2>&1) else (echo UR-STARTUP-SAVE-ROOT: could not commit legacy keybinds.ini migration. 1>&2 & exit /b 3)\r\n"
        ")\r\n"
        "if exist \"saves\\\" if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\saves\\\" (\r\n"
        "  xcopy \"saves\" \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-saves.migrate.tmp\\\" /e /i /h /k /y >nul\r\n"
        "  if errorlevel 2 (rmdir /s /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-saves.migrate.tmp\" >nul 2>&1 & echo UR-STARTUP-SAVE-ROOT: could not stage legacy saves migration. 1>&2 & exit /b 3)\r\n"
        "  ren \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-saves.migrate.tmp\" \"saves\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\saves\\\" (rmdir /s /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-saves.migrate.tmp\" >nul 2>&1) else (echo UR-STARTUP-SAVE-ROOT: could not commit legacy saves migration. 1>&2 & exit /b 3)\r\n"
        ")\r\n"
        "if exist \"mods\\preloaded\\state.toml\" if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml\" (\r\n"
        "  copy /b /y \"mods\\preloaded\\state.toml\" \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-mod-state.toml.migrate.tmp\" >nul\r\n"
        "  if errorlevel 1 (del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-mod-state.toml.migrate.tmp\" >nul 2>&1 & echo UR-STARTUP-SAVE-ROOT: could not stage legacy mod-state migration. 1>&2 & exit /b 3)\r\n"
        "  ren \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-mod-state.toml.migrate.tmp\" \"mod-state.toml\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml\" (del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-mod-state.toml.migrate.tmp\" >nul 2>&1) else (echo UR-STARTUP-SAVE-ROOT: could not commit legacy mod-state migration. 1>&2 & exit /b 3)\r\n"
        ")\r\n"
        "set \"SNESRECOMP_USER_DATA_DIR=%UR_RECOMP_USER_DATA_ROOT%\"\r\n"
        "set \"SNESRECOMP_MOD_STATE_PATH=%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml\"\r\n"
        f"\"{EXE_NAME}\" \"{ROM_NAME}\" %*\r\n"
        "exit /b %ERRORLEVEL%\r\n",
        encoding="utf-8",
        newline="",
    )


def write_readme(path: Path) -> None:
    path.write_text(
        "UR-Recomp - Windows x64 portable package\n"
        "\n"
        "This is the portable Windows build. Extract the whole folder before "
        "running it; do not run directly from inside the ZIP. The package "
        "files themselves are treated as read-only. This ZIP does not register "
        "an installer or uninstaller.\n"
        "\n"
        f"Start the game with {LAUNCHER_NAME}. Keep {EXE_NAME}, {ROM_NAME}, "
        "rom.cfg and the mods directory together.\n"
        "\n"
        "Mutable user data is stored outside the extracted package under "
        "%APPDATA%\\\\gamesbyian\\\\UR-Recomp by default. Set "
        "UR_RECOMP_USER_DATA_ROOT before launching to choose another writable "
        "absolute Windows path (drive-rooted or UNC). Relative overrides and a "
        "non-absolute resolved APPDATA root are rejected. The resolved root must "
        "also be outside the extracted package and all of its subdirectories. "
        "Config, keyboard bindings, cartridge/profile saves, mod "
        "selection state, Modern settings/profile metadata and run history "
        "share this policy.\n"
        "\n"
        "If an older portable folder already contains config.ini, "
        "keybinds.ini, saves, or mods/preloaded/state.toml, the launcher "
        "copies them into an empty corresponding user-data location on first "
        "launch. Existing user-data "
        "files always win, so migration is deterministic and safe to repeat.\n"
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
    source_revision = source_revision.strip()
    if not source_revision:
        raise ValueError("source revision is required for a shippable package")

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
        or not isinstance(manifest.get("source_revision"), str)
        or not manifest["source_revision"].strip()
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
                or not isinstance(manifest.get("source_revision"), str)
                or not manifest["source_revision"].strip()
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
