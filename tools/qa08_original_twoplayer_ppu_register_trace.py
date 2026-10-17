#!/usr/bin/env python3
"""Read-only Snes9x PPU write-log probes at deterministic stock 2P boundaries.

Create an action-script variant containing ONLY three zero-frame dump actions.
The original controller masks, commands, counts, waits, and guest bytes are
unchanged. One pinned original Snes9x process can thus expose true original
INIDISP brightness, CGRAM palette, CGADSUB and HDMA writes at the finish
fade and results transition, without speculative native timing modification.

Every sampled raster must be byte-identical to the independently executed
263-callback original 2P source before any register witness is accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ORIGINAL_ROUTE_LF_SHA="220ff1d5ce032311fc85b2199880d342a7c60ea8aa7759e3afcb5d3894c3b735"
ORIGINAL_UNTURBO_SHA="a6c8815482b742d90dca61645f876c15918f5d9985a027eef107ac4fdc515264"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SCHEMA="qa08-source-qualified-snes9x-readonly-2p-ppu-journal/1"
DUMPS={
  "qa08_before_finish":"press right+p2:right 800\npress right+up+p2:right+p2:down 60\n",
  "qa08_finish_fade":"press right+up+p2:right+p2:down 60\npress right+p2:right 1500\n",
  "qa08_results_cgram":"press right+p2:right 1500\nuntil16 0053 == F60C\n",
}
DUMP_FRAMES={"qa08_before_finish":3622,"qa08_finish_fade":3683,"qa08_results_cgram":5184}
FIRST,LAST,STEP=1279,5471,16


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def build_script(raw:bytes)->bytes:
    if sha(raw)!=ORIGINAL_ROUTE_LF_SHA:
        raise ValueError("original two-pad controller script changed")
    if raw.count(b"turbo on\n")!=1:
        raise ValueError("unexpected original script turbo directive")
    text=raw.replace(b"turbo on\n",b"",1).decode("ascii")
    if sha(text.encode("ascii"))!=ORIGINAL_UNTURBO_SHA:
        raise ValueError("original reference controller stream differs")
    for tag,anchor in DUMPS.items():
        if text.count(anchor)!=1:
            raise ValueError("source action boundary not unique")
        first,second=anchor.split("\n",1)
        assert second.endswith("\n")
        expanded=first+"\n"+"dump "+tag+"\n"+second
        text=text.replace(anchor,expanded,1)
    # Destructively remove ONLY the new zero-frame dump actions and prove
    # exact byte-identical original source controller stream.
    reconstructed=text
    for tag in DUMPS:
        reconstructed=reconstructed.replace("dump "+tag+"\n","")
    if sha(reconstructed.encode("ascii"))!=ORIGINAL_UNTURBO_SHA:
        raise ValueError("source-instrumented script mutates gameplay commands")
    return text.encode("ascii")


def verify(root:Path,prior:Path,route:Path,rom:Path,core:Path)->dict:
    if sha(rom.read_bytes())!=ROM_SHA:
        raise ValueError("original source ROM changed")
    actual=build_script(route.read_bytes())
    diagnostic=(root/"qa08-ppu-observer.script").read_bytes()
    if actual!=diagnostic:
        raise ValueError("actual source trace script differs from built action stream")
    prior_manifest=json.loads((prior/"qa08-original-2p-fullroute.json").read_text())
    if (prior_manifest.get("actual_script_quit_frame")!=5484
        or prior_manifest.get("actual_callbacks_captured")!=263):
        raise ValueError("historical original framebuffer control not qualified")
    output_frame_dir=root/"frames"
    if set(p.name for p in output_frame_dir.iterdir())!={f"frame_{x:06d}_256x224.raw" for x in range(FIRST,LAST+1,STEP)}:
        raise ValueError("source probe altered expected callback selection")
    frames=[]
    for m in prior_manifest["each_authentic_callback"]:
        f=m["real_original_snes9x_callback_frame"]
        raw=(output_frame_dir/f"frame_{f:06d}_256x224.raw").read_bytes()
        if len(raw)!=256*224*4 or sha(raw)!=m["original_unchanged_BGRX_sha256"]:
            raise ValueError("a read-only register dump changed original source video")
        frames.append(f)
    log=(root/"original.log").read_text(errors="replace")
    if "script f=5484 quit" not in log:
        raise ValueError("original two-pad script did not finish at pinned frame")
    dumps=[]
    source_dir=root/"registers"
    for tag,expected_frame in DUMP_FRAMES.items():
        matched=re.findall(r"script f=(\d+) dump "+re.escape(tag)+r"\b",log)
        if matched!=[str(expected_frame)]:
            raise ValueError(f"PPU witness {tag} not from expected source frame")
        files={}
        for suffix in ("regs.json","ppuw.tsv","cgram.bin","oam.bin","info.json"):
            file=source_dir/f"{tag}.{suffix}"
            blob=file.read_bytes()
            if not blob:
                raise ValueError(f"original patched core lacks real PPU {suffix}")
            files[suffix]={"bytes":len(blob),"sha256":sha(blob)}
        journal=(source_dir/f"{tag}.ppuw.tsv").read_text(errors="replace")
        if "2100" not in journal and "2131" not in journal:
            # Write journal is source-bound, but the selected frame need not
            # rewrite INIDISP every time. Don't fabricate brightness writes.
            files["warning"]="no INIDISP/CGADSUB write in selected source frame"
        dumps.append({"tag":tag,"actual_original_guest_script_frame":expected_frame,
                      "real_readonly_source_register_artifacts":files})
    return {
      "schema":SCHEMA,
      "actual_original_source_ROM_sha256":ROM_SHA,
      "pinned_original_core_binary_sha256":sha(core.read_bytes()),
      "source_original_action_script_sha256":ORIGINAL_ROUTE_LF_SHA,
      "actual_zero_frame_dump_only_script_sha256":sha(actual),
      "actual_script_quit_frame":5484,
      "all_263_original_PPU_BRGX_raw_frames_byte_exact_to_independent_uninstrumented_reference":True,
      "actual_source_register_dump_cases":dumps,
      "native_original_register_equivalence_not_yet_accepted":True,
      "release_quality_ledger_accepted":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--script",type=Path,required=True)
    p.add_argument("--out-script",type=Path)
    p.add_argument("--verify-root",type=Path)
    p.add_argument("--prior-original",type=Path)
    p.add_argument("--rom",type=Path)
    p.add_argument("--core",type=Path)
    p.add_argument("--result",type=Path)
    a=p.parse_args()
    if a.out_script:
        a.out_script.parent.mkdir(parents=True,exist_ok=True)
        a.out_script.write_bytes(build_script(a.script.read_bytes()))
        print("QA08_ORIGINAL_PPU_SCRIPT read_only_dumps=3 zero_input_frames=1")
    elif a.verify_root and a.prior_original and a.rom and a.core and a.result:
        x=verify(a.verify_root,a.prior_original,a.script,a.rom,a.core)
        a.result.parent.mkdir(parents=True,exist_ok=True)
        a.result.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n",
                            encoding="utf-8")
        print("QA08_ORIGINAL_PPU_REGISTER_TRACE source_frames_repeated=263 "
              "all_exact=1 dumps=3 release=0")
    else:
        p.error("pass --out-script or all verifier inputs")


if __name__=="__main__":
    main()
