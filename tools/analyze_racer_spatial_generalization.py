#!/usr/bin/env python3
"""Generalize racer 5x6 occupancy -> 64x64 OBJ placement across retained snapshots."""

from __future__ import annotations
import argparse, json
from pathlib import Path

from analyze_racer_piece_render_binding import (
    decode_obsel, decode_oam_slot, frame_occupancy_matrix,
    object_nonzero_grid, find_direct_subrect_matches,
)
from extract_racer_presentation_family import extract_frame

P1_ID=0x0FE9
P2_ID=0x0FEB
ATTRS=(0x66,0x68)
SLOTS=(96,97,98,99)


def u16(d:bytes,off:int)->int:
    return int.from_bytes(d[off:off+2],"little")


def analyze_snapshot(rom:bytes, stem:Path)->dict:
    tag=stem.name[:-5] if stem.name.endswith(".wram") else stem.name
    wram=(stem.parent/(tag+".wram.bin")).read_bytes()
    oam=(stem.parent/(tag+".oam.bin")).read_bytes()
    vram=(stem.parent/(tag+".vram.bin")).read_bytes()
    regs=json.loads((stem.parent/(tag+".regs.json")).read_text())
    obsel=decode_obsel(int(regs["obsel"]))
    slots=[decode_oam_slot(oam,s,obsel) for s in SLOTS]
    rows=[]
    for player,(off,attr) in enumerate(((P1_ID,ATTRS[0]),(P2_ID,ATTRS[1])),start=1):
        persistent=u16(wram,off)
        large=[s for s in slots if s["attr"]==attr and s["large"]]
        candidates=[]
        if persistent:
            for delta in range(-3,4):
                fid=(persistent+delta)&0xffff
                try:
                    fr=extract_frame(rom,fid)
                except Exception:
                    continue
                occ=frame_occupancy_matrix(fr)
                for slot in large:
                    grid=object_nonzero_grid(vram,obsel,slot)
                    matches=find_direct_subrect_matches(grid,occ)
                    if len(matches)==1:
                        candidates.append({
                            "frame_id":fid,
                            "frame_id_hex":f"0x{fid:04X}",
                            "delta_from_persistent":delta,
                            "oam_slot":slot["slot"],
                            "oam_tile":slot["tile_hex"],
                            "oam_attr":slot["attr_hex"],
                            "hflip":slot["hflip"],
                            "vflip":slot["vflip"],
                            "packed_cell_count":len(fr["pieces"]),
                            "match":matches[0],
                        })
        rows.append({
            "player":player,
            "persistent_frame_id":persistent,
            "persistent_frame_id_hex":f"0x{persistent:04X}",
            "large_oam_slots":large,
            "unique_nearby_bindings":candidates,
        })
    return {"checkpoint":tag,"obsel":obsel,"players":rows}


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("rom",type=Path)
    ap.add_argument("--dump-dir",type=Path,required=True)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    stems=[]
    for p in sorted(args.dump_dir.glob("*.wram.bin")):
        tag=p.name[:-9]
        if tag.startswith("two-player-") and all((args.dump_dir/f"{tag}.{ext}").exists() for ext in ("oam.bin","vram.bin","regs.json")):
            stems.append(args.dump_dir/(tag+".wram"))
    cps=[analyze_snapshot(rom,s) for s in stems]
    exact=[]
    nearby=[]
    offsets={}
    for cp in cps:
        for p in cp["players"]:
            for b in p["unique_nearby_bindings"]:
                row={"checkpoint":cp["checkpoint"],"player":p["player"],"persistent_frame_id_hex":p["persistent_frame_id_hex"],**b}
                nearby.append(row)
                if b["delta_from_persistent"]==0: exact.append(row)
                offsets.setdefault(str(b["delta_from_persistent"]),0); offsets[str(b["delta_from_persistent"])]+=1
    report={
        "schema_version":1,
        "purpose":"Test retained racer 5x6 spatial placement and quantify persistent-ID to rendered-VRAM phase offsets.",
        "checkpoints":cps,
        "summary":{
            "snapshot_count":len(cps),
            "unique_nearby_bindings":len(nearby),
            "exact_persistent_id_bindings":len(exact),
            "binding_delta_counts":offsets,
            "all_binding_offsets":[b["match"] for b in nearby],
            "all_unique_bindings_at_1_0":bool(nearby) and all(b["match"]["x"]==1 and b["match"]["y"]==0 for b in nearby),
        }
    }
    js=json.dumps(report,indent=2,sort_keys=True)+"\n"
    md=["# Racer spatial generalization","",
        f"Snapshots inspected: **{len(cps)}**.",
        f"Unique nearby frame/OAM/VRAM bindings: **{len(nearby)}**.",
        f"Exact persistent-ID bindings: **{len(exact)}**.",
        f"Binding delta counts: **{offsets}**.",
        f"All unique bindings use 5x6 offset (1,0): **{report['summary']['all_unique_bindings_at_1_0']}**.","",
        "## Bindings",""]
    for b in nearby:
        md.append(f"- {b['checkpoint']} P{b['player']}: persistent {b['persistent_frame_id_hex']} -> frame {b['frame_id_hex']} (delta {b['delta_from_persistent']:+d}), OAM slot {b['oam_slot']} tile {b['oam_tile']}, cells {b['packed_cell_count']}, offset ({b['match']['x']},{b['match']['y']}).")
    text="\n".join(md)+"\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True);args.json_out.write_text(js)
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True);args.md_out.write_text(text)
    print(text)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
