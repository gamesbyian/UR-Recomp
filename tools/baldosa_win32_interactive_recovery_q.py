#!/usr/bin/env python3
"""Original extracted Win32 CMD interactive recovery Q, with genuine console key.

No hook into the shipping launcher, no synthetic choice environment variable
and no modification to the ten-file CMD / nineteen-file QA02 evidence archives.
The only synthetic input is the user's Q key, dispatched as Win32 console
KEY_EVENT records to the isolated original cmd.exe's console.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import time

from assemble_baldosa_windows_candidate import ROM, USA_SHA256

KEY_EVENT = 0x0001
STDIN_READ_WRITE = 0xC0000000
SHARE_READ_WRITE = 3
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80


class ConsoleKey(ctypes.Structure):
    _fields_ = [
        ("bKeyDown", wintypes.BOOL),
        ("wRepeatCount", wintypes.WORD),
        ("wVirtualKeyCode", wintypes.WORD),
        ("wVirtualScanCode", wintypes.WORD),
        ("UnicodeChar", wintypes.WCHAR),
        ("dwControlKeyState", wintypes.DWORD),
    ]


class ConsoleRecordUnion(ctypes.Union):
    _fields_ = [("KeyEvent", ConsoleKey),
                ("padding", ctypes.c_byte * ctypes.sizeof(ConsoleKey))]


class ConsoleInputRecord(ctypes.Structure):
    _fields_ = [("EventType", wintypes.WORD),
                ("Event", ConsoleRecordUnion)]


def inject_console_q(pid: int) -> None:
    """Separate injector subprocess, so the verifier never loses its console."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.AttachConsole.argtypes = (wintypes.DWORD,)
    kernel.AttachConsole.restype = wintypes.BOOL
    kernel.FreeConsole.restype = wintypes.BOOL
    kernel.CreateFileW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.WriteConsoleInputW.argtypes = (
        ctypes.c_void_p, ctypes.POINTER(ConsoleInputRecord), wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD))
    kernel.WriteConsoleInputW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel.CloseHandle.restype = wintypes.BOOL
    # The dedicated injector can inherit the hosted runner's console even
    # though its stdout/stderr are redirected. AttachConsole then fails with
    # WinError 5 (ERROR_ACCESS_DENIED) because one process may be attached
    # to only one console at a time. Detach ONLY this one-shot injector,
    # never the parent verifier or the game. FreeConsole is harmless if the
    # injector has no console; failed attachment still remains fail-closed.
    kernel.FreeConsole()
    if not kernel.AttachConsole(pid):
        raise ctypes.WinError(ctypes.get_last_error())
    handle = None
    try:
        handle = kernel.CreateFileW(
            "CONIN$", STDIN_READ_WRITE, SHARE_READ_WRITE, None,
            OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None)
        if handle in (None, ctypes.c_void_p(-1).value):
            raise ctypes.WinError(ctypes.get_last_error())
        records = (ConsoleInputRecord * 2)()
        for i, down in enumerate((True, False)):
            records[i].EventType = KEY_EVENT
            records[i].Event.KeyEvent = ConsoleKey(
                int(down), 1, 0x51, 0x10, "Q", 0)
        written = wintypes.DWORD(0)
        if not kernel.WriteConsoleInputW(
                handle, records, 2, ctypes.byref(written)) or written.value != 2:
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        if handle not in (None, ctypes.c_void_p(-1).value):
            kernel.CloseHandle(handle)
        kernel.FreeConsole()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot(root: Path) -> dict[str, bytes]:
    expected = {
        "selector": root / "host-state-v1.txt",
        "catalog": root / "profiles-v1.txt",
        "typed": root / "saves/profile-native-ci-rider/host-profile.txt",
        "raw": root / "saves/profile-native-ci-rider/save.srm",
    }
    result = {}
    for name, path in expected.items():
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing or redirected original canonical file " + name)
        result[name] = path.read_bytes()
    if len(result["raw"]) != 8192:
        raise ValueError("Original save is not 8192 bytes")
    return result


