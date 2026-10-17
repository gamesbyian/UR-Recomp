#!/usr/bin/env python3
"""Source-registered original Snes9x OAM vs real Win32 live PPU OAM.

Three independent SHA-pinned original/native archive producers.
Original video callback f-1 == snesref post-retro_run do_dump f == native guest f
as *frame labels*. CPU instruction/beam phase is not proven.
Whole 544 original OAMDATA DMA write stream must reproduce original OAM.
Never edit guest CPU/PPU, tile, palette or frame registration to satisfy this.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

SHA={
 "original":"72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e",
 "original_registered":"2fef0440b97a69025bf9ee539551b414ef7f1f11978172aea5565f338b35d4c9",
 "native":"002c95a44f3539652760609c6f6d7376c82e6014f2481cc60bbb1f8990b3b970",
}
SLOTS=(96,97,98,99,112,113,114)
EXPECTED_ORIGINAL={4032:("cc","cc","e6","e6","a2","a4","a6"),
                   4176:("cc","cc","e2","e2","a2","a4","a6")}
EXPECTED_NATIVE={4032:("ce","ce","e6","e6","a0","a2","a4"),
                 4176:("ce","ce","e2","e2","a0","a2","a4")}
CALLBACKS={1280:1279,4032:4031,4176:4175}
TAGS={1280:"qa08_arrow_1280",4032:"qa08_medal_4032",4176:"qa08_medal_4176"}
ROM="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
GUEST="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def check(got,want,what:str)->None:
    if got!=want: raise ValueError(f"source registration/identity mismatch {what}: {got!r} != {want!r}")

def source_slot(oam:bytes,n:int)->dict:
    if len(oam)!=544 or not 0<=n<128: raise ValueError("truncated original OAM")
    x,y,tile,attr=oam[4*n:4*n+4]
    high=(oam[512+n//4]>>((n%4)*2))&3
    signed=x+(256 if high&1 else 0)
    if signed>=256:signed-=512
    return {"slot":n,"x":signed,"y":y,"tile":tile,"attr":attr,
            "high":high,"palette":(attr>>1)&7,"priority":(attr>>4)&3}

def real_original_DMA(frame:int, journal:bytes,oam:bytes)->dict:
    lines=journal.decode("ascii").splitlines()
    check(lines[0],"#frame\tvcounter\thcounter\taddr\tvalue\tsource",
          f"original {frame} PPU register journal schema")
    stream=[];clock=[]
    for line in lines[1:]:
        if line.startswith("#"):
            if "truncated" in line: raise ValueError("source PPU ring truncated")
            continue
        parts=line.split("\t")
        if len(parts)!=6:raise ValueError("incomplete real PPU journal event")
        sf,v,h,addr,val,owner=parts
        if addr!="2104":continue
        if int(sf)!=frame or owner!="dma" or not 225<=int(v)<=261:
            raise ValueError("original active-line/non-DMA OAM writes")
        stream.append(int(val,16));clock.append((int(v),int(h)))
    check(len(stream),544,f"original {frame} full 512+32 OAMDATA bytes")
    check(bytes(stream),oam,f"original {frame} complete OAM DMA memory")
    if clock!=sorted(clock):raise ValueError("original DMA chronological mismatch")
    return {"DMA_OAM_bytes":len(stream),"first_VBlank_v":clock[0][0],
            "last_VBlank_v":clock[-1][0],"observed_active_line_OAM_writes":0,
            "original_544byte_DMA_equals_actual_OAM":True,"journal_sha256":sha(journal)}

def verify(original:Path, registered:Path, native:Path)->dict:
    archives={}
    try:
        for key,path in (("original",original),("original_registered",registered),("native",native)):
            raw=path.read_bytes()
            check(sha(raw),SHA[key],key+" complete ZIP")
            archives[key]=zipfile.ZipFile(path)
            members=archives[key].namelist()
            if len(members)!=len(set(members)):raise ValueError("duplicate ZIP evidence members")
        o,e,n=archives["original"],archives["original_registered"],archives["native"]
        manifest=json.loads(o.read("qa08-original-2p-fullroute.json"))
        native_manifest=json.loads(n.read("qa08-native-effective-pixel-owner.json"))
        receipt=json.loads(e.read("matched-original-fields.json"))
        untouched=json.loads(e.read("original-263-verified.json"))
        check(manifest["actual_callbacks_captured"],263,"original full-route sampled frame count")
        check(manifest["unaltered_USA_ROM_sha256"],ROM,"original USA ROM")
        check(native_manifest["real_native_2p_guest_crc_sha256"],GUEST,"native unchanged 5484 guest CRCs")
        check(native_manifest["real_native_2p_guest_frames"],5484,"native complete guest route")
        check(native_manifest["independently_source_qualified_native_scanline_OAM_snapshots"],70,"native OAM line observations")
        check(native_manifest["original_snes9x_2014_same_field_pixel_priority_proven"],False,
              "never claim original effective OBJ before verifying it")
        if not receipt["host_preincrement_plus_one_registration_verified"]:
            raise ValueError("old misregistered Snes9x host capture supplied")
        check(receipt["original_unmodified_callback_endfield_count"],3,"original corrected field count")
        if not untouched["263_original_unmasked_BGRX_frames_identical_to_prior_original"]:
            raise ValueError("original reference video corpus was altered")
        src={int(x["real_original_snes9x_callback_frame"]):x["original_unchanged_BGRX_sha256"]
             for x in manifest["each_authentic_callback"]}
        if len(src)!=263:raise ValueError("original 263 source callbacks incomplete")
        current={}
        for host,callback in CALLBACKS.items():
            tag=TAGS[host]
            info=json.loads(e.read(f"registers/{tag}.info.json"))
            regs=json.loads(e.read(f"registers/{tag}.regs.json"))
            check((info["frame"],info["fb_frame"],regs["frame_tag"],regs["total_emulated_frames"]),
                  (host,host,host,host),"original video/host postrun counter registration")
            if info["ppuw_truncated"]:raise ValueError("truncated original PPU port history")
            raw=o.read(f"frames/frame_{callback:06d}_256x224.raw")
            fb=e.read(f"registers/{tag}.fb.bgrx")
            check(len(raw),256*224*4,"whole 2014 original reference video")
            check(sha(raw),src.get(callback),"original unmodified source frame callback SHA")
            check(fb,raw,"same original video callback versus correctly labelled host screenshot")
            oam=e.read(f"registers/{tag}.oam.bin")
            cgram=e.read(f"registers/{tag}.cgram.bin")
            check(len(oam),544,"original full OAM")
            check(len(cgram),512,"original full CGRAM")
            dma=real_original_DMA(host,e.read(f"registers/{tag}.ppuw.tsv"),oam)
            current[host]={"actual_video_callback":callback,"host_after_retro_run":host,
                           "raw_callback_sha256":sha(raw),"OAM_544_sha256":sha(oam),
                           "CGRAM_512_sha256":sha(cgram),"real_port_DMA":dma,
                           "slots":{slot:source_slot(oam,slot) for slot in SLOTS}}
        pair=[]
        for guest in (4032,4176):
            rows=native_manifest["native_OAM_in_effect_on_selected_lines"]
            for idx,slot in enumerate(SLOTS):
                original=current[guest]["slots"][slot]
                check(original["tile"],int(EXPECTED_ORIGINAL[guest][idx],16),
                      f"original correctly registered OAM guest {guest} slot {slot}")
                matched=[z for z in rows if z["native_guest"]==guest and z["OAM_slot"]==slot]
                check(len(matched),5,f"live native five raster lines guest {guest} slot {slot}")
                source={(v["native_scanline_oam_xy"],v["native_scanline_oam_tile_attr"],
                          v["native_scanline_high_oam_pair"]) for v in matched}
                check(len(source),1,"native actual OAM data changes within tested medal lines")
                xy,ta,hi=source.pop()
                check(xy,f"{original['y']:02x}{original['x']&255:02x}",
                      f"source sprite XY guest {guest} slot {slot}")
                check(int(ta[:2],16),original["attr"],
                      f"source palette/priority guest {guest} slot {slot}")
                check(hi,original["high"],"OAM high-bit state")
                check(ta[2:],EXPECTED_NATIVE[guest][idx],
                      f"native tile source guest {guest} slot {slot}")
                delta=int(ta[2:],16)-original["tile"]
                check(delta,-2 if slot>=112 else 2 if slot<=97 else 0,
                      f"matched field source tile delta slot {slot}")
                pair.append({"guest":guest,"source_original_callback":CALLBACKS[guest],
                             "original_postrun":guest,"slot":slot,
                             "original_tile":EXPECTED_ORIGINAL[guest][idx],
                             "native_tile":ta[2:],"native_minus_original":delta,
                             "five_actual_native_raster_line_samples":True})
        return {
          "schema":"qa08-correctly-registered-real-original-native-medal-OAM-differential/1",
          "exact_source_archive_SHA256":SHA,
          "frame_mapping":"native f == Snes9x do_dump postrun f == original video callback f-1",
          "original_263_video_callbacks_unchanged":True,
          "original_3_corrected_host_fields_and_full_VBlank_DMA":current_to_report(current),
          "native_70_actual_live_OAM_line_reads":True,
          "accepted_14_slot_comparisons":pair,
          "medal_tiles_native_minus_original":-2,
          "adjacent_96_97_native_minus_original":2,
          "adjacent_98_99_native_minus_original":0,
          "same_numbered_field_not_CPU_instruction_or_beam_equivalence":True,
          "original_effective_pixel_layer_ownership_not_proven":True,
          "renderer_or_guest_CPU_correction_applied":False,
          "graphics_release_accepted":False,
        }
    finally:
        for a in archives.values():a.close()

def current_to_report(current:dict)->list[dict]:
    return [{k:v for k,v in current[f].items() if k!="slots"} for f in sorted(current)]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("original","original-registered","native","out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    result=verify(a.original,a.original_registered,a.native)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_CORRECTLY_REGISTERED_REAL_OAM original_DMA_544_each=1 14_slots=1 "
          "tile_deltas=(-2,+2,0) source_priority_unproven=1 release=0")

if __name__=="__main__":
    main()
