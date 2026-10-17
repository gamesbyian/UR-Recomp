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
        'set "UR_BALDOSA_RECOVERY_ACTION="',
        'set "UR_BALDOSA_RECOVERY_PROFILE_ID="',
        'set "UR_BALDOSA_RECOVERY_ATTEMPTED=0"',
        'set "UR_BALDOSA_PACKAGE_DIR=%~dp0"',
        f'set "UR_BALDOSA_ROM=%~dp0{ROM}"',
        'if not exist "%UR_BALDOSA_ROM%" (echo UR-BALDOSA-STARTUP-ROM-MISSING: Copy a verified personal Uniracers USA dump beside the executable. 1>&2 & echo The file Uniracers_USA.sfc was not found next to this launcher. 1>&2 & echo Copy your own USA retail dump there under that exact name and start again. 1>&2 & echo Nothing was changed. 1>&2 & call :UR-BALDOSA-HOLD & exit /b 2)',
        'if not defined UR_RECOMP_USER_DATA_ROOT (',
        '  if not defined APPDATA (echo UR-BALDOSA-STARTUP-SAVE-ROOT: APPDATA is not available. 1>&2 & echo Windows did not provide a per-user data folder. Set UR_RECOMP_USER_DATA_ROOT to a folder you own outside the game folder. 1>&2 & call :UR-BALDOSA-HOLD & exit /b 3)',
        '  set "UR_RECOMP_USER_DATA_ROOT=%APPDATA%\\gamesbyian\\UR-Recomp"',
        ')',
        # PowerShell 5.1 is inbox on supported Windows. Use ENV VARS, not
        # interpolated paths, to avoid command injection via user paths.
        'powershell.exe -NoProfile -NonInteractive -Command '
        '"$ErrorActionPreference = \'Stop\'; '
        '$p = [IO.Path]::GetFullPath($env:UR_BALDOSA_PACKAGE_DIR).TrimEnd(\'\\\'); '
        '$d = $env:UR_RECOMP_USER_DATA_ROOT; '
        # IsPathRooted also admits drive-relative (C:name) and current-drive-
        # root-relative (\\name) strings, which resolve against the process
        # state. Admit only a drive-qualified absolute path (X:\ or X:/) or a
        # UNC/device path (two leading separators, then a non-separator).
        # Character codes avoid any quoting trouble: 58 ':', 92 '\\', 47 '/'.
        # IsPathRooted stays as the first, independently pinned gate (the QA
        # verifier's canonical-launcher template names it); the exact check
        # below then narrows it to fully-qualified paths.
        'if (-not [IO.Path]::IsPathRooted($d)) { exit 3 }; '
        '$ok = ($d.Length -ge 3 -and [char]::IsLetter($d[0]) -and '
        '$d[1] -eq [char]58 -and ($d[2] -eq [char]92 -or $d[2] -eq [char]47)) '
        '-or ($d.Length -ge 3 -and $d[0] -eq [char]92 -and $d[1] -eq [char]92 '
        '-and $d[2] -ne [char]92 -and $d[2] -ne [char]47); '
        'if (-not $ok) { exit 3 }; '
        '$d = [IO.Path]::GetFullPath($d).TrimEnd(\'\\\'); '
        'if ($d -ieq $p -or $d.StartsWith($p + \'\\\', [StringComparison]::OrdinalIgnoreCase)) { exit 3 }; '
        # A syntactically external user-data root can still be a Windows
        # junction/symlink back into this executable directory. Reject all
        # existing reparse-point ancestors before creating user state, rather
        # than relying on GetFullPath (which normalizes text, not targets).
        '$walk = $d; '
        'while ($walk) { '
        '$entry = Get-Item -LiteralPath $walk -Force -ErrorAction SilentlyContinue; '
        'if ($entry -and (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { exit 3 }; '
        '$parent = [IO.Path]::GetDirectoryName($walk); '
        'if (-not $parent -or $parent -eq $walk) { break }; '
        '$walk = $parent; '
        '}; '
        'if ((Get-FileHash -LiteralPath $env:UR_BALDOSA_ROM -Algorithm SHA256).Hash '
        f'-ine \'{USA_SHA256}\') {{ exit 2 }}"',
        'if errorlevel 3 (echo UR-BALDOSA-STARTUP-SAVE-ROOT: Invalid or package-local user-data root. 1>&2 & echo Your save folder must be a normal folder outside this game folder. Unset UR_RECOMP_USER_DATA_ROOT to use the default under your user profile. 1>&2 & call :UR-BALDOSA-HOLD & exit /b 3)',
        'if errorlevel 2 (echo UR-BALDOSA-STARTUP-ROM-INVALID: USA ROM SHA-256 mismatch. 1>&2 & echo Uniracers_USA.sfc is not the supported USA release: wrong region, an edited or patched copy, or a damaged download. 1>&2 & echo Use an unmodified USA retail dump. Nothing was changed. 1>&2 & call :UR-BALDOSA-HOLD & exit /b 2)',
        'if errorlevel 1 (echo UR-BALDOSA-STARTUP-PREFLIGHT: Windows PowerShell verification failed. 1>&2 & echo The built-in Windows PowerShell check could not run, so the ROM and save folder were not verified. Nothing was changed. 1>&2 & call :UR-BALDOSA-HOLD & exit /b 3)',
        'if not exist "%UR_RECOMP_USER_DATA_ROOT%\\" mkdir "%UR_RECOMP_USER_DATA_ROOT%" 2>nul',
        'if not exist "%UR_RECOMP_USER_DATA_ROOT%\\" (echo UR-BALDOSA-STARTUP-SAVE-ROOT: Could not create a writable user folder. 1>&2 & echo Windows would not let the game create its save folder. Pick a writable location with UR_RECOMP_USER_DATA_ROOT. 1>&2 & call :UR-BALDOSA-HOLD & exit /b 3)',
        'set "SNESRECOMP_USER_DATA_DIR=%UR_RECOMP_USER_DATA_ROOT%"',
        'set "UR_EXECUTION_MODE=modern"',
        'set "UR_BALDOSA_MODERN_ROOT=1"',
        'set "UR_BALDOSA_MODERN_INPUT=1"',
        'set "UR_BALDOSA_MODERN_PROFILE_SELECT=1"',
        'cd /d "%UR_RECOMP_USER_DATA_ROOT%"',
        'if errorlevel 1 (echo UR-BALDOSA-STARTUP-SAVE-ROOT: Cannot enter user folder. 1>&2 & echo The save folder exists but could not be opened. Check its permissions. 1>&2 & call :UR-BALDOSA-HOLD & exit /b 3)',
        # First-time controller-based profile creation completes only while
        # an anonymous game runs. Never rebind that live cartridge; relaunch
        # exactly ONCE after a clean exit if a new canonical selector appeared.
        # Scripted CLI invocations retain deterministic one-run semantics.
        'set "UR_BALDOSA_FIRST_RACER_RELAUNCH=0"',
        'if not exist "%UR_RECOMP_USER_DATA_ROOT%\\host-state-v1.txt" set "UR_BALDOSA_FIRST_RACER_RELAUNCH=1"',
        'if not "%~1"=="" set "UR_BALDOSA_FIRST_RACER_RELAUNCH=0"',
        ':UR-BALDOSA-NATIVE-START',
        f'"%UR_BALDOSA_PACKAGE_DIR%{EXE}" --no-launcher "%UR_BALDOSA_ROM%" %*',
        # The pinned native after_config exits 7 before any guest frame when
        # Modern selector/profile/SRAM authority is incomplete or mismatched.
        # Keep that exact status and all save data; never start a default
        # anonymous game or tell players to delete the affected profile.
        'if "%ERRORLEVEL%"=="7" goto UR-BALDOSA-RECOVERY-MENU',
        'if "%ERRORLEVEL%"=="8" goto UR-BALDOSA-SAVE-FAILURE',
        'if "%ERRORLEVEL%"=="9" goto UR-BALDOSA-SWITCH-FAILURE',
        # Preserve the independent release-auditor's existing exact
        # nonzero exit propagation marker; IF does not alter errorlevel.
        'if not "%ERRORLEVEL%"=="0" exit /b %ERRORLEVEL%',
        'if "%UR_BALDOSA_FIRST_RACER_RELAUNCH%"=="1" if exist "%UR_RECOMP_USER_DATA_ROOT%\\host-state-v1.txt" goto UR-BALDOSA-REBOOT-FIRST-RACER',
        'exit /b 0',
        ':UR-BALDOSA-REBOOT-FIRST-RACER',
        # The already-existing named-profile after_config must validate its
        # canonical typed/catalog/raw SRAM and will fail closed on exit 7.
        # No second profile selector, anonymous fallback or unbounded loop.
        'set "UR_BALDOSA_FIRST_RACER_RELAUNCH=0"',
        'echo UR-BALDOSA-FIRST-RACER: Restarting with newly created racer.',
        'goto UR-BALDOSA-NATIVE-START',
        # A double-clicked launcher closes its window the moment it exits, so
        # a refusal would vanish unread. Hold the console for up to a minute
        # (any key continues). `timeout` fails at once without a console, so
        # scripted/CI callers are never delayed; UR_BALDOSA_NO_HOLD forces it.
        # The existing launcher owns these explicit recovery choices. It
        # reruns the SAME original executable with one-shot environment
        # arguments; no fixture or competing save UI ships in the ZIP.
        ':UR-BALDOSA-RECOVERY-MENU',
        'if "%UR_BALDOSA_RECOVERY_ATTEMPTED%"=="1" (echo UR-BALDOSA-RECOVERY-RETRY-FAILED: Explicit recovery completed, but the new game still refused to start. Keep the archived snapshots. No second repair is offered. 1>&2 & call :UR-BALDOSA-HOLD & exit /b 7)',
        'echo UR-BALDOSA-STARTUP-PROFILE-REJECTED: Named racer rejected. Preserve both the raw save and Modern profile files. 1>&2',
        'echo Back up your entire save directory before considering recovery. 1>&2',
        'if not "%~1"=="" (call :UR-BALDOSA-HOLD & exit /b 7)',
        'if defined UR_BALDOSA_NO_HOLD exit /b 7',
        'echo R: Keep guest SRAM. May include newer progress; archive old typed data.',
        'echo T: Restore last committed SRAM. May lose recent progress; archive raw data.',
        'echo S: Switch to a verified healthy racer. Damaged racer remains untouched.',
        'echo Q: Exit without changing any saved data. Safest if uncertain.',
        'choice.exe /c RTSQ /n /m "Explicit recovery choice [R/T/S/Q]: "',
        'if errorlevel 4 exit /b 7',
        'if errorlevel 3 goto UR-BALDOSA-RECOVERY-HEALTHY',
        'if errorlevel 2 goto UR-BALDOSA-RECOVERY-TYPED',
        'if errorlevel 1 goto UR-BALDOSA-RECOVERY-RAW',
        'exit /b 7',
        ':UR-BALDOSA-RECOVERY-RAW',
        'set "UR_BALDOSA_RECOVERY_ACTION=raw"',
        'goto UR-BALDOSA-RECOVERY-EXECUTE',
        ':UR-BALDOSA-RECOVERY-TYPED',
        'set "UR_BALDOSA_RECOVERY_ACTION=typed"',
        'goto UR-BALDOSA-RECOVERY-EXECUTE',
        ':UR-BALDOSA-RECOVERY-HEALTHY',
        'set "UR_BALDOSA_RECOVERY_ACTION=healthy"',
        'echo Enter the registered PROFILE ID of the healthy alternate racer.',
        'echo First field in each canonical catalog row is the profile ID:',
        'if exist "%UR_RECOMP_USER_DATA_ROOT%\\profiles-v1.txt" type "%UR_RECOMP_USER_DATA_ROOT%\\profiles-v1.txt"',
        'echo Only the named target is validated; unrelated broken profiles are untouched.',
        'echo The damaged currently selected profile will not be modified.',
        'set /p "UR_BALDOSA_RECOVERY_PROFILE_ID=Healthy registered profile ID: "',
        'goto UR-BALDOSA-RECOVERY-EXECUTE',
        ':UR-BALDOSA-RECOVERY-EXECUTE',
        'echo Executing one explicit recovery choice before any guest frame.',
        f'"%UR_BALDOSA_PACKAGE_DIR%{EXE}" --no-launcher "%UR_BALDOSA_ROM%"',
        'if not "%ERRORLEVEL%"=="89" (echo UR-BALDOSA-RECOVERY-REFUSED: No automatic replacement was made. 1>&2 & call :UR-BALDOSA-HOLD & exit /b 7)',
        'set "UR_BALDOSA_RECOVERY_ACTION="',
        'set "UR_BALDOSA_RECOVERY_PROFILE_ID="',
        'set "UR_BALDOSA_FIRST_RACER_RELAUNCH=0"',
        'set "UR_BALDOSA_RECOVERY_ATTEMPTED=1"',
        'echo UR-BALDOSA-RECOVERY-COMMITTED: Relaunching with verified selected racer.',
        'goto UR-BALDOSA-NATIVE-START',
        # A guest session refused a save. Never classify exit 8 as a
        # clean shutdown or offer startup-only recovery before cold boot.
        ':UR-BALDOSA-SWITCH-FAILURE',
        'echo UR-BALDOSA-SWITCH-FAILED: The current racer was saved, but the requested next racer was not selected. 1>&2',
        'echo Your saved progress is intact. Another process may have changed the active racer or Windows refused the selector update. 1>&2',
        'echo Do not replace a healthy racer. Restart and make a fresh selection after checking your saved data. 1>&2',
        'if not "%~1"=="" exit /b 9',
        'call :UR-BALDOSA-HOLD',
        'exit /b 9',
        ':UR-BALDOSA-SAVE-FAILURE',
        'echo UR-BALDOSA-SAVE-FAILED: This game session could not finish saving. 1>&2',
        'echo Some recent progress may not have been committed. Preserve your entire user-data folder. 1>&2',
        'echo Do not delete a racer or overwrite its save. Relaunch to inspect recovery, or preserve a backup. 1>&2',
        'if not "%~1"=="" exit /b 8',
        'call :UR-BALDOSA-HOLD',
        'exit /b 8',
        ':UR-BALDOSA-HOLD',
        'if defined UR_BALDOSA_NO_HOLD exit /b 0',
        'echo. 1>&2',
        'echo Press any key to close this window, or wait. 1>&2',
        'timeout /t 60 >nul 2>nul',
        'exit /b 0',
    ]
    return ("\r\n".join(commands) + "\r\n").encode("utf-8")


