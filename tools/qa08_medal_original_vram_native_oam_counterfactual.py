#!/usr/bin/env python3
"""QA08 source-only original VRAM / actual Windows OAM-name counterfactual.

Original completed-frame VRAM is *not native live VRAM*. The seven genuine
2014 source OBJ 16x16 FNVs establish original VRAM consistency; the actual
Win32 PPU records establish separate on-scanline indexed colour. No bytes
from SRAM/WRAM/VRAM/ROM or a decoded image leave the CI artifact.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path

PIN={
 "registered":"2fef0440b97a69025bf9ee539551b414ef7f1f11978172aea5565f338b35d4c9",
 "indexed":"a280062d25fa721c096485522f6bb4a8d5af359ee797ad2d41db400e77b4efe9",
 "native":"f467aaafc193e0b8e56934e6f505c10d60c3a4a1afa8727ffa376e5cdf7d53de"}
SLOTS=(96,97,98,99,112,113,114)
PAIRS=((4031,4032),(4175,4176))
POINTS=((207,91,112),(205,115,113),(205,139,114),(225,96,99),(225,120,98))
GUEST_CRC="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"


def indexed(vram:bytes,name:int,base:int,selector:int,x:int,y:int,
            hf:bool=False,vf:bool=False)->int:
    if len(vram)!=65536 or not 0<=name<=511 or not 0<=x<16 or not 0<=y<16:
        raise ValueError("SNES 4bpp indexed source requires full original VRAM and in-bounds tile")
    x=15-x if hf else x
    y=15-y if vf else y
    tile=(name&0x100)|(((name&0xf0)+((y>>3)<<4))&0xf0)|((name+(x>>3))&15)
    a=(base+32*tile+(selector if tile&0x100 else 0))&0xffff
    return sum(((vram[(a+d+2*(y&7))&0xffff]>>(7-(x&7)))&1)<<i
               for i,d in enumerate((0,1,16,17)))


def sprite_digest(vram:bytes,name:int,base:int,selector:int,h:bool,v:bool):
    digest=14695981039346656037
    opaque=0
    for y in range(16):
        for x in range(16):
            n=indexed(vram,name,base,selector,x,y,h,v)
            opaque+=bool(n)
            digest=((digest^n)*1099511628211)&((1<<64)-1)
    return f"{digest:016x}",opaque


def cgram_word(c:bytes,pal:int,index:int)->int:
    if len(c)!=512 or not 0<=pal<8 or not 0<=index<16:
        raise ValueError("bad CGRAM/palette/index")
    at=2*(128+pal*16+index)
    return int.from_bytes(c[at:at+2],"little")


def verify(registered:Path,observed:Path,native_source:Path)->dict:
    for label,path in (("registered",registered),("indexed",observed),("native",native_source)):
        if hashlib.sha256(path.read_bytes()).hexdigest()!=PIN[label]:
            raise ValueError("unverified original/native source ZIP "+label)
    rows=[]
    with zipfile.ZipFile(registered) as z,zipfile.ZipFile(observed) as o,zipfile.ZipFile(native_source) as n:
        original=json.loads(o.read("verified-indexed16-source.json"))
        win=json.loads(n.read("qa08-native-effective-pixel-owner.json"))
        m=json.loads(n.read("qa08-windows-2p-fullroute.json"))
        if (original.get("original_263_full_source_frame_bytes_identical") is not True or
            original.get("actual_sampled_original_sprite_slots")!=14 or
            original.get("actual_sampled_original_pixel_slots")!=10 or
            win.get("independently_source_qualified_native_pixels")!=11 or
            win.get("independently_source_qualified_native_scanline_OAM_snapshots")!=70 or
            m.get("actual_native_guest_CRC_sha256")!=GUEST_CRC):
            raise ValueError("source original/native frame identity or original sprite provenance invalid")
        prior={(p["original_video_callback"],p["source_slot"]):p for p in
               original["authenticated_16x16_sprites"]}
        samples={(p["original_video_callback"],tuple(p["source_xy"])):p for p in
                 original["actual_indexed_pixel_candidates"]}
        for cb,guest in PAIRS:
            prefix=f"registers/qa08_medal_{guest}"
            regs=json.loads(z.read(prefix+".regs.json"))
            oam=z.read(prefix+".oam.bin")
            vram=z.read(prefix+".vram.bin")
            c=z.read(prefix+".cgram.bin")
            cfg=regs["ppu"]["obj"]
            if (len(oam)!=544 or len(vram)!=65536 or len(c)!=512 or
                regs["frame_tag"]!=guest or regs["total_emulated_frames"]!=guest or
                cfg["obsel"]!="63" or cfg["size_select"]!=3 or
                cfg["name_base"]!="C000" or cfg["name_select"]!="0000"):
                raise ValueError("unqualified original postrun VRAM/OAM source")
            base=int(cfg["name_base"],16);select=int(cfg["name_select"],16)
            for slot in SLOTS:
                off=slot*4; attr=oam[off+3]
                name=oam[off+2]|((attr&1)<<8)
                digest,opaque=sprite_digest(vram,name,base,select,bool(attr&64),bool(attr&128))
                source=prior[cb,slot]
                if (digest,opaque)!=(source["tile_index_FNV64"],source["source_16x16_opaque_pixels"]):
                    raise ValueError("original VRAM has changed vs independent source 16x16 indexed fingerprint")
            for x,y,slot in POINTS:
                off=slot*4
                ox,oy,low,attr=oam[off:off+4]
                name=low|((attr&1)<<8)
                pal=(attr>>1)&7
                dx=x-ox;dy=(y-oy)&255
                oldidx=indexed(vram,name,base,select,dx,dy,bool(attr&64),bool(attr&128))
                orig=samples[cb,(x,y)]["original_OAM_slots_with_source_sample"][str(slot)]
                if (oldidx!=orig["indexed4bpp"] or
                    cgram_word(c,pal,oldidx)!=int(orig["CGRAM_RGB15_word"],16)):
                    raise ValueError("not the original live source 4bpp pixel at original OAM name")
                matches=[r for r in win["native_OAM_in_effect_on_selected_lines"]
                         if (r["native_guest"],r["OAM_slot"],r["raster_y"],r["x"])==(guest,slot,y,x)]
                screen=[r for r in win["native_real_PPU_resolved_pixels"]
                        if (r["native_guest"],r["raster_y"],r["x"])==(guest,y,x)]
                if len(matches)!=1 or len(screen)!=1:
                    raise ValueError("missing duplicate/foreign actual Win32 PPU source")
                r=matches[0];p=screen[0]
                native_attr=int(r["native_scanline_oam_tile_attr"],16)
                native_name=(native_attr&255)|(((native_attr>>8)&1)<<8)
                if (r["native_scanline_oam_xy"]!=f"{oy:02x}{ox:02x}" or
                    (native_attr>>8)!=attr or p["inidisp"]!="0e" or p["cgadsub"]!="7f"):
                    raise ValueError("native OAM other than tile index differs from original")
                hypothesis=indexed(vram,native_name,base,select,dx,dy,bool(attr&64),bool(attr&128))
                live_palet= int(p["native_effective_OBJ_CGRAM_slot"],16)
                if p["resolved_main_layer"]==4:
                    actual=live_palet-(128+16*pal)
                    if not 0<=actual<=15 or cgram_word(c,pal,actual)!=int(p["native_effective_OBJ_colour_word"],16):
                        raise ValueError("real native indexed OBJ colour is not independently original CGRAM")
                else:
                    actual=None
                    if p["resolved_main_layer"]!=0 or live_palet!=0 or hypothesis!=0:
                        raise ValueError("no independently observed BG1-over-transparent-OBJ")
                rows.append({
                    "original_callback":cb,"native_guest":guest,"xy":[x,y],
                    "slot":slot,"original_OAM_name9":f"{name:03x}",
                    "actual_native_OAM_name9":f"{native_name:03x}",
                    "actual_original_indexed_4bpp":oldidx,
                    "original_VRAM_with_native_OAM_name_hypothetical_4bpp":hypothesis,
                    "actual_native_observed_palette_4bpp_index":actual,
                    "native_observed_CGRAM_word":p["native_effective_OBJ_colour_word"],
                    "conditional_original_VRAM_matches_actual_native_index":(
                        hypothesis==actual if actual is not None else hypothesis==0)})
    if (len(rows)!=10 or
        [r["conditional_original_VRAM_matches_actual_native_index"] for r in rows]!=
          [True,True,True,False,False]*2 or
        [r["actual_original_indexed_4bpp"] for r in rows]!=[6,6,0,15,15]*2 or
        [r["original_VRAM_with_native_OAM_name_hypothetical_4bpp"] for r in rows]!=[0,4,6,15,15]*2 or
        [r["actual_native_observed_palette_4bpp_index"] for r in rows]!=[None,4,6,14,14]*2):
        raise ValueError("counterfactual and actual source-index evidence not stable")
    return {
      "schema":"qa08-original-VRAM-vs-real-Win32-OAM-name-five-medal-source-index/1",
      "status":"six_source_pixels_predicted_by_originalVRAM_plus_nativeOAM;four_equalOAM_index_divergences",
      "pinned_producer_zip_sha256":PIN,
      "source_original_14_16x16_sprite_FNV_matches_full_original_VRAM":True,
      "source_original_263_256x224_frames_preserved":True,
      "source_native_5484_frame_CRC_preserved":True,
      "original_vs_native_registered_pixels":rows,
      "total_source_pairs":10,"conditional_original_VRAM_matching_pairs":6,
      "conditional_original_VRAM_mismatching_pairs":4,
      "two_distinct_unresolved_equalOAM_medal_pixels":[[225,96],[225,120]],
      "gold_medal_original_palette_index":15,
      "gold_medal_actual_native_palette_index":14,
      "original_palette5_index15_word":"4b3b",
      "actual_native_palette5_index14_word":"3a11",
      "native_VRAM_live_content_same_as_original":False,
      "native_tile_index_decoder_equivalence_proven":False,
      "PPU_or_CPU_OAM_timing_root_cause_proven":False,
      "renderer_patch_authorized":False,
      "QA08_QA10_release_or_HDart_accepted":False,
      "no_ROM_VRAM_WRAM_SRAM_or_sprite_bitmap_exported":True
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("registered","indexed-original","native","out"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    report=verify(a.registered,a.indexed_original,a.native)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("QA08_MEDAL_VRAM_COUNTERFACTUAL MATCH=6/10 EQ_OAM_INDEX_DIVERGENT=4/10 LIVE_NATIVE_VRAM=UNPROVEN")


if __name__=="__main__":
    main()
