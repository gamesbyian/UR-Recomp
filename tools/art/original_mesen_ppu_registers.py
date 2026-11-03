"""Source-pinned MesenCE SNES PPU register and 128 OBJ size witness.

Read-only and intentionally narrower than an original visible-sprite mask.
The MesenCE Lua emu.getState() map omits some internal scanout variables;
this decoder must not call their absence an original draw-phase observation.

The mode/width/height tables and register write bounds come directly from
pinned MesenCE Core/SNES/SnesPpu.cpp at a60e79feb4d6dcced5922d636f9211837d01e381.
"""
from __future__ import annotations
import hashlib
import json

SCHEMA="UR-ART4K-MESEN-SOURCE-PPU-OBJ-CONFIG/1"
PINNED_MESENCE_REVISION="a60e79feb4d6dcced5922d636f9211837d01e381"
W=(8,8,8,16,16,32,16,16,16,32,64,32,64,64,32,32)
H=(8,8,8,16,16,32,32,32,16,32,64,32,64,64,64,32)

REQUIRED_INTS={
    "ppu.oammode":(0,7),
    "ppu.oambaseaddress":(0,0xE000),
    "ppu.oamaddressoffset":(0x1000,0x4000),
    "ppu.oamramaddress":(0,0x1FF),
    "ppu.bgmode":(0,7),
    "ppu.screenbrightness":(0,15),
    "ppu.mainscreenlayers":(0,63),
    "ppu.subscreenlayers":(0,63),
    "ppu.framecount":(0,10_000_000),
    "ppu.scanline":(-1,400),
}
REQUIRED_BOOLEANS=(
    "ppu.forcedblank",
    "ppu.enableoampriority",
    "ppu.hiresmode",
    "ppu.screeninterlace",
    "ppu.objinterlace",
    "ppu.overscanmode",
)


def obj_pixel_dimensions(oam_mode:int,large:bool)->tuple[int,int]:
    """Exact MesenCE source-pinned OAM small/large OBJ width and height."""
    if type(oam_mode) is not int or not 0<=oam_mode<8 or type(large) is not bool:
        raise ValueError("original source OBJ size mode or high-table bit malformed")
    mode=oam_mode+(8 if large else 0)
    return (W[mode],H[mode])


def extract_serialized_ppu_registers(state:dict)->dict:
    """Source MesenCE Serializer Map keys, with fail-closed exact types.

    Global live console state may include unrelated CPU/WRAM fields; only a
    fixed whitelist of original source PPU config is returned.
    """
    if not isinstance(state,dict) or len(state)>20_000:
        raise ValueError("original executed source state mapping invalid")
    required={}
    for key,(low,high) in REQUIRED_INTS.items():
        value=state.get(key)
        if type(value) is not int or not low<=value<=high:
            raise ValueError("original Mesen serialized PPU integer field missing/out of bounds: "+key)
        required[key]=value
    for key in REQUIRED_BOOLEANS:
        value=state.get(key)
        if type(value) is not bool:
            raise ValueError("original Mesen serialized PPU boolean field missing: "+key)
        required[key]=value
    for axis in ("hscroll","vscroll"):
        for n in range(4):
            key=f"ppu.layers[{n}].{axis}"
            value=state.get(key)
            if type(value) is not int or not 0<=value<=0x1FFF:
                raise ValueError("original Mesen background layer source scroll missing: "+key)
            required[key]=value
    if required["ppu.oambaseaddress"]%0x2000:
        raise ValueError("Mesen original OAM/OBJ VRAM base must be 8192-byte aligned")
    if required["ppu.oamaddressoffset"]%0x1000:
        raise ValueError("Mesen original OBJ table offset must be 4096-byte aligned")
    mode=required["ppu.oammode"]
    result={
        "schema":SCHEMA,
        "source_emulator_revision":PINNED_MESENCE_REVISION,
        "source_mesen_flat_state_key_class":"ppu.* from emu.getState Serializer Map",
        "source_registers":dict(sorted(required.items())),
        "original_16bit_OBJ_small_dimensions_pixels":list(obj_pixel_dimensions(mode,False)),
        "original_16bit_OBJ_large_dimensions_pixels":list(obj_pixel_dimensions(mode,True)),
        "source_state_whitelist_sha256":hashlib.sha256(
            json.dumps(required,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest(),
        "original_PPUSCANOUT_phase_independently_verified":False,
        "source_1994_racer_OBJ_pixel_visibility_verified":False,
        "source_original_3d_anatomical_part_correspondence_verified":False,
        "owner_likeness_approved":False,
    }
    return result


def add_oam_pixel_sizes(source_oam:bytes,ppu:dict)->dict:
    """128 original raw OBJ size choices; NEVER imply these appeared onscreen."""
    if not isinstance(ppu,dict) or ppu.get("schema")!=SCHEMA or not isinstance(ppu.get("source_registers"),dict):
        raise ValueError("original PPU config witness invalid")
    from tools.art.audit_original_mesen_oam_descriptors import decode_oam
    oam=decode_oam(source_oam)
    mode=ppu["source_registers"]["ppu.oammode"]
    size=[
        {
            "source_oam_slot":row["oam_slot"],
            "source_oam_high_table_large_bit":row["source_obj_size_select_large"],
            "source_OBJ_width":obj_pixel_dimensions(mode,row["source_obj_size_select_large"])[0],
            "source_OBJ_height":obj_pixel_dimensions(mode,row["source_obj_size_select_large"])[1],
            "source_OBJ_X_signed9":row["source_oam_x_signed9"],
            "source_OBJ_Y_raw8":row["source_oam_y_raw8"],
            "original_visible_pixel_ownership_verified":False,
        } for row in oam
    ]
    return {
        "original_source_OAM_slots":len(size),
        "original_size_config_for_each_source_OAM_slot":size,
        "original_OAM_to_visible_source_OBJ_pixels_verified":False,
    }
