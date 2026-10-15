#!/usr/bin/env python3
"""Read-only original-USA 2P $2121/$2122 results chronology at 5183/5184.

Keep the EXACT stock route and previously verified three zero-frame dumps.
Use a separately opted-in read-only original-host callback to capture 5183,
and prove all 263 full 256x224 BGRX frames equal the immutable original.
An earlier press-command split was rejected because snesref inserts idle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from tools import qa08_original_twoplayer_ppu_register_trace as control
except ImportError:
    import qa08_original_twoplayer_ppu_register_trace as control

DUMPS = {**control.DUMP_FRAMES, "qa08_results_previous": 5183}
SCHEMA = "qa08-original-source-2p-adjacent-results-CGRAM-chronology/2"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cgram_fnv(raw: bytes) -> str:
    if len(raw) != 512:
        raise ValueError("CGRAM must have 256 15-bit words")
    h = 2166136261
    for c in raw:
        h = ((h ^ c) * 16777619) & 0xffffffff
    return f"{h:08x}"


def build_script(raw: bytes) -> bytes:
    """Return the exact already-verified 3-dump original input script.

    Do NOT split press holds: snesref inserts a trailing idle frame after
    each completed press command. The rejected split changed original PPU
    callback 5215. The new 5183 dump is inserted by the opt-in read-only
    reference-host callback, not by modifying controller commands.
    """
    return control.build_script(raw)


def parse_history(raw: bytes) -> dict:
    """Fail closed on incomplete read-only original PPU-ring port chronology."""
    lines=raw.decode("ascii").splitlines()
    if len(lines)<5 or lines[:2] != [
        "#range=5072..5184", "frame\tvcounter\thcounter\taddr\tvalue\tsource"]:
        raise ValueError("not the pinned 112-frame original PPU chronology")
    counts={}
    rows=[]
    for line in lines[2:]:
        if line.startswith("#"):
            if "=" not in line:
                raise ValueError("malformed original readback metadata")
            k,v=line[1:].split("=",1)
            if k in counts:
                raise ValueError("duplicate original-ring metadata")
            counts[k]=v
            continue
        parts=line.split("\t")
        if len(parts)!=6:
            raise ValueError("not a source PPU port record")
        f,vc,hc,addr,value,src=parts
        if (not 5072<=int(f)<=5184 or addr not in ("2121","2122")
            or not 0<=int(vc)<=340 or not 0<=int(hc)<=340
            or len(value)!=2 or src not in ("cpu","dma","hdma")):
            raise ValueError("out of range or malformed PPU data-port write")
        rows.append({"frame":int(f),"v":int(vc),"h":int(hc),
                     "addr":addr,"value":value,"source":src})
    if (set(counts)!={"ring_earliest","port_writes","scan_complete"} or
        counts["scan_complete"]!="1" or int(counts["ring_earliest"])>5072 or
        int(counts["port_writes"])!=len(rows)):
        raise ValueError("original ring has incomplete coverage or bad write count")
    by_frame={}
    for entry in rows:
        f=str(entry["frame"])
        by_frame[f]=by_frame.get(f,0)+1
    return {"source_window":[5072,5184],"source_port_write_count":len(rows),
            "source_port_writes_by_frame":by_frame,
            "source_latest_16_port_writes":rows[-16:],
            "original_ring_earliest_frame":int(counts["ring_earliest"]),
            "raw_112_frame_port_writes_sha256":sha(raw)}


def verify(root: Path, prior: Path, script: Path, rom: Path, core: Path) -> dict:
    if sha(rom.read_bytes()) != control.ROM_SHA:
        raise ValueError("source USA ROM differs")
    if (root / "qa08-ppu-observer.script").read_bytes() != build_script(script.read_bytes()):
        raise ValueError("executed original script differs")
    earlier = json.loads((prior / "qa08-original-2p-fullroute.json").read_text())
    if earlier.get("actual_callbacks_captured") != 263 or earlier.get("actual_script_quit_frame") != 5484:
        raise ValueError("independent original reference is incomplete")
    expected = {f"frame_{n:06d}_256x224.raw" for n in
                range(control.FIRST, control.LAST + 1, control.STEP)}
    if {x.name for x in (root / "frames").iterdir()} != expected:
        raise ValueError("263 real PPU frames are not all present")
    for entry in earlier["each_authentic_callback"]:
        n = entry["real_original_snes9x_callback_frame"]
        data = (root / "frames" / f"frame_{n:06d}_256x224.raw").read_bytes()
        if len(data) != 256*224*4 or sha(data) != entry["original_unchanged_BGRX_sha256"]:
            raise ValueError(f"read-only split changed source original raster: {n}")
    log = (root / "original.log").read_text(errors="replace")
    if re.findall(r"(?m)^script f=(\d+) quit\s*$", log) != ["5484"]:
        raise ValueError("script termination/guest duration differs")
    receipts = []
    palettes = {}
    for tag, frame in DUMPS.items():
        actual = re.findall(r"script f=(\d+) dump " + re.escape(tag) + r"\b", log)
        if actual != [str(frame)]:
            raise ValueError(f"{tag}: actual original frame {actual} rather than {frame}")
        files = {}
        for suffix in ("regs.json","ppuw.tsv","cgram.bin","oam.bin","info.json"):
            data = (root/"registers"/f"{tag}.{suffix}").read_bytes()
            if not data:
                raise ValueError(f"{tag}.{suffix} missing")
            if suffix in ("regs.json","info.json"):
                json.loads(data)
            files[suffix] = {"bytes":len(data),"sha256":sha(data)}
            if suffix == "cgram.bin":
                palettes[tag] = data
                files[suffix]["fnv1a"] = cgram_fnv(data)
        receipts.append({"source_tag":tag,"original_script_frame":frame,
                         "original_register_artifacts":files})
    left, right = palettes["qa08_results_previous"], palettes["qa08_results_cgram"]
    if cgram_fnv(left)!="e8cdbe60" or cgram_fnv(right)!="e8cdbe60":
        raise ValueError("independently authenticated adjacent original CGRAM changed")
    history = parse_history(
        (root/"registers"/"qa08-results-5072-5184-cgram-history.tsv").read_bytes())
    differences = [
        {"word":i,"before":left[2*i:2*i+2].hex(),"after":right[2*i:2*i+2].hex()}
        for i in range(256) if left[2*i:2*i+2] != right[2*i:2*i+2]]
    return {
        "schema":SCHEMA, "original_ROM_sha256":control.ROM_SHA,
        "original_core_sha256":sha(core.read_bytes()),
        "unchanged_stock_script_sha256":control.ORIGINAL_ROUTE_LF_SHA,
        "unaltered_original_three_dump_script_sha256":sha(build_script(script.read_bytes())),
        "source_5183_cgram_fnv1a":cgram_fnv(left),
        "additional_dump_acquired_after_retro_run_without_new_script_command":True,
        "source_5184_cgram_fnv1a":cgram_fnv(right),
        "source_palette_words_changed":len(differences),
        "source_palette_changed_words_first_32":differences[:32],
        "source_palette_changed_words_full_sha256":sha(json.dumps(differences,sort_keys=True).encode()),
        "source_receipts":receipts,
        "source_prior_112_frame_CGRAM_write_history":history,
        "263_original_unmasked_BGRX_frames_identical_to_prior_original":True,
        "script_still_quits_at_5484":True,
        "raw_original_ppuw_TSV_requires_explicit_write_chronology_review":True,
        "native_guest_phase_certified":False, "raster_fix_accepted":False,
        "release_ledger_accepted":False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--script",required=True,type=Path)
    p.add_argument("--out-script",type=Path)
    p.add_argument("--verify-root",type=Path)
    p.add_argument("--prior-original",type=Path)
    p.add_argument("--rom",type=Path)
    p.add_argument("--core",type=Path)
    p.add_argument("--result",type=Path)
    a = p.parse_args()
    if a.out_script and not any((a.verify_root,a.prior_original,a.rom,a.core,a.result)):
        a.out_script.parent.mkdir(parents=True,exist_ok=True)
        a.out_script.write_bytes(build_script(a.script.read_bytes()))
        print("QA08_CGRAM_5183_5184: input unchanged, three script dumps + opt-in host 5183")
    elif not a.out_script and all((a.verify_root,a.prior_original,a.rom,a.core,a.result)):
        receipt = verify(a.verify_root,a.prior_original,a.script,a.rom,a.core)
        a.result.parent.mkdir(parents=True,exist_ok=True)
        a.result.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        print("QA08_CGRAM_5183_5184: 263 original frames unchanged; "
              f"palette_words_changed={receipt['source_palette_words_changed']}; "
              f"source_prior_112_frame_port_writes={receipt['source_prior_112_frame_CGRAM_write_history']['source_port_write_count']}; "
              "native/graphics/release=unaccepted")
    else:
        p.error("supply --out-script or all verification inputs")


if __name__ == "__main__":
    main()