def readme(revision: str) -> bytes:
    return (
        "UR-Recomp / Baldosa native Windows x64 candidate\n"
        "================================================\n\n"
        "This is a development candidate, NOT a completed remaster.\n"
        "The existing Modern root can enter original 1P/2P selection and\n"
        "provides native profile SRAM persistence where authorized.\n"
        "Quick Practice enters the original courses your racer has unlocked\n"
        "(20 on a new save; secret Hunter stays closed), each verified by\n"
        "the original game's own course identity, using a disposable guest\n"
        "SRAM save root. Normal exit preserves the named racer.\n"
        "Practice cannot publish career Records or runs.\n"
        "Options changes Display, VSync and Volume and shows the menu\n"
        "controls; settings persist in options-v1.txt. Other settings are\n"
        "not offered because this build does not apply them.\n"
        "Records shows the verified named racer's historical runs read-only.\n"
        "A scripted-input native Windows 1P Race has completed, persisted\n"
        "its source-confirmed named run, and reopened it in a fresh game.\n"
        "That does not prove original-emulator parity or physical gamepads.\n"
        "A real native Windows 2P Race also published a paired match and\n"
        "reopened both match files in fresh-game Records, with scripted pad\n"
        "semantics. Physical controllers and strict original/native event\n"
        "parity remain unverified. Ghost/replay equivalence,\n"
        "integrated HD/widescreen, complete frontend and 45-event fidelity\n"
        "remain outstanding. This package is NOT a release or a beta approval.\n\n"
        "HOW TO LAUNCH\n"
        "1. Extract the ZIP to a normal Windows folder.\n"
        "2. Copy your own legally obtained USA retail Uniracers ROM dump as\n"
        f"   {ROM} next to {EXE}.\n"
        f"   Required SHA-256: {USA_SHA256}\n"
        f"3. Double-click {LAUNCHER}.\n\n"
        "FIRST-TIME RACER SETUP (MODERN ONLY)\n"
        "From the native home screen press X (gamepad X or keyboard X).\n"
        "Use UP/DOWN to choose one of the original 16 stock racers.\n"
        "Press A/ENTER to create an isolated named racer and clean save.\n"
        "Press B/ESC to close the picker, then B/ESC and A/ENTER to Quit.\n"
        "The double-click launcher automatically restarts the game ONCE\n"
        "after a clean first-time creation, to load the chosen racer.\n"
        "If started directly without the launcher, quit and relaunch.\n"
        "Never change the active cartridge's identity while it is running.\n\n"
        "The ROM and all profile/save data are ABSENT from this archive.\n"
        "The launcher refuses a wrong ROM, validates the root, and uses\n"
        "%APPDATA%\\gamesbyian\\UR-Recomp for user state, or the optional\n"
        "absolute UR_RECOMP_USER_DATA_ROOT override. It refuses data paths\n"
        "inside the extracted package or through an existing Windows\n"
        "junction/reparse-point path. Saved data is NEVER shipped in a ZIP.\n"
        "An existing named Modern profile needs a complete valid catalog,\n"
        "host-profile state and 8192-byte native save; otherwise startup\n"
        "refuses the profile instead of writing into another slot.\n"
        "INTERRUPTED FIRST-CREATE RECOVERY\n"
        "If first-racer setup stopped AFTER one valid catalog entry and its\n"
        "typed and raw SRAM were saved but BEFORE the active selection,\n"
        "launch the native root again and explicitly choose the SAME preset.\n"
        "Only an exact matching single profile/catalog/8192-byte SRAM\n"
        "allows safe completion of the previously missing selector.\n"
        "Do not remove the save directory or choose another racer to fix it.\n"
        "CRASHED NAMED RACER RECOVERY (WINDOWS DOUBLE-CLICK LAUNCHER)\n"
        "If an authorized named racer cannot boot, the launcher offers\n"
        "an explicit R/T/S/Q recovery choice. Copy the complete user-data\n"
        "directory first. Q does not modify anything. No choice is automatic.\n"
        "R keeps a complete guest-authored SRAM and archives prior metadata.\n"
        "T restores the last committed typed SRAM after archiving raw bytes\n"
        "and an exact pending intent where present. Both choices preserve\n"
        "forensic old/new evidence and require valid existing authority.\n"
        "S displays the canonical roster and lets you enter a registered\n"
        "healthy profile ID, changing only the next-boot selector while\n"
        "preserving damaged and unrelated racers, including 3+ catalogs.\n"
        "Malformed/missing typed sidecars are never silently re-created.\n"
        "Recovery uses a fresh invocation of the original native game exe.\n"
        "A refused or incomplete session save exits with code 8 and warns\n"
        "in the launcher; keep the entire user-data folder, even when\n"
        "the old raw save and typed profile still look intact. Exit 8\n"
        "never silently starts recovery or reports a successful save.\n"
        "A separate code 9 means the current racer WAS saved but the\n"
        "requested next-racer selector change was refused. It is not\n"
        "a lost-save warning; reselect after a fresh start.\n"
        "After a successful R/T/S repair the launcher retries the original\n"
        "game only once. A further refusal exits 7 without a second prompt;\n"
        "the preserved backup and original data are never auto-deleted.\n"
        "Automated or command-line launcher runs retain fail-closed exit 7.\n\n"
        "If startup reports PROFILE-REJECTED or SAVE-MISMATCH, preserve\n"
        "both save.srm and host-profile.txt plus the roster and selector.\n"
        "General recovery of a corrupt or missing typed sidecar remains\n"
        "unsupported. Never delete or overwrite a save to bypass checks.\n\n"
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
            # Python defaults to creator OS=0 on Windows, 3 on Unix.
            # Pin the existing Windows value so identical immutable inputs
            # reproduce the same ZIP SHA across native Windows and Linux.
            info.create_system = 0
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
