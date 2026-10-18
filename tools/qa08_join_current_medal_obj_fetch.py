#!/usr/bin/env python3
"""Join actual current RF017 4bpp sprite writes to effective medal pixel owners.

Only the source-pinned original 5,484-guest Windows observer qualifies this
evidence. This parser cannot repair the PPU, infer a native CPU clock or claim
the 2014 Snes9x original medal used the same OAM slot. The final writer to a
particular OBJ buffer coordinate is a candidate; it becomes a proven actual
native winner ONLY if its zbuffer word equals the already observed effective
PPU OBJ pixel from the same guest/frame/line and no later host overlay wins.
"""
from __future__ import annotations

FRAMES=(4032,4048,4064,4080,4176)
COORDS=((207,91),(205,115),(205,139),(225,96),(225,120))
PREFIX="UR_QA08_WIN_OBJ_FETCH "
FIELDS={"frame","x","raster_y","slot","oam","attrs","oam_tile",
        "used_tile","objadr","row","src_col","px","palette","priority",
        "pixel","plane","writer_obj"}
MAX_WRITES=700

def record(s:str)->dict:
    if not s.startswith(PREFIX):
        raise ValueError("unrelated original/native sprite producer")
    parts={}
    for token in s[len(PREFIX):].split():
        if token.count("=")!=1:
            raise ValueError("invalid PPU sprite producer record")
        k,v=token.split("=",1)
        if k in parts:raise ValueError("duplicate native sprite field")
        parts[k]=v
    if set(parts)!=FIELDS:
        raise ValueError("missing/extra actual original PPU fetch operand")
    dec=["frame","x","raster_y","slot","row","src_col","px","priority"]
    hx=[k for k in FIELDS if k not in dec]
    try:
        d={k:int(parts[k],10) for k in dec}
        d.update({k:int(parts[k],16) for k in hx})
    except ValueError as e:
        raise ValueError("malformed genuine PPU OAM/VRAM operand") from e
    f,x,y=d["frame"],d["x"],d["raster_y"]
    if (f not in FRAMES or (x,y) not in COORDS or
        not (0<=d["slot"]<128) or
        not (0<=d["oam"]<=0xffff and 0<=d["attrs"]<=0xffff) or
        d["oam_tile"]!=(d["attrs"]&0xff) or
        not (0<=d["used_tile"]<1024 and 0<=d["objadr"]<=0x7fff) or
        not (0<=d["px"]<8 and 0<=d["src_col"]<64) or
        not (0<=d["row"]<64) or
        d["palette"] not in range(0x80,0x100,0x10) or
        not (0<=d["priority"]<=255) or
        not (1<=d["pixel"]<=15) or
        not (0<=d["plane"]<=0xffffffff)):
        raise ValueError("unqualified current native medal sprite fetch")
    flip=bool(d["attrs"]&0x4000)
    shift=d["px"] if flip else 7-d["px"]
    plane=d["plane"]>>shift
    pix=(plane&1)|((plane>>7)&2)|((plane>>14)&4)|((plane>>21)&8)
    if pix!=d["pixel"] or (
        (d["priority"]<<8)+d["palette"]+d["pixel"]!=d["writer_obj"]):
        raise ValueError("PPU VRAM 4bpp pixel, palette or priority inconsistent")
    return d

def joined(log:str, owner:dict)->dict:
    if (owner.get("real_2p_guest_frames")!=5484 or
        owner.get("real_guest_CRC_SHA256")!=
        "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568" or
        len(owner.get("pixels",[]))!=25 or
        owner.get("source_original_same_field_ownership_proven") is not False):
        raise ValueError("authentic current RF017 original PPU owner gate missing")
    keys=[(p["frame"],p["xy"][0],p["xy"][1]) for p in owner["pixels"]]
    expected={(f,x,y) for f in FRAMES for x,y in COORDS}
    if len(set(keys))!=len(keys) or set(keys)!=expected:
        raise ValueError("native source owner set missing/duplicated a medal point")
    samples={}
    count=0
    for ln in log.splitlines():
        if not ln.startswith(PREFIX):continue
        d=record(ln)
        key=(d["frame"],d["x"],d["raster_y"])
        samples.setdefault(key,[]).append(d)
        count+=1
        if count>MAX_WRITES:
            raise ValueError("source OAM/VRAM fetch exceeds bounded trace budget")
    if not samples:
        raise ValueError("no genuine current PPU per-pixel 4bpp fetch observed")
    proven=[]
    not_obj=[]
    for p in owner["pixels"]:
        frame,x,y=p["frame"],p["xy"][0],p["xy"][1]
        if frame not in FRAMES or (x,y) not in COORDS:
            raise ValueError("unexpected PPU effective owner coordinate")
        target=(frame,x,y)
        writes=samples.get(target,[])
        # The old source observer knows which final visible main layer won.
        if p["main"]!="4":
            not_obj.append({"frame":frame,"xy":[x,y],
                            "effective_main_layer":p["main"],
                            "direct_OBJ_candidate_writes":len(writes)})
            continue
        if not writes:
            raise ValueError("current native OBJ main pixel has no genuine sprite fetch")
        last=writes[-1]
        source_obj=int(p["obj_word"],16)
        if last["writer_obj"]!=source_obj:
            raise ValueError(
                "OBJ buffer winner not last regular fetched sprite; "
                "extra object overwrite or different effective epoch")
        proven.append({
            "guest":frame,"xy":[x,y],
            "actual_current_native_winning_oam_slot":last["slot"],
            "actual_current_native_winning_oam_tile":f"{last['oam_tile']:02x}",
            "actual_current_native_used_4bpp_tile":last["used_tile"],
            "source_vram_tile_base_word_address":last["objadr"],
            "actual_source_4bpp_plane_word":f"{last['plane']:08x}",
            "actual_pixel_nibble":last["pixel"],
            "palette_base":f"{last['palette']:02x}",
            "sprite_priority":last["priority"],
            "direct_sprite_contenders_in_real_writer_order":len(writes),
            "actual_final_OBJ_zbuffer_word":f"{source_obj:04x}",
            "last_direct_writer_matches_effective_OBJ":True,
        })
    if len(proven)<4 or not any(p["guest"]==4032 for p in proven):
        raise ValueError("insufficient independently observed current medal OBJ winners")
    return {
        "schema":"qa08-current-RF017-real-4bpp-OBJ-pixel-winners/1",
        "actual_2p_USA_guest_CRC_SHA256":owner["real_guest_CRC_SHA256"],
        "actual_source_sprite_port_writes":count,
        "current_native_exact_sprite_winners":len(proven),
        "current_native_non_OBJ_main_cases":len(not_obj),
        "actual_current_OBJ_source_tile_pixels":proven,
        "effective_main_non_OBJ_pixels":not_obj,
        "source_2014_Snes9x_pixel_winner_tile_identical_proven":False,
        "original_vs_native_CPU_NMI_instruction_phase_proven":False,
        "native_VRAM_content_vs_2014_exact_source_verified":False,
        "global_output_shift_or_tile_reindex_authorized":False,
        "renderer_mutation_or_art_release_accepted":False,
    }
