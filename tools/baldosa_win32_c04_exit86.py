#!/usr/bin/env python3
"""C04: actual Win32 exit-86 after target SRAM, followed by cold selection.
Evidence is intentionally not a release gate. No source ROM is retained.
"""
from __future__ import annotations
import argparse
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

def run(launcher: Path, fixture: Path, seed: Path, out: Path, timeout: int):
    out.mkdir()
    user = out / "Two Original Racer Roots With Spaces"
    user.mkdir()
    for extra in ([], ["--add-second-keep-first"]):
        subprocess.run([str(fixture), str(user), str(seed), *extra],
                       check=True, capture_output=True, timeout=timeout)
    # The actual CMD recovery S route requires an invalid currently selected
    # racer; corrupt only A's raw while retaining its independently valid typed.
    a = user / ("saves/profile-" + A) / "save.srm"
    raw = bytearray(a.read_bytes())
    raw[0x0711] ^= 0x35
    a.write_bytes(raw)
    before = canonical_two(user)
    if before["a-raw"] == before["b-raw"]:
        raise ValueError("Racer roots are not independent")
    receipts = {}
    evidence = out / "source-bytes"
    keep(evidence, "before-crash", before, receipts)
    proc, transcript = spawn(launcher, user, out, "c04-crash")
    # Only the crashing child inherits the exact opt-in token. The wrapper
    # must set it BEFORE launching the native executable.
    # spawn() inherits this process environment.
    try:
        deadline = time.monotonic() + timeout
        wait_for(proc, transcript, "Explicit recovery choice [R/T/S/Q]:", deadline)
        inject(proc.pid, out, "c04-S", ["--inject-console-key", "S", str(proc.pid)])
        wait_for(proc, transcript, "Healthy registered profile ID:", deadline)
        inject(proc.pid, out, "c04-target", ["--inject-console-text", str(proc.pid), B])
        proc.wait(timeout=timeout)
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
    # Cold S must recover the still-invalid A selector by explicitly choosing B.
    # Disable the fault hook in the parent before spawning this new process.
    os.environ.pop("UR_C04_TEST_KILL_AFTER_TARGET_SRAM", None)
    log, injected = launch_until_first_frame(
        launcher, user, out, "cold-select-B", key="S", profile_id=B, timeout=timeout)
    if not injected or "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=" + B not in log:
        raise ValueError("Cold process failed to select healthy B")
    recovered = canonical_two(user)
    keep(evidence, "after-cold-select", recovered, receipts)
    if any(recovered[k] != after[k] for k in after if k != "selector"):
        raise ValueError("Cold recovery lost or modified racer data")
    if recovered["selector"] == after["selector"]:
        raise ValueError("Cold recovery did not publish B selector")
    result = dict(schema="ur-c04-win32-real-exit86/1", actual_exit=86,
                  cold_B_selected=True, competing_writer_tested=False,
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
