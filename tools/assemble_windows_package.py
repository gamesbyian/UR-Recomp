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
ROM_CONFIG_NAME = "rom.cfg"
ROM_CONFIG_BYTES = f"{ROM_NAME}\n".encode("ascii")
MANIFEST_NAME = "PACKAGE-MANIFEST.json"
LAUNCHER_NAME = "run-uniracers.cmd"
README_NAME = "README.txt"
ARCHIVE_ROOT = "UR-Recomp-Windows-x64"
ARCHIVE_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ARCHIVE_CHECKSUM_SUFFIX = ".sha256"
MUTABLE_PACKAGE_PATHS = {"mods/preloaded/state.toml"}
# Consumer ZIP verification must never trust decompressed payload size or the
# manifest's claimed file sizes. These bounds also apply to the producer so a
# locally assembled archive is never larger than the independent verifier
# admits. Keep I/O memory bounded independently of the archive size.
MAX_PACKAGE_ENTRIES = 10000
MAX_PACKAGE_FILE_BYTES = 512 * 1024 * 1024
MAX_PACKAGE_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_PACKAGE_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_PACKAGE_README_BYTES = 256 * 1024
MAX_PACKAGE_ROM_CONFIG_BYTES = 1 * 1024 * 1024
ARCHIVE_IO_CHUNK_BYTES = 1 << 20
REQUIRED_PACKAGE_FILES = {
    EXE_NAME,
    ROM_NAME,
    ROM_CONFIG_NAME,
    LAUNCHER_NAME,
    README_NAME,
}


STARTUP_SUPPORT_GUIDANCE = (
    (
        "UR-STARTUP-ROM-MISSING",
        "The packaged ROM is missing. Re-extract the complete ZIP and retry.",
    ),
    (
        "UR-STARTUP-ROM-INVALID",
        "The ROM does not match this build. Restore the packaged verified ROM.",
    ),
    (
        "UR-STARTUP-RUNTIME-DATA",
        "Required package files are missing. Re-extract the complete ZIP.",
    ),
    (
        "UR-STARTUP-SAVE-ROOT",
        "The user-data path is unusable. Choose a writable absolute path outside the package.",
    ),
    (
        "UR-STARTUP-VIDEO",
        "Video initialization failed. Reset display settings or update the graphics driver.",
    ),
    (
        "UR-STARTUP-AUDIO",
        "Audio initialization failed. Check the Windows audio device and driver.",
    ),
    (
        "UR-STARTUP-CONTROLLER",
        "Controller initialization failed. Reconnect controllers or restart Windows.",
    ),
)


def startup_support_text() -> str:
    lines = ["Startup code guide:"]
    lines.extend(
        f"  {code}: {guidance}"
        for code, guidance in STARTUP_SUPPORT_GUIDANCE
    )
    return "\n".join(lines)


def normalize_source_revision(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("source revision must be a string")
    revision = value.strip()
    if (
        not revision
        or revision != value
        or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in revision)
    ):
        raise ValueError("source revision must be one non-empty canonical line")
    return revision


def expected_readme_revision_line(source_revision: str) -> str:
    return f"Source revision: {source_revision}"


