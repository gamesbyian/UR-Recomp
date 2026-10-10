#!/usr/bin/env python3
"""Build a ROM-free, reproducible Baldosa Modern Windows x64 candidate ZIP.

Unlike the existing full UR-Recomp shipping package, this provisional native
archive deliberately excludes the USA ROM and *all* mutable user data. The
player supplies a verified personal ROM dump beside the extracted executable.
No "complete Modern" or event-fidelity claim is made by the archive itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from check_windows_portable_binary import check_pe_x64

EXE = "UniracersSNESRecomp.exe"
LAUNCHER = "run-baldosa-modern.cmd"
README = "README-BALDOSA-CANDIDATE.txt"
MANIFEST = "BALDOSA-CANDIDATE-MANIFEST.json"
ROM = "Uniracers_USA.sfc"
USA_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
PREFIX = "UR-Recomp-Baldosa-Windows-x64/"
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
MAX_EXE_BYTES = 512 * 1024 * 1024


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def launcher() -> bytes:
    commands = [
        "@echo off",
        "setlocal DisableDelayedExpansion",
        'set "UR_BALDOSA_PACKAGE_DIR=%~dp0"',
        f'set "UR_BALDOSA_ROM=%~dp0{ROM}"',
        'if not exist "%UR_BALDOSA_ROM%" (echo UR-BALDOSA-STARTUP-ROM-MISSING: Copy a verified personal Uniracers USA dump beside the executable. 1>&2 & exit /b 2)',
        'if not defined UR_RECOMP_USER_DATA_ROOT (',
        '  if not defined APPDATA (echo UR-BALDOSA-STARTUP-SAVE-ROOT: APPDATA is not available. 1>&2 & exit /b 3)',
        '  set "UR_RECOMP_USER_DATA_ROOT=%APPDATA%\\gamesbyian\\UR-Recomp"',
        ')',
        # PowerShell 5.1 is inbox on supported Windows. Use ENV VARS, not
        # interpolated paths, to avoid command injection via user paths.
        'powershell.exe -NoProfile -NonInteractive -Command '
        '"$ErrorActionPreference = \'Stop\'; '
        '$p = [IO.Path]::GetFullPath($env:UR_BALDOSA_PACKAGE_DIR).TrimEnd(\'\\\'); '
        '$d = $env:UR_RECOMP_USER_DATA_ROOT; '
        'if (-not [IO.Path]::IsPathRooted($d)) { exit 3 }; '
        '$d = [IO.Path]::GetFullPath($d).TrimEnd(\'\\\'); '
        'if ($d -ieq $p -or $d.StartsWith($p + \'\\\', [StringComparison]::OrdinalIgnoreCase)) { exit 3 }; '
        'if ((Get-FileHash -LiteralPath $env:UR_BALDOSA_ROM -Algorithm SHA256).Hash '
        f'-ine \'{USA_SHA256}\') {{ exit 2 }}"',
        'if errorlevel 3 (echo UR-BALDOSA-STARTUP-SAVE-ROOT: Invalid or package-local user-data root. 1>&2 & exit /b 3)',
        'if errorlevel 2 (echo UR-BALDOSA-STARTUP-ROM-INVALID: USA ROM SHA-256 mismatch. 1>&2 & exit /b 2)',
        'if errorlevel 1 (echo UR-BALDOSA-STARTUP-PREFLIGHT: Windows PowerShell verification failed. 1>&2 & exit /b 3)',
        'if not exist "%UR_RECOMP_USER_DATA_ROOT%\\" mkdir "%UR_RECOMP_USER_DATA_ROOT%" 2>nul',
        'if not exist "%UR_RECOMP_USER_DATA_ROOT%\\" (echo UR-BALDOSA-STARTUP-SAVE-ROOT: Could not create a writable user folder. 1>&2 & exit /b 3)',
        'set "SNESRECOMP_USER_DATA_DIR=%UR_RECOMP_USER_DATA_ROOT%"',
        'set "UR_EXECUTION_MODE=modern"',
        'set "UR_BALDOSA_MODERN_ROOT=1"',
        'set "UR_BALDOSA_MODERN_INPUT=1"',
        'set "UR_BALDOSA_MODERN_PROFILE_SELECT=1"',
        'cd /d "%UR_RECOMP_USER_DATA_ROOT%"',
        'if errorlevel 1 (echo UR-BALDOSA-STARTUP-SAVE-ROOT: Cannot enter user folder. 1>&2 & exit /b 3)',
        f'"%UR_BALDOSA_PACKAGE_DIR%{EXE}" --no-launcher "%UR_BALDOSA_ROM%" %*',
        'exit /b %ERRORLEVEL%',
    ]
    return ("\r\n".join(commands) + "\r\n").encode("utf-8")


def readme(revision: str) -> bytes:
    return (
        "UR-Recomp / Baldosa native Windows x64 candidate\n"
        "================================================\n\n"
        "This is a development candidate, NOT a completed remaster.\n"
        "The existing Modern root can enter original 1P/2P selection and\n"
        "provides native profile SRAM persistence where authorized.\n"
        "Practice, Records and Options are not yet integrated; no complete\n"
        "45-event fidelity, HD+widescreen product or run capture is claimed.\n\n"
        "HOW TO LAUNCH\n"
        "1. Extract the ZIP to a normal Windows folder.\n"
        "2. Copy your own legally obtained USA retail Uniracers ROM dump as\n"
        f"   {ROM} next to {EXE}.\n"
        f"   Required SHA-256: {USA_SHA256}\n"
        f"3. Double-click {LAUNCHER}.\n\n"
        "The ROM and all profile/save data are ABSENT from this archive.\n"
        "The launcher refuses a wrong ROM, validates the root, and uses\n"
        "%APPDATA%\\gamesbyian\\UR-Recomp for user state, or the optional\n"
        "absolute UR_RECOMP_USER_DATA_ROOT override. It refuses data paths\n"
        "inside the extracted package. Saved data is NEVER shipped in a ZIP.\n"
        "An existing named Modern profile needs a complete valid catalog,\n"
        "host-profile state and 8192-byte native save; otherwise startup\n"
        "refuses the profile instead of writing into another slot.\n\n"
        "To report a problem, include the exact startup diagnostic and\n"
        "reproduction steps, but never share personal ROMs or profile data.\n\n"
        f"Project source revision: {revision}\n"
    ).encode("utf-8")


def payloads(executable: Path, revision: str) -> dict[str, bytes]:
    if not revision or revision.strip() != revision or len(revision) > 100:
        raise ValueError("source revision must be one canonical short identifier")
    if any(ord(ch) < 33 or ord(ch) > 126 for ch in revision):
        raise ValueError("source revision contains invalid characters")
    if executable.name != EXE or executable.is_symlink():
        raise ValueError("expected non-symlink pinned native Windows executable")
    size = executable.stat().st_size
    if size < 65536 or size > MAX_EXE_BYTES:
        raise ValueError("native candidate executable outside size budget")
    check_pe_x64(executable)
    items = {
        EXE: executable.read_bytes(),
        LAUNCHER: launcher(),
        README: readme(revision),
    }
    manifest = {
        "format": "ur-recomp-baldosa-windows-x64-romless-candidate-v1",
        "project_revision": revision,
        "immutable_files": [
            {"path": name, "bytes": len(data), "sha256": sha256(data)}
            for name, data in sorted(items.items())
        ],
        "rom_bundled": False,
        "rom_filename": ROM,
        "rom_sha256_required": USA_SHA256,
        "profile_data_bundled": False,
        "status": "native-modern-root-stock-1p-2p-candidate-only",
    }
    items[MANIFEST] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return items


def create_candidate(executable: Path, archive: Path, revision: str) -> str:
    if archive.exists() or archive.is_symlink():
        raise ValueError("candidate archive destination already exists")
    items = payloads(executable, revision)
    if any(name.lower().endswith((".sfc", ".smc", ".srm", ".urrun")) for name in items):
        raise ValueError("protected ROM or mutable record entered archive")
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, mode="x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9, allowZip64=True) as z:
        for name, data in sorted(items.items()):
            info = zipfile.ZipInfo(PREFIX + name, date_time=ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED,
                       compresslevel=9)
    # Reopen the exact published bytes; the candidate cannot make a claim
    # about files other than those present in its own immutable manifest.
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if names != [PREFIX + name for name in sorted(items)]:
            raise ValueError("candidate file manifest does not match archive")
        for name, blob in items.items():
            if z.read(PREFIX + name) != blob:
                raise ValueError(f"candidate ZIP verification failed: {name}")
    return sha256(archive.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    digest = create_candidate(args.exe, args.out, args.revision)
    print(f"BALDOSA_NATIVE_ROMLESS_CANDIDATE path={args.out} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
