#!/usr/bin/env python3
"""One bounded actual Win32 source guest race: effective medal pixel provenance.

Reuse existing unchanged 2P route and Windows binary; only set a read-only
Uniracers PPU trace opt-in. Every chosen pixel is source-divergent in pinned
original Snes9x vs real compiled Win32 256x224 PPU source images. This is
native layer and register telemetry, not an original same-field acceptance,
priority proof, a colour/math fix, or a release check.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
try:
    from tools.baldosa_windows_native_pause_route import run_route
except ImportError:
    from baldosa_windows_native_pause_route import run_route

ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
ROUTE_SHA="ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194"
GUEST_CRC_SHA="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
SLOTS=(96,97,98,99,112,113,114)
ORIGINAL_SOURCE_ZIP="72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
WINDOWS_SOURCE_ZIP="f01ab5a4888c227f306a0b9cd89e67710a4b41cad4c22867072280a17811fa82"
# These are real untouched Windows Original PPU RGB bytes from the archived
# post-V0 source frames; none of them is the original-Snes9x expected RGB.
POINTS={
    (1280,55,65):(90,66,74),
    (4032,207,91):(115,115,115),
    (4032,205,115):(132,49,24),
    (4032,205,139):(115,57,74),
    (4032,225,96):(132,123,107),
    (4032,225,120):(132,123,107),
    (4176,207,91):(115,115,115),
    (4176,205,115):(132,49,24),
    (4176,205,139):(115,57,74),
    (4176,225,96):(132,123,107),
    (4176,225,120):(132,123,107),
}
ORIGINAL_RGB={
    (1280,55,65):(90,74,82),
    **{(frame,x,y):rgb
       for frame in (4032,4176)
       for x,y,rgb in (
         (207,91,(115,57,74)),
         (205,115,(115,57,74)),
         (205,139,(132,132,132)),
         (225,96,(206,189,140)),
         (225,120,(206,189,140)),
       )},
}
FIELDS=frozenset(("frame","x","raster_y","ppu_line","main","sub",
    "math","window","premain","presub","postmath","final","obj",
    "obj_cgram_index","obj_word","inidisp","cgadsub","cgwsel",
    "fixed","tm","ts","obsel"))
OAM_FIELDS=frozenset(("frame","x","ppu_line","slot","xy","attrs","high"))

def sha256(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def fields(line:str,prefix:str,allowed:frozenset[str])->dict[str,str]:
    if not line.startswith(prefix+" "):
        raise ValueError("unexpected source pixel telemetry prefix")
    d={}
    for token in line[len(prefix)+1:].split():
        if token.count("=")!=1:
            raise ValueError("malformed source telemetry column")
        key,value=token.split("=",1)
        if not key or key in d:
            raise ValueError("duplicate/empty PPU telemetry field")
        d[key]=value
    if set(d)!=allowed:
        raise ValueError("missing/extra PPU source telemetry fields")
    return d

def csv_int(v:str,arity:int)->list[int]:
    vals=v.split(",")
    if len(vals)!=arity or not all(re.fullmatch(r"-?\d+",x) for x in vals):
        raise ValueError("malformed original PPU RGB triplet")
    return [int(x) for x in vals]

def inspect(log:str,guest_crcs:list[str])->dict:
    if len(guest_crcs)!=5484 or any(not re.fullmatch(r"0x[0-9a-fA-F]{8}",v) for v in guest_crcs):
        raise ValueError("not a complete source-qualified 2P native guest execution")
    crcsha=sha256(("\n".join(v.lower() for v in guest_crcs)+"\n").encode("ascii"))
    if crcsha!=GUEST_CRC_SHA:
        raise ValueError("full 2P guest CRC history differs from original probe")
    pixels={}
    oam={}
    for line in log.splitlines():
        if line.startswith("UR_QA08_WIN_PIXEL_OWNER"):
            d=fields(line,"UR_QA08_WIN_PIXEL_OWNER",FIELDS)
            try:
                frame,x,y,ppl=[int(d[k]) for k in ("frame","x","raster_y","ppu_line")]
                if ppl!=y+1 or not 0<=x<256 or not 0<=y<224:
                    raise ValueError("PPU source coordinate not physical 256x224")
                k=(frame,x,y)
                if k not in POINTS or k in pixels:
                    raise ValueError("unsolicited/duplicate chosen original PPU pixel")
                pixel=csv_int(d["final"],3)
                if tuple(pixel)==ORIGINAL_RGB[k]:
                    raise ValueError("native pixel mislabeled a known-original mismatch")
                if tuple(pixel)!=POINTS[k]:
                    raise ValueError(f"source pixel {k} drifted from source-qualified Windows frame")
                for f in ("premain","presub","postmath"):
                    rgb=csv_int(d[f],3)
                    if any(not -1<=n<=63 for n in rgb):
                        raise ValueError("malformed native 5-bit prebrightness colour")
                for f in ("main","sub"):
                    if not -1<=int(d[f])<=6:
                        raise ValueError("invalid actual renderer layer enum")
                for f in ("math","window"):
                    if not -1<=int(d[f])<=1:
                        raise ValueError("invalid window/math flag")
                for f in ("obj","obj_cgram_index","obj_word","inidisp",
                          "cgadsub","cgwsel","fixed","tm","ts","obsel"):
                    if not re.fullmatch(r"[0-9a-fA-F]{2,8}",d[f]):
                        raise ValueError("malformed native PPU register/OBJ word")
                pixels[k]=d
            except (ValueError,KeyError) as exc:
                raise ValueError(f"unqualified native pixel owner: {exc}") from exc
        elif line.startswith("UR_QA08_WIN_OAM_LINE"):
            d=fields(line,"UR_QA08_WIN_OAM_LINE",OAM_FIELDS)
            try:
                frame,x,ppl,slot=(int(d[k]) for k in ("frame","x","ppu_line","slot"))
                k=(frame,x,ppl-1)
                if k not in POINTS or frame==1280 or slot not in SLOTS:
                    raise ValueError("wrong PPU frame/line/slot candidate")
                id=(*k,slot)
                if id in oam or any(not re.fullmatch(r"[0-9a-fA-F]{4}",d[f]) for f in ("xy","attrs")):
                    raise ValueError("duplicated/invalid native scanline OAM")
                if not re.fullmatch(r"[0-3]",d["high"]):
                    raise ValueError("invalid native high OAM bit pair")
                oam[id]=d
            except (ValueError,KeyError) as exc:
                raise ValueError(f"unqualified actual source OAM: {exc}") from exc
    if set(pixels)!=set(POINTS):
        raise ValueError("native PPU never visited all 11 source-qualified RGB5 positions")
    wanted={(*k,slot) for k in POINTS if k[0]!=1280 for slot in SLOTS}
    if set(oam)!=wanted:
        raise ValueError("native effective OAM 7-slot read missing or unsolicited")
    pixel_rows=[]
    for (frame,x,y),p in sorted(pixels.items()):
        pixel_rows.append({"native_guest":frame,"x":x,"raster_y":y,
                           "native_rgb8_original_PPU":[*POINTS[frame,x,y]],
                           "original_2014_snes9x_RGB5_expanded":[*ORIGINAL_RGB[frame,x,y]],
                           "resolved_main_layer":int(p["main"]),
                           "resolved_sub_layer":int(p["sub"]),
                           "color_math_enabled":int(p["math"]),
                           "color_window_state":int(p["window"]),
                           "resolved_main_rgb5":csv_int(p["premain"],3),
                           "resolved_sub_rgb5":csv_int(p["presub"],3),
                           "composed_before_brightness_rgb5":csv_int(p["postmath"],3),
                           "native_effective_obj":p["obj"],
                           "native_effective_OBJ_CGRAM_slot":p["obj_cgram_index"],
                           "native_effective_OBJ_colour_word":p["obj_word"],
                           "inidisp":p["inidisp"],"cgadsub":p["cgadsub"],
                           "cgwsel":p["cgwsel"],"fixed":p["fixed"],
                           "main_screen_enabled":p["tm"],"sub_screen_enabled":p["ts"],
                           "obsel":p["obsel"]})
    oam_rows=[]
    for (frame,x,y,slot),row in sorted(oam.items()):
        oam_rows.append({"native_guest":frame,"x":x,"raster_y":y,"OAM_slot":slot,
                         "native_scanline_oam_xy":row["xy"],
                         "native_scanline_oam_tile_attr":row["attrs"],
                         "native_scanline_high_oam_pair":int(row["high"])})
    return {
        "schema":"qa08-native-effective-pixel-OAM-readonly-original-source-points/1",
        "real_native_2p_guest_frames":len(guest_crcs),
        "real_native_2p_guest_crc_sha256":crcsha,
        "logical_PPU_output_dimensions":[256,224],
        "independent_2014_Snes9x_2p_source_ZIP_SHA256":ORIGINAL_SOURCE_ZIP,
        "independent_2p_Windows_original_PPU_ZIP_SHA256":WINDOWS_SOURCE_ZIP,
        "independently_source_qualified_native_pixels":len(pixel_rows),
        "independently_source_qualified_native_scanline_OAM_snapshots":len(oam_rows),
        "native_real_PPU_resolved_pixels":pixel_rows,
        "native_OAM_in_effect_on_selected_lines":oam_rows,
        "original_snes9x_2014_same_field_pixel_priority_proven":False,
        "native_pixel_trace_writes_to_guest_or_renderer":False,
        "original_raster_pixels_repaired":False,
        "release_graphics_accepted":False,
    }


# Four source-comparison windows gold-medal pixels: original source used
# index15 with equal native OAM tile name; Win32 actually composites index14.
# Read actual native raw guest VRAM, host renderVram and OBJ-buffer index.
VRAM_FIELDS=frozenset(("frame","x","raster_y","ppu_line","slot","xoff","yoff",
  "usedcol","usedrow","name","obsel","obsel_bank","tile","wordaddr",
  "guest_w0","guest_w8","render_w0","render_w8","guest_idx","render_idx",
  "actual_obj","actual_cgram","overlay","vram_writes"))
VRAM_COORDS={(4032,225,96,99,"1e6"),(4032,225,120,98,"1e6"),
             (4176,225,96,99,"1e2"),(4176,225,120,98,"1e2")}

def inspect_medal_live_vram(log:str)->dict:
    """Fail-close exact guest/render bitplanes at four *actual* native lines.

    Deliberately does NOT force renderer and physical guest VRAM equivalence
    or expected index15/14: those comparisons are the research result.
    """
    found={}
    if "UR_QA08_WIN_MEDAL_VRAM_REJECT " in log:
        raise ValueError("actual Win32 source PPU rejected live medal VRAM probe")
    for line in log.splitlines():
        if not line.startswith("UR_QA08_WIN_MEDAL_VRAM "):
            continue
        d=fields(line,"UR_QA08_WIN_MEDAL_VRAM",VRAM_FIELDS)
        try:
            frame,x,y,slot=[int(d[k]) for k in ("frame","x","raster_y","slot")]
            key=(frame,x,y,slot,d["name"].lower())
            if key not in VRAM_COORDS or key in found or int(d["ppu_line"])!=y+1:
                raise ValueError("nonregistered/duplicated medal PPU raster frame, slot or tile name")
            if (int(d["xoff"]),int(d["yoff"]))!=(6,8) or (
                int(d["usedcol"]),int(d["usedrow"]))!=(6,8):
                raise ValueError("observed flipped/out-of-bounds sprite texel")
            if (d["obsel"].lower()!="63" or int(d["obsel_bank"],16)!=0x7000 or
                int(d["tile"],16)!=(0xf6 if frame==4032 else 0xf2) or
                int(d["wordaddr"],16)!=(0x7f60 if frame==4032 else 0x7f20)):
                raise ValueError("actual OBJ tile/bank/word address disagrees with source")
            if int(d["overlay"]) not in (0,1) or int(d["vram_writes"])<0:
                raise ValueError("invalid render-VRAM override or guest write counter")
            for prefix in ("guest","render"):
                a,b=(int(d[k],16) for k in (prefix+"_w0",prefix+"_w8"))
                plane=a | b<<16
                bit=1 # xoff=6 -> SNES bit7-6=1
                val=(plane>>bit&1)|(plane>>(bit+7)&2)|(
                    plane>>(bit+14)&4)|(plane>>(bit+21)&8)
                if int(d[prefix+"_idx"])!=val or not 0<=val<=15:
                    raise ValueError("native actual 4bpp planes do not yield their claimed indexed pixel")
            actual=int(d["actual_obj"],16)
            if (actual&255)!=0xde or int(d["actual_cgram"],16)!=0xde:
                raise ValueError("real legacy OBJ is not the independently observed palette5 index14")
            if (int(d["overlay"])==0 and
                any(d["guest_"+field]!=d["render_"+field] for field in
                    ("w0","w8","idx"))):
                raise ValueError("renderVram differs from guest without a host override")
            found[key]={
                "actual_native_guest":frame,"original_2014_callback":frame-1,
                "sampled_xy":[x,y],"source_slot":slot,"native_oam_name9":d["name"].lower(),
                "original_OBJ_palette5_4bpp_index":15,
                "native_actual_effective_OBJ_palette5_4bpp_index":14,
                "native_guest_vram_4bpp_index":int(d["guest_idx"]),
                "native_render_vram_4bpp_index":int(d["render_idx"]),
                "native_guest_vram_words":[d["guest_w0"].lower(),d["guest_w8"].lower()],
                "native_render_vram_words":[d["render_w0"].lower(),d["render_w8"].lower()],
                "native_source_VRAM_word_address":d["wordaddr"].lower(),
                "host_render_VRAM_override_live":bool(int(d["overlay"])),
                "native_total_VRAM_write_count":int(d["vram_writes"]),
                "native_objBuffer_and_decoded_render_VRAM_agree":int(d["render_idx"])==14,
            }
        except (ValueError,KeyError) as exc:
            raise ValueError("invalid native source VRAM/OBJ observation: "+str(exc)) from exc
    if set(found)!=VRAM_COORDS:
        raise ValueError("native VRAM/4bpp source did not visit all four registered medal pixels")
    return {
      "schema":"qa08-real-Win32-2p-live-medal-gold-VRAM-OBJ-index-probe/1",
      "source_exact_two_2P_results_guest_frames":[4032,4176],
      "source_registered_exact_four_pixel_records":[found[k] for k in sorted(found)],
      "observed_actual_Windows_pixel_count":4,
      "original_index15_source_verified_with_separate_2014_archive":True,
      "native_OBJ_index14_source_qualified_from_existing_11_point_PPU":True,
      "source_corresponding_PPU_renderVram_probe_readonly":True,
      "CPU_NMI_writer_phase_and_hardware_DAC_equivalence_accepted":False,
      "native_PPU_corrective_patch_authorized":False,
      "QA08_QA10_release_or_HD_art_accepted":False,
    }


FINISH_RGB_NATIVE = (57,24,0)
FINISH_RGB_ORIGINAL = (49,24,0)
FINISH_GUESTS = (3792,3872)


def inspect_finish_live_pixel_owners(log:str)->dict:
    """Two real live pre-output PPU pixel owners, never reconstructed pixels.

    The independently archived 2014 Snes9x comparison found a single wrong
    RGB5 pixel (121,165) on each guest, with exactly identical red delta.
    Original source layer/priority is still *unobserved*; the native trace
    reads its existing effective compositor values without intervening.
    """
    selected={}
    for line in log.splitlines():
        if not line.startswith("UR_QA08_WIN_FINISH_PIXEL_OWNER "):
            continue
        d=fields(line,"UR_QA08_WIN_FINISH_PIXEL_OWNER",FIELDS)
        try:
            guest,x,y,ppu_line=(
                int(d[k]) for k in ("frame","x","raster_y","ppu_line"))
            if guest not in FINISH_GUESTS or x!=121 or y!=165 or ppu_line!=166:
                raise ValueError("not the independently source-qualified finish pixel")
            if guest in selected:
                raise ValueError("duplicate authentic native 2P finish source pixel")
            if csv_int(d["final"],3)!=list(FINISH_RGB_NATIVE):
                raise ValueError("real native finish pixel changed from its 263-frame source")
            for key in ("premain","presub","postmath"):
                if any(not -1<=v<=63 for v in csv_int(d[key],3)):
                    raise ValueError("non-PPU RGB5 native pixel operands")
            for key in ("main","sub"):
                if not -1<=int(d[key])<=6:
                    raise ValueError("unrecognized live native PPU source layer")
            for key in ("math","window"):
                if not -1<=int(d[key])<=1:
                    raise ValueError("invalid native math/window state")
            for key in ("obj","obj_cgram_index","obj_word","inidisp",
                        "cgadsub","cgwsel","fixed","tm","ts","obsel"):
                if not re.fullmatch(r"[0-9a-fA-F]{2,8}",d[key]):
                    raise ValueError("unqualified native PPU or OBJ register")
            selected[guest]={
                "native_guest":guest,"original_video_callback":guest-1,
                "x":x,"y":y,"native_actual_RGB8":list(FINISH_RGB_NATIVE),
                "original_Snes9x_RGB5_expanded":list(FINISH_RGB_ORIGINAL),
                "native_resolved_main_layer":int(d["main"]),
                "native_resolved_sub_layer":int(d["sub"]),
                "native_color_math_enabled":int(d["math"]),
                "native_color_window_state":int(d["window"]),
                "native_main_RGB5":csv_int(d["premain"],3),
                "native_sub_RGB5":csv_int(d["presub"],3),
                "native_postmath_RGB5":csv_int(d["postmath"],3),
                "native_effective_obj":d["obj"],
                "native_effective_obj_CGRAM_index":d["obj_cgram_index"],
                "native_effective_obj_CGRAM_word":d["obj_word"],
                "inidisp":d["inidisp"],"cgadsub":d["cgadsub"],
                "cgwsel":d["cgwsel"],"fixed":d["fixed"],
                "tm":d["tm"],"ts":d["ts"],"obsel":d["obsel"],
                "source_original_PPU_layers_proven":False,
                "physical_SNES_DAC_equivalence_proven":False,
                "native_pixel_mismatches_repaired":False
            }
        except (ValueError, KeyError) as exc:
            raise ValueError("unqualified real native finish PPU pixel owner: "+str(exc)) from exc
    if set(selected)!=set(FINISH_GUESTS):
        raise ValueError("missing two authentic source-isolated finish PPU owners")
    return {
        "schema":"qa08-live-native-finishing-pixel-PPU-layer-observer/1",
        "actual_source_qualified_win32_guest_2p_frames":[*FINISH_GUESTS],
        "pixel_256x224":[121,165],
        "strict_original_Snes9x_RGB5_expanded":[*FINISH_RGB_ORIGINAL],
        "strict_actual_Windows_RGB8":[*FINISH_RGB_NATIVE],
        "read_only_native_live_PPU_effective_pixels":[selected[n] for n in FINISH_GUESTS],
        "observer_did_not_modify_guest_or_PPU":True,
        "original_live_same_scanline_PPU_priority_proven":False,
        "native_vs_original_hardware_DAC_math_order_proven":False,
        "release_gate_accepted":False
    }

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("exe","rom","script","out"):
        ap.add_argument("--"+name,required=True,type=Path)
    ap.add_argument("--timeout",type=int,default=300)
    ap.add_argument("--collect-2p-fullroute",action="store_true",
                    help="observe 263 full 256x224 source frames and bounded PPU ports in the same native route")
    a=ap.parse_args()
    for file,hash_value,label in ((a.rom,ROM_SHA,"USA ROM"),(a.script,ROUTE_SHA,"2P route")):
        if sha256(file.read_bytes())!=hash_value:
            ap.error("wrong pinned original "+label)
    if a.out.exists():
        ap.error("refusing to overwrite source result root")
    a.out.mkdir(parents=True)
    # One real Windows process simultaneously owns both the 11 selected
    # pixel/OAM observations and (only when explicitly selected) the 263
    # complete Original PPU source fields + bounded port/register chronology.
    # This avoids a second 5484-frame guest run and cannot rewrite PPU pixels.
    enabled={
        "UR_QA08_WINDOWS_PIXEL_OWNER_TRACE":"1",
        "UR_QA08_WINDOWS_OAM_PORT_TRACE":"1",
    }
    if a.collect_2p_fullroute:
        enabled["UR_QA08_WINDOWS_FINISH_PIXEL_OWNER_TRACE"]="1"
        enabled["UR_QA08_WINDOWS_MEDAL_VRAM_TRACE"]="1"
        source_dir=a.out/"source"
        source_dir.mkdir()
        enabled.update({
            "UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR":str(source_dir.resolve()),
            "UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE":"twoplayer-fullroute",
            "UR_QA08_WINDOWS_PPU_STATE_TRACE":"1",
            "UR_QA08_WINDOWS_CGRAM_PORT_TRACE":"1",
            "UR_QA08_WINDOWS_INIDISP_PORT_TRACE":"1",
            "UR_QA08_WINDOWS_HDMA_FIRSTLINE_TRACE":"1",
        })
    previous={key:os.environ.get(key) for key in enabled}
    os.environ.update(enabled)
    try:
        crcs,log=run_route(a.exe.resolve(),a.rom.resolve(),a.script.resolve(),
                           a.out,pause=False,video="windows",timeout=a.timeout)
    finally:
        for key,value in previous.items():
            if value is None:
                os.environ.pop(key,None)
            else:
                os.environ[key]=value
    # Retain a bounded graphics-only trace even if an assertion rejects it.
    # Never archive user files, ROM/SRAM, personal profiles or full commands.
    diagnostic=[row for row in log.splitlines()
                if row.startswith(("UR_QA08_WIN_PIXEL_OWNER ",
                                   "UR_QA08_WIN_FINISH_PIXEL_OWNER ",
                                   "UR_QA08_WIN_MEDAL_VRAM ",
                                   "UR_QA08_WIN_OAM_LINE ",
                                   "UR_QA08_WIN_OAM_PORT "))]
    (a.out/"qa08-effective-pixel-source-log.txt").write_text(
        "\n".join(diagnostic)+"\n",encoding="utf-8")
    result=inspect(log,crcs)
    result["verified_same_actual_Windows_executable"]=sha256(a.exe.read_bytes())
    result["verified_original_2P_script_SHA256"]=ROUTE_SHA
    if a.collect_2p_fullroute:
        try:
            from tools import qa08_windows_full_twoplayer_source_coverage as fullroute
        except ImportError:
            import qa08_windows_full_twoplayer_source_coverage as fullroute
        # Fail closed on all 263 actual 256x224 post-PPU source fields, their
        # logged real guest labels and complete source CRC. Do not manufacture
        # absent video callbacks or infer reference/hardware equivalence.
        capture=fullroute.inspect(source_dir,log,crcs)
        if (capture["actual_native_guest_CRC_sha256"]!=GUEST_CRC_SHA
            or capture["actual_native_simulations"]!=5484
            or capture["actual_source_count"]!=263):
            raise ValueError("same-process full-route visual/guest witness diverged")
        capture["read_only_native_PPU_registers"]=fullroute.inspect_native_ppu_registers(log)
        capture["read_only_native_CGRAM_port_writer_chronology"]=fullroute.inspect_native_cgram_port_history(log)
        capture["read_only_native_INIDISP_2100_write_chronology"]=fullroute.inspect_native_inidisp_port_history(log)
        capture["read_only_native_HDMA7_firstline"]=fullroute.inspect_native_channel7_firstline(log)
        capture["actual_windows_PE_sha256"]=result["verified_same_actual_Windows_executable"]
        capture["actual_two_pad_route_sha256"]=ROUTE_SHA
        capture["same_unmodified_exe_and_native_guest_execution_as_pixel_owner"]=True
        capture["original_snes9x_effective_OBJ_BG_math_priority_accepted"]=False
        (a.out/"qa08-windows-2p-fullroute.json").write_text(
            json.dumps(capture,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        prefixes=("UR_QA08_WIN_PPU_STATE ","UR_QA08_WIN_CGRAM_WRITE ",
                  "UR_QA08_WIN_INIDISP_WRITE ","UR_QA08_WIN_HDMA7 ",
                  "UR_QA08_WINDOWS_ORIGINAL_SOURCE ")
        (a.out/"qa08-native-ppu-source-phase-log.txt").write_text(
            "\n".join(line for line in log.splitlines() if line.startswith(prefixes))+"\n",
            encoding="utf-8")
        result["bounded_two_finish_live_pixel_owners"]=inspect_finish_live_pixel_owners(log)
        result["bounded_gold_medal_live_VRAM_and_OBJ_indexes"]=inspect_medal_live_vram(log)
        (a.out/"qa08-native-live-gold-medal-VRAM-words.json").write_text(
            json.dumps(result["bounded_gold_medal_live_VRAM_and_OBJ_indexes"],
                       indent=2,sort_keys=True)+"\\n",encoding="utf-8")
        result["qualified_263_frame_source_PPU_in_same_native_process"]=True
        result["same_real_Windows_process_CGRAM_ports_2100_HDMA7_observed"]=True
        print("QA08_SAME_ROUTE_2P_PPU full_guest=5484 source_256x224=263 "
              "original_CPU_phase_and_physical_pixels=UNACCEPTED")
    (a.out/"qa08-native-effective-pixel-owner.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA08_PIXEL_OWNER real_original_win32_frames=5484 source_positions=11 "
          "native_OAM_slots_by_line=70 no_pixel_edits=1 no_release_gate=1")

if __name__=="__main__":
    main()