def canonical_manifest_bytes(manifest: dict[str, object]) -> bytes:
    return (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def is_same_or_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_files(root: Path) -> list[dict[str, object]]:
    files: list[dict[str, object]] = []
    total_bytes = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative == MANIFEST_NAME:
            continue
        size = path.stat().st_size
        total_bytes += size
        if (
            size > MAX_PACKAGE_FILE_BYTES
            or total_bytes > MAX_PACKAGE_TOTAL_BYTES
            or len(files) >= MAX_PACKAGE_ENTRIES
        ):
            raise ValueError("package payload exceeds shipping size limits")
        if relative == README_NAME and size > MAX_PACKAGE_README_BYTES:
            raise ValueError("package README exceeds shipping size limit")
        files.append(
            {
                "path": relative,
                "size": size,
                "sha256": sha256(path),
            }
        )
    return files


def validate_rom_config(payload: bytes, *, context: str) -> None:
    if payload != ROM_CONFIG_BYTES:
        raise ValueError(
            f"{context} rom.cfg must contain canonical package-relative ROM path "
            f"{ROM_NAME}"
        )


def validate_required_package_paths(
    paths: set[str], *, context: str = "package"
) -> None:
    missing = sorted(REQUIRED_PACKAGE_FILES - paths)
    if missing:
        raise ValueError(
            f"required {context} files missing: " + ", ".join(missing)
        )
    if not any(path.startswith("mods/") for path in paths):
        raise ValueError(f"{context} mods directory is empty")
    unexpected = sorted(
        path
        for path in paths
        if path not in REQUIRED_PACKAGE_FILES and not path.startswith("mods/")
    )
    if unexpected:
        raise ValueError(
            f"unexpected {context} files: " + ", ".join(unexpected)
        )
    mutable = sorted(MUTABLE_PACKAGE_PATHS & paths)
    if mutable:
        raise ValueError(
            f"{context} contains mutable user state: " + ", ".join(mutable)
        )


def write_launcher(path: Path, source_revision: str) -> None:
    path.write_text(
        "@echo off\r\n"
        "setlocal DisableDelayedExpansion\r\n"
        "cd /d \"%~dp0\"\r\n"

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
        "if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\\" mkdir \"%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\" 2>nul\r\n"
        # ur-startup-log-v1 seeds seven bootstrap lines here. A host-side
        # classified failure may append four more, including one safe path,
        # and the launcher then records the host process_exit line.
        "if exist \"%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\\" (\r\n"
        "  set \"UR_RECOMP_STARTUP_LOG=%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log\"\r\n"
        "  set \"SNESRECOMP_STARTUP_LOG=%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log\"\r\n"
        "  > \"%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log\" echo schema=ur-startup-log-v1\r\n"
        f"  >> \"%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log\" echo build_revision={source_revision}\r\n"
        "  >> \"%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log\" echo architecture=x64\r\n"
        "  >> \"%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log\" echo subsystem=bootstrap\r\n"
        "  >> \"%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log\" echo package_root=%UR_PACKAGE_ROOT%\r\n"
        "  >> \"%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log\" echo user_data_root=%UR_RECOMP_USER_DATA_ROOT%\r\n"
        "  >> \"%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log\" echo result=startup-begin\r\n"
        ")\r\n"
        f"if not exist \"{EXE_NAME}\" (call :startup_fail \"UR-STARTUP-RUNTIME-DATA\" \"runtime-data\" \"Required package file is missing: {EXE_NAME}. Re-extract the complete package.\" & exit /b 2)\r\n"
        f"if not exist \"{ROM_NAME}\" (call :startup_fail \"UR-STARTUP-ROM-MISSING\" \"rom\" \"Packaged ROM is missing: {ROM_NAME}. Restore the package or your verified personal dump.\" & exit /b 2)\r\n"
        "if not exist \"rom.cfg\" (call :startup_fail \"UR-STARTUP-RUNTIME-DATA\" \"runtime-data\" \"Required package file is missing: rom.cfg. Re-extract the complete package.\" & exit /b 2)\r\n"
        "if not exist \"mods\\\" (call :startup_fail \"UR-STARTUP-RUNTIME-DATA\" \"runtime-data\" \"Required package directory is missing: mods. Re-extract the complete package.\" & exit /b 2)\r\n"
        "for /f \"delims=\" %%I in ('dir /b /s /a-d \"mods\\*\" 2^>nul') do goto mods_payload_ready\r\n"
        "call :startup_fail \"UR-STARTUP-RUNTIME-DATA\" \"runtime-data\" \"Required package directory is empty: mods. Re-extract the complete package.\"\r\n"
        "exit /b 2\r\n"
        ":mods_payload_ready\r\n"
        "if exist \"%UR_RECOMP_USER_DATA_ROOT%\\config.ini\\\" (call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"User data config.ini is a directory. Remove or rename it and retry.\" & exit /b 3)\r\n"
        "if exist \"%UR_RECOMP_USER_DATA_ROOT%\\keybinds.ini\\\" (call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"User data keybinds.ini is a directory. Remove or rename it and retry.\" & exit /b 3)\r\n"
        "if exist \"%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml\\\" (call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"User data mod-state.toml is a directory. Remove or rename it and retry.\" & exit /b 3)\r\n"
        "if exist \"%UR_RECOMP_USER_DATA_ROOT%\\rom.cfg\\\" (call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"User data rom.cfg is a directory. Remove or rename it and retry.\" & exit /b 3)\r\n"
        "if exist \"%UR_RECOMP_USER_DATA_ROOT%\\saves\" if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\saves\\\" (call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"User data saves path is not a directory. Remove or rename it and retry.\" & exit /b 3)\r\n"
        "set \"UR_MIGRATE_TOKEN=%RANDOM%-%RANDOM%\"\r\n"
        "set \"UR_MIGRATE_CONFIG=%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-config.ini.%UR_MIGRATE_TOKEN%.migrate.tmp\"\r\n"
        "set \"UR_MIGRATE_KEYS=%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-keybinds.ini.%UR_MIGRATE_TOKEN%.migrate.tmp\"\r\n"
        "set \"UR_MIGRATE_SAVES=%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-saves.%UR_MIGRATE_TOKEN%.migrate.tmp\"\r\n"
        "set \"UR_MIGRATE_MOD=%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-mod-state.toml.%UR_MIGRATE_TOKEN%.migrate.tmp\"\r\n"
        "if exist \"config.ini\" if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\config.ini\" (\r\n"
        "  copy /b /y \"config.ini\" \"%UR_MIGRATE_CONFIG%\" >nul\r\n"
        "  if errorlevel 1 (del /q \"%UR_MIGRATE_CONFIG%\" >nul 2>&1 & call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"Could not stage legacy config.ini migration.\" & exit /b 3)\r\n"
        "  ren \"%UR_MIGRATE_CONFIG%\" \"config.ini\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\config.ini\" attrib -R \"%UR_RECOMP_USER_DATA_ROOT%\\config.ini\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\config.ini\" (del /q \"%UR_MIGRATE_CONFIG%\" >nul 2>&1) else (call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"Could not commit legacy config.ini migration.\" & exit /b 3)\r\n"
        ")\r\n"
        "if exist \"keybinds.ini\" if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\keybinds.ini\" (\r\n"
        "  copy /b /y \"keybinds.ini\" \"%UR_MIGRATE_KEYS%\" >nul\r\n"
        "  if errorlevel 1 (del /q \"%UR_MIGRATE_KEYS%\" >nul 2>&1 & call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"Could not stage legacy keybinds.ini migration.\" & exit /b 3)\r\n"
        "  ren \"%UR_MIGRATE_KEYS%\" \"keybinds.ini\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\keybinds.ini\" attrib -R \"%UR_RECOMP_USER_DATA_ROOT%\\keybinds.ini\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\keybinds.ini\" (del /q \"%UR_MIGRATE_KEYS%\" >nul 2>&1) else (call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"Could not commit legacy keybinds.ini migration.\" & exit /b 3)\r\n"
        ")\r\n"
        "if exist \"saves\\\" if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\saves\\\" (\r\n"
        "  mkdir \"%UR_MIGRATE_SAVES%\" >nul 2>&1\r\n"
        "  if not exist \"%UR_MIGRATE_SAVES%\\\" (call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"Could not create legacy saves staging directory.\" & exit /b 3)\r\n"
        "  xcopy \"saves\" \"%UR_MIGRATE_SAVES%\\\" /e /i /h /y >nul\r\n"
        "  if errorlevel 2 (rmdir /s /q \"%UR_MIGRATE_SAVES%\" >nul 2>&1 & call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"Could not stage legacy saves migration.\" & exit /b 3)\r\n"
        "  ren \"%UR_MIGRATE_SAVES%\" \"saves\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\saves\\\" attrib -R \"%UR_RECOMP_USER_DATA_ROOT%\\saves\\*\" /s /d >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\saves\\\" (rmdir /s /q \"%UR_MIGRATE_SAVES%\" >nul 2>&1) else (call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"Could not commit legacy saves migration.\" & exit /b 3)\r\n"
        ")\r\n"
        "if exist \"mods\\preloaded\\state.toml\" if not exist \"%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml\" (\r\n"
        "  copy /b /y \"mods\\preloaded\\state.toml\" \"%UR_MIGRATE_MOD%\" >nul\r\n"
        "  if errorlevel 1 (del /q \"%UR_MIGRATE_MOD%\" >nul 2>&1 & call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"Could not stage legacy mod-state migration.\" & exit /b 3)\r\n"
        "  ren \"%UR_MIGRATE_MOD%\" \"mod-state.toml\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml\" attrib -R \"%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml\" >nul 2>&1\r\n"
        "  if exist \"%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml\" (del /q \"%UR_MIGRATE_MOD%\" >nul 2>&1) else (call :startup_fail \"UR-STARTUP-SAVE-ROOT\" \"save-root\" \"Could not commit legacy mod-state migration.\" & exit /b 3)\r\n"
        ")\r\n"
        "del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-config.ini.migrate.tmp\" >nul 2>&1\r\n"
        "del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-keybinds.ini.migrate.tmp\" >nul 2>&1\r\n"
        "del /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-mod-state.toml.migrate.tmp\" >nul 2>&1\r\n"
        "rmdir /s /q \"%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-saves.migrate.tmp\" >nul 2>&1\r\n"
        "set \"SNESRECOMP_USER_DATA_DIR=%UR_RECOMP_USER_DATA_ROOT%\"\r\n"
        "set \"SNESRECOMP_MOD_STATE_PATH=%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml\"\r\n"
        f"\"%~dp0{EXE_NAME}\" \"%~dp0{ROM_NAME}\" %*\r\n"
        "set \"UR_GAME_RC=%ERRORLEVEL%\"\r\n"
        "if defined UR_RECOMP_STARTUP_LOG >> \"%UR_RECOMP_STARTUP_LOG%\" echo process_exit=%UR_GAME_RC%\r\n"
        "exit /b %UR_GAME_RC%\r\n"
        ":startup_fail\r\n"
        "echo %~1: %~3 1>&2\r\n"
        "if defined UR_RECOMP_STARTUP_LOG (\r\n"
        "  >> \"%UR_RECOMP_STARTUP_LOG%\" echo code=%~1\r\n"
        "  >> \"%UR_RECOMP_STARTUP_LOG%\" echo subsystem=%~2\r\n"
        "  >> \"%UR_RECOMP_STARTUP_LOG%\" echo result=fatal\r\n"
        ")\r\n"
        "exit /b 0\r\n",
        encoding="utf-8",
        newline="",
    )


def readme_text(source_revision: str) -> str:
    return (
        "UR-Recomp - Windows x64 portable package\n"
        f"Source revision: {source_revision}\n"
        "\n"
        "This is the portable Windows build. Extract the whole folder before "
        "running it; do not run directly from inside the ZIP. The package "
        "files themselves are treated as read-only. The executable is built "
        "with the static MSVC runtime, so the package does not require a "
        "separately installed Visual C++ Redistributable. This ZIP does not "
        "register an installer or uninstaller.\n"
        "\n"
        f"Start the game with {LAUNCHER_NAME}. Keep {EXE_NAME}, {ROM_NAME}, "
        "rom.cfg and the mods directory together.\n"
        "\n"
        "Mutable user data is stored outside the extracted package under "
        "%APPDATA%\\gamesbyian\\UR-Recomp by default. Set "
        "UR_RECOMP_USER_DATA_ROOT before launching to choose another writable "
        "absolute Windows path (drive-rooted or UNC). Relative overrides and a "
        "non-absolute resolved APPDATA root are rejected. The resolved root must "
        "also be outside the extracted package and all of its subdirectories. "
        "Config, keyboard bindings, cartridge/profile saves, mod "
        "selection state, Modern settings/profile metadata and run history "
        "share this policy.\n"
        "\n"
        "If startup fails, the launcher prints one stable UR-STARTUP-* code "
        "with a concise recovery message. When the user-data root is writable, "
        "the same launch retains diagnostics\\startup.log there for support; "
        "the file is replaced on the next launch and contains no ROM bytes, "
        "save contents, profile names or controller input.\n"
        "\n"
        f"{startup_support_text()}\n"
        "\n"
        "If an older portable folder already contains config.ini, "
        "keybinds.ini, saves, or mods/preloaded/state.toml, the launcher "
        "copies them into an empty corresponding user-data location on first "
        "launch. Existing user-data "
        "files always win, so migration is deterministic and safe to repeat.\n"
        "\n"
        "To update this portable build, close the game, delete or move the old "
        "extracted UR-Recomp-Windows-x64 folder, then extract the new ZIP as a "
        "fresh folder. Do not overlay a new ZIP onto an old package tree. Your "
        "normal settings, profiles, bindings and run history live outside the "
        "package and are preserved across that replacement.\n"
        "\n"
        "Private personal-use preservation/remaster build.\n"
    )


def write_readme(path: Path, source_revision: str) -> None:
    path.write_bytes(readme_text(source_revision).encode("utf-8"))


def assemble(
    build_dir: Path,
    rom: Path,
    output: Path,
    source_revision: str,
) -> dict[str, object]:
    build_dir = build_dir.resolve()
    rom = rom.resolve()
    output = output.resolve()
    try:
        source_revision = normalize_source_revision(source_revision)
    except ValueError as exc:
        raise ValueError(
            "source revision is required for a shippable package"
        ) from exc

    if (
        is_same_or_within(output, build_dir)
        or is_same_or_within(build_dir, output)
    ):
        raise ValueError(
            "package output must be outside and must not contain the build directory"
        )
    if is_same_or_within(rom, output):
        raise ValueError("package output must not contain the source ROM")

    required_files = [build_dir / EXE_NAME, build_dir / ROM_CONFIG_NAME, rom]
    for path in required_files:
        if not path.is_file():
            raise ValueError(f"required package input missing: {path}")
    mods = build_dir / "mods"
    if not mods.is_dir():
        raise ValueError(f"required package input missing: {mods}")
    if not any(path.is_file() for path in mods.rglob("*")):
        raise ValueError(f"required package input empty: {mods}")

    if output.exists():
        if not output.is_dir():
            raise ValueError(
                "package output exists and is not a directory"
            )
        shutil.rmtree(output)
    output.mkdir(parents=True)

    shutil.copy2(build_dir / EXE_NAME, output / EXE_NAME)
    (output / ROM_CONFIG_NAME).write_bytes(ROM_CONFIG_BYTES)
    shutil.copy2(rom, output / ROM_NAME)
    shutil.copytree(mods, output / "mods")
    for relative in MUTABLE_PACKAGE_PATHS:
        candidate = output / relative
        if candidate.is_file() or candidate.is_symlink():
            candidate.unlink()
    write_launcher(output / LAUNCHER_NAME, source_revision)
    write_readme(output / README_NAME, source_revision)

    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "package_format": PACKAGE_FORMAT,
        "source_revision": source_revision,
        "files": package_files(output),
    }
    manifest_bytes = canonical_manifest_bytes(manifest)
    if len(manifest_bytes) > MAX_PACKAGE_MANIFEST_BYTES:
        raise ValueError("package manifest exceeds shipping size limit")
    (output / MANIFEST_NAME).write_bytes(manifest_bytes)
    return manifest


def verify(package: Path) -> dict[str, object]:
    package = package.resolve()
    manifest_path = package / MANIFEST_NAME
    if not manifest_path.is_file():
        raise ValueError(f"package manifest missing: {manifest_path}")

    if manifest_path.stat().st_size > MAX_PACKAGE_MANIFEST_BYTES:
        raise ValueError("package manifest exceeds shipping size limit")
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read package manifest: {exc}") from exc
    if manifest_bytes != canonical_manifest_bytes(manifest):
        raise ValueError("package manifest is not canonical UTF-8/LF JSON")

    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("package_format") != PACKAGE_FORMAT
        or not isinstance(manifest.get("files"), list)
    ):
        raise ValueError("unsupported or malformed package manifest")
    try:
        source_revision = normalize_source_revision(manifest.get("source_revision"))
    except ValueError as exc:
        raise ValueError("unsupported or malformed package manifest") from exc

    expected = manifest["files"]
    actual = package_files(package)
    if actual != expected:
        raise ValueError("package contents do not match PACKAGE-MANIFEST.json")

    actual_paths = {entry["path"] for entry in actual}
    validate_required_package_paths(actual_paths, context="packaged")
    if (package / ROM_CONFIG_NAME).stat().st_size > MAX_PACKAGE_ROM_CONFIG_BYTES:
        raise ValueError("packaged rom.cfg exceeds shipping size limit")
    try:
        validate_rom_config(
            (package / ROM_CONFIG_NAME).read_bytes(), context="packaged"
        )
    except OSError as exc:
        raise ValueError(f"cannot read packaged rom.cfg: {exc}") from exc
    if (package / README_NAME).stat().st_size > MAX_PACKAGE_README_BYTES:
        raise ValueError("package README exceeds shipping size limit")
    try:
        readme_bytes = (package / README_NAME).read_bytes()
        readme = readme_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"cannot read packaged README: {exc}") from exc
    if (
        expected_readme_revision_line(source_revision)
        not in readme.splitlines()
    ):
        raise ValueError(
            "package README source revision does not match manifest"
        )
    if readme_bytes != readme_text(source_revision).encode("utf-8"):
        raise ValueError("package README is not canonical UTF-8/LF content")

    return manifest


