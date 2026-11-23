#!/usr/bin/env python3
"""C04: actual Win32 exit-86 after target SRAM, followed by cold selection.
Evidence is intentionally not a release gate. No source ROM is retained.
"""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from assemble_baldosa_windows_candidate import ROM, USA_SHA256
from baldosa_win32_interactive_recovery_q import digest
from baldosa_win32_interactive_recovery_rt import forced_stop_tree, launch_until_first_frame
from baldosa_win32_interactive_recovery_s import A, B, canonical, keep
from baldosa_win32_interactive_recovery_s_reject import spawn, wait_for, inject

def wait_for_game_window(deadline: float) -> int:
    """Find the hosted game's real visible Win32 SDL window."""
    user32 = ctypes.windll.user32
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    while time.monotonic() < deadline:
        windows = []
        def inspect(hwnd, unused):
            if not user32.IsWindowVisible(hwnd):
                return True
            size = user32.GetWindowTextLengthW(hwnd)
            if size:
                title = ctypes.create_unicode_buffer(size + 1)
                user32.GetWindowTextW(hwnd, title, size + 1)
                if "uniracer" in title.value.lower() or "unirally" in title.value.lower():
                    windows.append(hwnd)
            return True
        user32.EnumWindows(callback(inspect), 0)
        if len(windows) == 1:
            return windows[0]
        if len(windows) > 1:
            raise ValueError("Ambiguous game windows; refusing unbound keyboard input")
        time.sleep(0.05)
    raise TimeoutError("No visible original Win32 SDL game window")


def send_game_key(hwnd: int, vk: int):
    """Inject hardware-style keyboard events into the foreground SDL window.

    PostMessage(WM_KEYDOWN) does not update Windows keyboard state, so SDL's
    Windows backend can discard it. Require foreground ownership and use
    SendInput instead of silently assuming a queued window message was read.
    """
    user32 = ctypes.windll.user32
    if not user32.IsWindow(hwnd):
        raise ValueError("Original game window disappeared before input")
    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    deadline = time.monotonic() + 3
    while user32.GetForegroundWindow() != hwnd and time.monotonic() < deadline:
        time.sleep(0.05)
    if user32.GetForegroundWindow() != hwnd:
        raise RuntimeError("SDL game window did not acquire keyboard foreground")

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_size_t)]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                    ("wParamH", wintypes.WORD)]

    class INPUTUNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", INPUTUNION)]

    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    for flags in (0, 0x0002):  # down, KEYEVENTF_KEYUP
        event = INPUT()
        event.type = 1  # INPUT_KEYBOARD
        event.u.ki = KEYBDINPUT(vk, 0, flags, 0, 0)
        if user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT)) != 1:
            raise ctypes.WinError()
        time.sleep(0.12)