def run(launcher: Path, fixture: Path, seed: Path, root: Path,
        *, timeout: int = 100) -> dict:
    if os.name != "nt":
        raise ValueError("Only actual Windows console accepts this key witness")
    if root.exists():
        raise ValueError("Do not reuse or delete a previously tested root")
    if not launcher.is_file() or not (launcher.parent / ROM).is_file():
        raise ValueError("Use the exact extracted CMD with a verified original ROM")
    if not fixture.is_file() or not seed.is_file():
        raise ValueError("Source fixture and original SRAM seed are required")
    root.mkdir(parents=True)
    user = root / "Original Player With Spaces"
    user.mkdir()
    init = subprocess.run(
        [str(fixture), str(user), str(seed)],
        capture_output=True, text=True, timeout=timeout, check=True)
    (root / "original-fixture.log").write_text(
        init.stdout + "\n" + init.stderr, encoding="utf-8")
    original = snapshot(user)
    # A legacy mismatch without a pending intent is not recoverable without
    # explicit user choice. Keep its original stock signature intact.
    raw = user / "saves/profile-native-ci-rider/save.srm"
    damaged = bytearray(original["raw"])
    damaged[256] ^= 1
    raw.write_bytes(damaged)
    pre = snapshot(user)
    if pre["raw"] == original["raw"] or any(
            pre[x] != original[x] for x in ("selector", "catalog", "typed")):
        raise ValueError("Test failed to create a precise raw-vs-typed mismatch")
    if list(user.rglob("native-sram-checkpoint.pending")):
        raise ValueError("Legacy mismatch must have no trusted pending intent")

    # Separate, product-only byte witness for INDEPENDENT rehash.
    # These are CI fixture-owned original-format bytes, never a person's
    # real profile and never added to strict QA02 or launcher artifacts.
    byte_root = root / "source-bytes"
    byte_root.mkdir()
    receipts = {}
    def retain_stage(stage: str, states: dict[str, bytes]) -> None:
        if set(states) != {"selector", "catalog", "typed", "raw"}:
            raise ValueError("Missing canonical source stage member")
        for name, content in sorted(states.items()):
            member = f"{stage}.{name}.bin"
            (byte_root / member).write_bytes(content)
            receipts[member] = {"sha256": digest(content), "bytes": len(content)}

    retain_stage("before-Q", pre)

    transcript = root / "interactive-console.log"
    # The CREATE_NEW_CONSOLE process must receive its genuine console stdin.
    # CMD file redirection of CONIN$ failed with Win32 access denied under
    # the hosted runner, before choice.exe could accept Q. Preserve STDIN
    # unredirected; redirect *only* output in the wrapper. Passing DEVNULL
    # handles through Popen forces STARTF_USESTDHANDLES, overriding fresh
    # console standard handles even with CREATE_NEW_CONSOLE. The shipping
    # source launcher and candidate bytes are completely unchanged.
    wrapper = root / "run-original-console.cmd"
    wrapper.write_text(
        '@echo off\n'
        f'call "{launcher}" >"{transcript}" 2>&1\n'
        'exit /b %ERRORLEVEL%\n', encoding="utf-8")
    env = os.environ.copy()
    env.pop("UR_BALDOSA_NO_HOLD", None)
    env.pop("UR_BALDOSA_RECOVERY_ACTION", None)
    env.pop("UR_BALDOSA_RECOVERY_PROFILE_ID", None)
    env.update({
        "UR_RECOMP_USER_DATA_ROOT": str(user),
        "SDL_AUDIODRIVER": "dummy",
        "SDL_VIDEODRIVER": "windows",
    })
    proc = subprocess.Popen(
        ["cmd.exe", "/d", "/c", "call", str(wrapper)],
        cwd=launcher.parent, env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE)
    try:
        prompt = "Explicit recovery choice [R/T/S/Q]:"
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            text = transcript.read_text(encoding="utf-8", errors="replace") \
                if transcript.is_file() else ""
            if prompt in text:
                break
            if proc.poll() is not None:
                raise ValueError("Actual CMD exited without interactive choice: " +
                                 text[-1500:])
            time.sleep(0.025)
        else:
            raise TimeoutError("Original choice.exe prompt not visible")

        # The independent helper owns only the isolated console; even CI's
        # own console state is never detached or redirected.
        injector = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()),
             "--inject-console-q", str(proc.pid)],
            cwd=root, capture_output=True, text=True, timeout=20)
        (root / "key-injection.log").write_text(
            f"exit={injector.returncode}\n" +
            injector.stdout + "\n" + injector.stderr, encoding="utf-8")
        if injector.returncode != 0:
            raise ValueError("Real Win32 console Q key injection refused")
        proc.wait(timeout=timeout)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=30)
    text = transcript.read_text(encoding="utf-8", errors="replace")
    if (proc.returncode != 7 or
        text.count("UR-BALDOSA-STARTUP-PROFILE-REJECTED:") != 1 or
        text.count("Explicit recovery choice [R/T/S/Q]:") != 1 or
        "Q: Exit without changing any saved data." not in text or
        "UR-BALDOSA-RECOVERY-COMMITTED:" in text or
        "UR-BALDOSA-RECOVERY-REFUSED:" in text or
        "UR-BALDOSA-FIRST-RACER:" in text):
        raise ValueError("Q did not refuse a real original recovery menu")
    post = snapshot(user)
    retain_stage("after-Q", post)
    if post != pre or list(user.rglob("native-sram-manual-archive-*.bin")) or \
       list(user.rglob("native-sram-recovered-intent-*.bin")) or \
       list(user.rglob("native-sram-checkpoint.pending")):
        raise ValueError("Q changed canonical data or invented recovery receipts")
    result = {
        "schema": "ur-win32-interactive-original-cmd-q/1",
        "genuine_win32_console_key_event": "Q",
        "child_process_exit_code": proc.returncode,
        "exact_extracted_cmd_sha256": digest(launcher.read_bytes()),
        "native_profile_fixture_sha256": digest(fixture.read_bytes()),
        "initial_original_seed_sha256": digest(seed.read_bytes()),
        "legacy_raw_signature_preserved": pre["raw"][:16] == original["raw"][:16],
        "original_persisted_bytes_equal_after_Q": True,
        "typed_raw_selector_catalog_sha256": {
            k: digest(value) for k, value in sorted(post.items())},
        "eight_original_before_after_binary_members": len(receipts) == 8,
        "source_bytes_sha256": receipts,
        "manual_repair_archive_created": False,
        "second_guest_or_default_fallback": False,
        "independent_qa_release_credit": 0,
    }
    (root / "interactive-q-result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result



def run_with_personal_rom(launcher: Path, verified_rom: Path, fixture: Path,
                          seed: Path, root: Path, *, timeout: int = 100) -> dict:
    """Reuse the real extracted package while leaving no ROM inside it.

    The preceding release acceptance intentionally REMOVES its temporary
    retail ROM before returning. Copy this separately verified USA original
    for the one Q attempt, then remove it on every exit, including failure.
    Never write ROM data, names or bytes into any uploaded artifact.
    """
    if (not launcher.is_file() or not verified_rom.is_file() or
        verified_rom.is_symlink() or
        digest(verified_rom.read_bytes()) != USA_SHA256):
        raise ValueError("Must supply verified personal original USA ROM")
    installed = launcher.parent / ROM
    if installed.exists() or installed.is_symlink():
        raise ValueError("Extracted ROM-free candidate unexpectedly retained ROM")
    try:
        shutil.copyfile(verified_rom, installed)
        if digest(installed.read_bytes()) != USA_SHA256:
            raise ValueError("Temporary installed USA ROM bytes changed")
        result = run(launcher, fixture, seed, root, timeout=timeout)
        result["verified_original_USA_ROM_sha256"] = USA_SHA256
        (root / "interactive-q-result.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        return result
    finally:
        installed.unlink(missing_ok=True)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inject-console-q", type=int)
    ap.add_argument("--launcher", type=Path)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--fixture", type=Path)
    ap.add_argument("--seed", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--timeout", type=int, default=100)
    a = ap.parse_args()
    if a.inject_console_q is not None:
        inject_console_q(a.inject_console_q)
    else:
        if not all((a.launcher, a.rom, a.fixture, a.seed, a.out)):
            ap.error("launcher, ROM, fixture, seed and output required")
        print(json.dumps(run_with_personal_rom(
            a.launcher.resolve(), a.rom.resolve(),
            a.fixture.resolve(), a.seed.resolve(), a.out.resolve(),
            timeout=a.timeout), sort_keys=True))


if __name__ == "__main__":
    main()