def write_archive_checksum(archive: Path, output: Path) -> str:
    archive = archive.resolve()
    output = output.resolve()
    if not archive.is_file():
        raise ValueError(f"package archive missing: {archive}")
    if output == archive:
        raise ValueError("archive checksum output must be separate from the archive")
    if output.exists() and not output.is_file():
        raise ValueError("archive checksum output exists and is not a file")
    output.parent.mkdir(parents=True, exist_ok=True)
    digest = sha256(archive)
    output.write_text(
        f"{digest}  {archive.name}\n",
        encoding="ascii",
        newline="\n",
    )
    return digest


def verify_archive_checksum(archive: Path, checksum: Path) -> str:
    archive = archive.resolve()
    checksum = checksum.resolve()
    if not archive.is_file():
        raise ValueError(f"package archive missing: {archive}")
    if not checksum.is_file():
        raise ValueError(f"archive checksum missing: {checksum}")

    try:
        # Bytes, not text mode: universal newlines would hide a CRLF sidecar.
        raw = checksum.read_bytes().decode("ascii")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"cannot read archive checksum: {exc}") from exc

    expected_name = archive.name
    lines = raw.splitlines()
    if len(lines) != 1 or raw != raw.rstrip("\r\n") + "\n":
        raise ValueError("archive checksum must be one canonical LF-terminated line")
    line = lines[0]
    if len(line) != 64 + 2 + len(expected_name) or line[64:66] != "  ":
        raise ValueError("archive checksum has malformed canonical format")
    digest = line[:64]
    filename = line[66:]
    if (
        filename != expected_name
        or any(ch not in "0123456789abcdef" for ch in digest)
    ):
        raise ValueError("archive checksum does not identify this archive")

    actual = sha256(archive)
    if digest != actual:
        raise ValueError("archive checksum does not match package archive")
    return actual


