#!/usr/bin/env python3
"""One bounded real Windows 1P source PPU capture from an immutable binary.

No recompilation, new renderer or gameplay/Modern changes. The existing
QA-08 title observer is ALREADY linked in the independently pinned PR #1641
Windows executable. Capture authentic callbacks only; missing raster is an
incomplete observation, not a nearest-frame replacement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

from baldosa_windows_native_pause_route import run_route

EXE_SHA = "7431889698913feadab76261caf3b00b82d1d9a1466a8260d9b7512d8328324e"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
FRAMES = (1856,2192,2208,2224)
HEADER = (b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
          b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
LOG = re.compile(r"^UR_QA08_WINDOWS_ORIGINAL_SOURCE frame=(\d+) "
                 r"logical=256x224 saved=1 "
                 r"source=post-original-ppu-before-present$", re.M)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify_capture(folder: Path, log: str, crcs: list[str]) -> dict:
    if len(crcs) < 2224 or len(crcs) > 20000:
        raise ValueError("real native 1P guest did not complete the bounded source route")
    if any(not re.fullmatch(r"0x[0-9a-fA-F]{8}", x) for x in crcs):
        raise ValueError("native 1P guest CRC transcript malformed")
    seen = [int(x) for x in LOG.findall(log)]
    if 2208 not in seen or len(seen) != len(set(seen)) or any(f not in FRAMES for f in seen):
        raise ValueError("actual 1P guest2208 post-PPU callback absent or duplicated")
    if "UR_QA08_WINDOWS_SOURCE_REJECT" in log:
        raise ValueError("original source observer rejected/duplicated 1P sample")
    files = sorted(folder.glob("ur-baldosa-original-source-*.pam"))
    present = {}
    for file in files:
        m = re.fullmatch(r"ur-baldosa-original-source-(\d{6})\.pam", file.name)
        if not m or int(m[1]) not in FRAMES:
            raise ValueError("extraneous guessed framebuffer in 1P source dir")
        frame = int(m[1])
        raw = file.read_bytes()
        if not raw.startswith(HEADER) or len(raw) != len(HEADER)+256*224*4:
            raise ValueError("PPU source not complete native 256x224 RGBA")
        present[frame] = sha(raw)
    if set(present) != set(seen):
        raise ValueError("emitted frame files do not correspond to actual raster callbacks")
    return {
        "schema": "qa08-windows-real-1p-original-source-observer/1",
        "source_geometry": [256,224],
        "actual_guest_frames_simulated": len(crcs),
        "guest_CRC_lowercase_sha256": sha(
            ("\n".join(s.lower() for s in crcs)+"\n").encode("ascii")),
        "actual_observed_source_guest_frames": sorted(present),
        "unmodified_source_P7_sha256_by_guest_frame": present,
        "guest2208_captured_in_source": True,
        "proves_original_Snes9x_native_pixel_equivalence": False,
        "candidate_binary_changes_guest_or_host_business": False,
        "release_gate_approved": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ("exe","rom","script","out"):
        ap.add_argument("--"+key,required=True,type=Path)
    ap.add_argument("--timeout",type=int,default=240)
    args=ap.parse_args()
    if sha(args.exe.read_bytes()) != EXE_SHA:
        ap.error("not immutable original-PPU-observer Windows executable")
    if sha(args.rom.read_bytes()) != ROM_SHA:
        ap.error("not authentic Uniracers USA source ROM")
    if args.out.exists():
        ap.error("output root exists; refuse to mix separate attempts")
    args.out.mkdir(parents=True)
    source=args.out/"source"
    source.mkdir()
    before=os.environ.get("UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR")
    os.environ["UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR"]=str(source.resolve())
    try:
        crcs,log=run_route(args.exe.resolve(),args.rom.resolve(),
                           args.script.resolve(),args.out,
                           pause=False,video="windows",timeout=args.timeout)
    finally:
        if before is None:
            os.environ.pop("UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR",None)
        else:
            os.environ["UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR"]=before
    result=verify_capture(source,log,crcs)
    result.update({
        "actual_windows_binary_sha256":EXE_SHA,
        "native_input_script_sha256":sha(args.script.read_bytes()),
        "original_USA_ROM_sha256":ROM_SHA,
    })
    (args.out/"qa08-windows-1p-source.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA08_WIN_1P_REAL_SOURCE_CAPTURE frame2208=observed "
          "source256x224=unmodified original_pixel_parity=UNADJUDICATED")


if __name__=="__main__":
    main()