def run(launcher: Path, fixture: Path, seed: Path, out: Path, timeout: int):
    out.mkdir()
    user = out / "Two Original Racer Roots With Spaces"
    user.mkdir()
    for extra in ([], ["--add-second-keep-first"]):
        subprocess.run([str(fixture), str(user), str(seed), *extra],
                       check=True, capture_output=True, timeout=timeout)
    # Healthy startup is essential: CMD emergency S bypasses the in-game
    # activate_profile_id() fault boundary and cannot witness exit 86.
    before = canonical_two(user)
    if before["a-raw"] == before["b-raw"]:
        raise ValueError("Racer roots are not independent")
    receipts = {}
    evidence = out / "source-bytes"
    keep(evidence, "before-crash", before, receipts)
    proc, transcript = spawn(launcher, user, out, "c04-crash")
    try:
        deadline = time.monotonic() + timeout
        wait_for(proc, transcript, "first frame simulated", deadline)
        hwnd = wait_for_game_window(deadline)
        # Real Win32 keyboard messages enter SDL's event pump, then the Modern
        # F2 chooser. Never call the product's acceptance/test-key shortcut.
        send_game_key(hwnd, 0x71)  # VK_F2
        # An SDL frame is not evidence that F2 was eligible. Require the
        # actual native product's chooser-open discriminator before selection.
        wait_for(proc, transcript, "UR_PROFILE_UI OPENED", min(deadline, time.monotonic() + 12))
        send_game_key(hwnd, 0x28)  # VK_DOWN: A -> B
        time.sleep(0.25)
        send_game_key(hwnd, 0x0D)  # VK_RETURN: activate_profile_id(B)
        proc.wait(timeout=max(1, deadline - time.monotonic()))
        log = transcript.read_text(encoding="utf-8", errors="replace")
        if proc.returncode != 86 or "UR_C04_FAULT POST_TARGET_SRAM_PRE_SELECTOR" not in log:
            raise ValueError(f"Fault not reached: exit={proc.returncode}, tail={log[-1500:]}")
    finally:
        forced_stop_tree(proc)
    after = canonical_two(user)
    keep(evidence, "after-exit86", after, receipts)
    if after["selector"] != before["selector"] or after["catalog"] != before["catalog"]:
        raise ValueError("Crash published selector or changed roster prematurely")
    if after["a-raw"] != before["a-raw"] or after["a-typed"] != before["a-typed"]:
        raise ValueError("Crash mutated original racer A")
    if after["b-typed"] != before["b-typed"] or after["b-raw"] != before["b-raw"]:
        raise ValueError("Crash mutated healthy target B raw SRAM or typed metadata")
    # After the crash, A remains healthy; cold boot must retain its selector.
    # Disable the fault hook in the parent before spawning this new process.
    os.environ.pop("UR_C04_TEST_KILL_AFTER_TARGET_SRAM", None)
    log, injected = launch_until_first_frame(
        launcher, user, out, "cold-select-A", key=None, timeout=timeout)
    if injected or "first frame simulated" not in log:
        raise ValueError("Cold process failed to retain original A")
    recovered = canonical_two(user)
    keep(evidence, "after-cold-select", recovered, receipts)
    if recovered != after:
        raise ValueError("Cold boot mutated the interrupted selector or racer data")
    # A second independent process must boot the selected B without a recovery
    # prompt or any silent rewrite of the canonical racer authorities.
    log2, injected2 = launch_until_first_frame(
        launcher, user, out, "cold-reentry-A", key=None, timeout=timeout)
    if injected2 or "first frame simulated" not in log2:
        raise ValueError("Second cold A boot did not reach an original game frame")
    reentered = canonical_two(user)
    keep(evidence, "after-second-cold-boot", reentered, receipts)
    if reentered != recovered:
        raise ValueError("Second cold A boot rewrote selector, roster or racer data")
    result = dict(schema="ur-c04-win32-real-exit86/1", actual_exit=86,
                  cold_A_preserved=True, second_cold_boot=True,
                  competing_writer_tested=False,
                  sha256_receipts=receipts, release_gate_credit=0)
    (out / "c04-result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    return result

def canonical_two(root: Path):
    paths = {"selector": root/"host-state-v1.txt", "catalog": root/"profiles-v1.txt"}
    for tag, racer in (("a", A), ("b", B)):
        base = root/("saves/profile-"+racer)
        paths[tag+"-raw"] = base/"save.srm"
        paths[tag+"-typed"] = base/"host-profile.txt"
    result = {}
    for tag, path in paths.items():
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing canonical "+tag)
        data = path.read_bytes()
        if tag.endswith("-raw") and len(data) != 8192:
            raise ValueError("Wrong SRAM size "+tag)
        result[tag] = data
    return result

def main():
    p=argparse.ArgumentParser()
    for name in ("launcher","rom","fixture","seed","out"):
        p.add_argument("--"+name,required=True,type=Path)
    p.add_argument("--timeout",type=int,default=120)
    a=p.parse_args()
    if os.name!="nt" or a.out.exists() or digest(a.rom.read_bytes())!=USA_SHA256:
        raise ValueError("Fresh Windows root and authentic USA ROM required")
    installed=a.launcher.parent/ROM
    if installed.exists(): raise ValueError("ROM-free launcher already contains ROM")
    shutil.copyfile(a.rom,installed)
    try:
        os.environ["UR_C04_TEST_KILL_AFTER_TARGET_SRAM"]="C04_POST_SRAM_PRE_SELECTOR_V1"
        print(json.dumps(run(a.launcher,a.fixture,a.seed,a.out,a.timeout),sort_keys=True))
    finally:
        os.environ.pop("UR_C04_TEST_KILL_AFTER_TARGET_SRAM",None)
        installed.unlink(missing_ok=True)

if __name__=="__main__":
    main()