def create_archive(package: Path, archive: Path) -> dict[str, object]:
    package = package.resolve()
    archive = archive.resolve()
    if is_same_or_within(archive, package):
        raise ValueError("package archive must be written outside the package tree")
    manifest = verify(package)
    if archive.exists():
        if not archive.is_file():
            raise ValueError(
                "package archive output exists and is not a file"
            )
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
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            if path.stat().st_size > MAX_PACKAGE_FILE_BYTES:
                raise ValueError(f"archive entry exceeds shipping size limit: {relative}")
            with path.open("rb") as src, output.open(info, "w", force_zip64=True) as dst:
                shutil.copyfileobj(src, dst, ARCHIVE_IO_CHUNK_BYTES)
    return manifest


def verify_archive(archive: Path) -> dict[str, object]:
    archive = archive.resolve()
    if not archive.is_file():
        raise ValueError(f"package archive missing: {archive}")

    manifest_name = f"{ARCHIVE_ROOT}/{MANIFEST_NAME}"
    try:
        with zipfile.ZipFile(archive, "r") as source:
            infos = source.infolist()
            if len(infos) > MAX_PACKAGE_ENTRIES + 1:
                raise ValueError("package archive has too many files")
            names = [info.filename for info in infos]
            info_by_name = {info.filename: info for info in infos}
            total_bytes = 0
            for info in infos:
                total_bytes += info.file_size
                if (
                    info.file_size > MAX_PACKAGE_FILE_BYTES
                    or total_bytes > MAX_PACKAGE_TOTAL_BYTES +
                        MAX_PACKAGE_MANIFEST_BYTES
                ):
                    raise ValueError("package archive exceeds shipping size limits")
                if (
                    info.date_time != ARCHIVE_TIMESTAMP
                    or info.compress_type != zipfile.ZIP_DEFLATED
                    or info.create_system != 3
                    or info.external_attr != (0o100644 << 16)
                ):
                    raise ValueError(
                        f"package archive metadata is not normalized: {info.filename}"
                    )
            if len(names) != len(set(names)):
                raise ValueError("package archive contains duplicate paths")
            if any(
                name.startswith("/") or "\\" in name or ".." in Path(name).parts
                for name in names
            ):
                raise ValueError("package archive contains unsafe paths")
            if manifest_name not in names:
                raise ValueError("package archive manifest missing")
            if info_by_name[manifest_name].file_size > MAX_PACKAGE_MANIFEST_BYTES:
                raise ValueError("package archive manifest exceeds shipping size limit")
            if info_by_name.get(f"{ARCHIVE_ROOT}/{README_NAME}") and (
                info_by_name[f"{ARCHIVE_ROOT}/{README_NAME}"].file_size >
                    MAX_PACKAGE_README_BYTES
            ):
                raise ValueError("package archive README exceeds shipping size limit")
            if info_by_name.get(f"{ARCHIVE_ROOT}/{ROM_CONFIG_NAME}") and (
                info_by_name[f"{ARCHIVE_ROOT}/{ROM_CONFIG_NAME}"].file_size >
                    MAX_PACKAGE_ROM_CONFIG_BYTES
            ):
                raise ValueError("package archive rom.cfg exceeds shipping size limit")
            try:
                manifest_bytes = source.read(manifest_name)
                manifest = json.loads(manifest_bytes.decode("utf-8"))
            except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"cannot read package archive manifest: {exc}"
                ) from exc

            if (
                not isinstance(manifest, dict)
                or manifest.get("schema_version") != SCHEMA_VERSION
                or manifest.get("package_format") != PACKAGE_FORMAT
                or not isinstance(manifest.get("files"), list)
            ):
                raise ValueError("unsupported or malformed package archive manifest")
            if manifest_bytes != canonical_manifest_bytes(manifest):
                raise ValueError(
                    "package archive manifest is not canonical UTF-8/LF JSON"
                )
            try:
                source_revision = normalize_source_revision(
                    manifest.get("source_revision")
                )
            except ValueError as exc:
                raise ValueError(
                    "unsupported or malformed package archive manifest"
                ) from exc

            expected_names = {manifest_name}
            relative_paths: set[str] = set()
            for entry in manifest["files"]:
                if not isinstance(entry, dict):
                    raise ValueError("malformed package archive file entry")
                relative = entry.get("path")
                expected_size = entry.get("size")
                expected_hash = entry.get("sha256")
                if (
                    not isinstance(relative, str)
                    or type(expected_size) is not int
                    or expected_size < 0
                    or expected_size > MAX_PACKAGE_FILE_BYTES
                    or not isinstance(expected_hash, str)
                    or len(expected_hash) != 64
                    or any(ch not in "0123456789abcdef" for ch in expected_hash)
                ):
                    raise ValueError("malformed package archive file entry")
                relative_path = Path(relative)
                if (
                    not relative
                    or relative.startswith("/")
                    or "\\" in relative
                    or ".." in relative_path.parts
                    or relative_path.as_posix() != relative
                ):
                    raise ValueError(
                        f"unsafe package archive manifest path: {relative}"
                    )
                if relative in relative_paths:
                    raise ValueError(
                        f"duplicate package archive manifest path: {relative}"
                    )
                relative_paths.add(relative)
                name = f"{ARCHIVE_ROOT}/{relative}"
                expected_names.add(name)
                info = info_by_name.get(name)
                if info is None:
                    raise ValueError(f"package archive payload missing: {relative}")
                if info.file_size != expected_size:
                    raise ValueError(f"package archive size mismatch: {relative}")
                # ZipExtFile yields bounded chunks; never source.read(name)
                # into one allocation, even when the ZIP and manifest agree.
                digest = hashlib.sha256()
                observed_size = 0
                with source.open(info) as payload:
                    while True:
                        chunk = payload.read(ARCHIVE_IO_CHUNK_BYTES)
                        if not chunk:
                            break
                        observed_size += len(chunk)
                        if observed_size > expected_size:
                            raise ValueError(
                                f"package archive size mismatch: {relative}"
                            )
                        digest.update(chunk)
                if observed_size != expected_size:
                    raise ValueError(f"package archive size mismatch: {relative}")
                if digest.hexdigest() != expected_hash:
                    raise ValueError(f"package archive checksum mismatch: {relative}")

            validate_required_package_paths(
                relative_paths, context="archive package"
            )
            try:
                validate_rom_config(
                    source.read(f"{ARCHIVE_ROOT}/{ROM_CONFIG_NAME}"),
                    context="archive package",
                )
            except KeyError as exc:
                raise ValueError("cannot read package archive rom.cfg") from exc
            readme_name = f"{ARCHIVE_ROOT}/{README_NAME}"
            try:
                readme_bytes = source.read(readme_name)
                readme = readme_bytes.decode("utf-8")
            except (KeyError, UnicodeDecodeError) as exc:
                raise ValueError("cannot read package archive README") from exc
            if (
                expected_readme_revision_line(source_revision)
                not in readme.splitlines()
            ):
                raise ValueError(
                    "package archive README source revision does not match manifest"
                )
            if readme_bytes != readme_text(source_revision).encode("utf-8"):
                raise ValueError(
                    "package archive README is not canonical UTF-8/LF content"
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

    checksum_parser = subparsers.add_parser("checksum-archive")
    checksum_parser.add_argument("--archive", type=Path, required=True)
    checksum_parser.add_argument("--output", type=Path)

    verify_checksum_parser = subparsers.add_parser("verify-archive-checksum")
    verify_checksum_parser.add_argument("--archive", type=Path, required=True)
    verify_checksum_parser.add_argument("--checksum", type=Path, required=True)

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
        elif args.command == "verify-archive":
            manifest = verify_archive(args.archive)
            print(
                f"WINDOWS_PACKAGE_ARCHIVE_VERIFIED files={len(manifest['files'])} "
                f"archive={args.archive}"
            )
        elif args.command == "checksum-archive":
            output = args.output or Path(
                str(args.archive) + ARCHIVE_CHECKSUM_SUFFIX
            )
            digest = write_archive_checksum(args.archive, output)
            print(
                f"WINDOWS_PACKAGE_ARCHIVE_SHA256 sha256={digest} "
                f"output={output}"
            )
        else:
            digest = verify_archive_checksum(args.archive, args.checksum)
            print(
                f"WINDOWS_PACKAGE_ARCHIVE_SHA256_VERIFIED sha256={digest} "
                f"archive={args.archive}"
            )
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
