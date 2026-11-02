#!/usr/bin/env python3
"""Recover exact 4bpp palette-index roles behind authenticated ROM source PNGs.

The existing ROM composer already decodes each 4bpp tile and then maps index
to RGB; its published source corpus retains only RGBA. This read-only audit
recovers the INDEX plane from the SAME composer inputs and proves its RGBA
round-trip on every one of the 59 registered source representations. It does
not assert that an index labels one physical fork/hub/spoke in 3D.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

try:
    from tools.extract_racer_presentation_family import (
        extract_frame, compose_racer_staging, decode_4bpp_tile,
        piece_source_tile, rgba_palette, rasterize_composed_player_rgba,
        RASTER_WIDTH, RASTER_HEIGHT, RASTER_TILE_OFFSET,
    )
    from tools.art.audit_art4k_original_wheel_ring import (
        validate_corpus_and_measure, CORPUS_MANIFEST_SHA256,
        ORIGINAL_ROM_SHA256,
    )
    from tools.art.audit_original_racer_colourway import classify_source_chroma
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from extract_racer_presentation_family import (
        extract_frame, compose_racer_staging, decode_4bpp_tile,
        piece_source_tile, rgba_palette, rasterize_composed_player_rgba,
        RASTER_WIDTH, RASTER_HEIGHT, RASTER_TILE_OFFSET,
    )
    from audit_art4k_original_wheel_ring import (
        validate_corpus_and_measure, CORPUS_MANIFEST_SHA256,
        ORIGINAL_ROM_SHA256,
    )
    from audit_original_racer_colourway import classify_source_chroma
    from no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-ROM-4BPP-PALETTE-INDEX-PROVENANCE/1"
REGISTRY_KEYS=("p1_primary","p2_primary","p1_companion","p2_companion")
SAMPLE_RADIUS=7


def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def parse_id(value)->int:
    if not isinstance(value,str) or not value.startswith("0x"):
        raise ValueError("original source frame/asset ID must be explicit hexadecimal")
    number=int(value,16)
    if not 0<=number<=65535:
        raise ValueError("original source frame ID out of range")
    return number


def composition_for_registry_entry(rom:bytes,entry:dict)->dict:
    g=entry["composition_guards"]
    if not all(key in g for key in (*REGISTRY_KEYS,
        "p1_selector","p2_selector","p1_companion_gate_word","p2_companion_gate_word")):
        raise ValueError("original source representation missing composition guards")
    frames={key:extract_frame(rom,parse_id(g[key])) for key in REGISTRY_KEYS}
    for key in ("p1_selector","p2_selector"):
        if type(g[key]) is not int or not 0<=g[key]<=3:
            raise ValueError("invalid original occupancy selector")
    return compose_racer_staging(
        frames["p1_primary"],frames["p2_primary"],
        frames["p1_companion"],frames["p2_companion"],
        p1_selector=g["p1_selector"],p2_selector=g["p2_selector"],
        p1_companion_enabled=parse_id(g["p1_companion_gate_word"])!=0,
        p2_companion_enabled=parse_id(g["p2_companion_gate_word"])!=0)


def rasterize_composed_palette_indices(rom:bytes,composition:dict,player:str,
                                      *,hflip:bool=False,vflip:bool=False)->bytes:
    """Exact source composer cell ownership; index zero stays transparent.

    Both source tile layers and overrides are consumed in composition order,
    including transparent pixels that overwrite a preceding cell.
    """
    if player not in ("p1","p2") or type(hflip) is not bool or type(vflip) is not bool:
        raise ValueError("unsupported original source player or 2D reflection")
    if (RASTER_WIDTH,RASTER_HEIGHT)!=(64,64):
        raise ValueError("original source raster layout changed")
    data=bytearray(RASTER_WIDTH*RASTER_HEIGHT)
    ox,oy=RASTER_TILE_OFFSET
    for cell in composition["cells"]:
        if cell["player"]!=player or cell["word_hex"] is None:
            continue
        raw,_=piece_source_tile(rom,parse_id(cell["word_hex"]))
        tile=decode_4bpp_tile(raw)
        gx=ox+int(cell["minor_slot"])
        gy=oy+int(cell["major_slot"])
        for ty,row in enumerate(tile):
            for tx,index in enumerate(row):
                x=gx*8+tx;y=gy*8+ty
                if hflip:x=63-x
                if vflip:y=63-y
                if not(0<=x<64 and 0<=y<64 and 0<=index<16):
                    raise ValueError("invalid tile cell or palette index")
                data[y*64+x]=index
    return bytes(data)


def palette_disk_census(indices:bytes,centres:list,palette:list)->dict:
    """Per-index wheel-disc min/max counts, all source ring ties retained."""
    if (not isinstance(indices,bytes) or len(indices)!=4096 or
            any(v>15 for v in indices) or len(palette)<16 or
            not isinstance(centres,list) or not centres):
        raise ValueError("invalid exact 64x64 index plane, palette or wheel candidates")
    histogram=Counter(indices)
    if histogram[0]+sum(histogram[i] for i in range(1,16))!=4096:
        raise ValueError("palette index census incomplete")
    per_index={}
    for i in range(1,16):
        total=histogram[i]
        if not total:
            continue
        if len(palette[i])!=4 or palette[i][3]!=255:
            raise ValueError("unexpected opaque 4bpp index palette")
        points=[(j%64,j//64) for j,v in enumerate(indices) if v==i]
        by_centre=[]
        for centre in centres:
            if (not isinstance(centre,(list,tuple)) or len(centre)!=3 or
                    any(type(v) is not int for v in centre)):
                raise ValueError("bad original ring centre")
            cx,cy,r=centre
            if not(0<=cx<64 and 0<=cy<64 and r==SAMPLE_RADIUS):
                raise ValueError("not an original source 7px wheel ring")
            by_centre.append(sum(
                (x-cx)**2+(y-cy)**2<=r*r for x,y in points))
        colour=palette[i]
        per_index[str(i)]={
            "original_4bpp_palette_index":i,
            "source_rgba8":list(colour),
            "source_high_chroma_heuristic":classify_source_chroma(tuple(colour[:3])),
            "opaque_source_pixels":total,
            "source_wheel_disc_pixels_min":min(by_centre),
            "source_wheel_disc_pixels_max":max(by_centre),
            "unknown_source_physical_part":True,
        }
    return {"opaque_palette_indices":per_index,
            "all_source_wheel_centre_candidates":len(centres),
            "opaque_source_pixels":4096-histogram[0],
            "source_3d_part_identity_verified":False}


def original_source_audit(rom_path:Path,registry_path:Path,corpus_zip:Path)->dict:
    rom=rom_path.read_bytes()
    if digest(rom)!=ORIGINAL_ROM_SHA256:
        raise ValueError("canonical original USA ROM SHA mismatch")
    frozen=validate_corpus_and_measure(corpus_zip)
    if (frozen.get("source_corpus_manifest_sha256")!=CORPUS_MANIFEST_SHA256
            or frozen.get("original_usa_rom_sha256")!=ORIGINAL_ROM_SHA256):
        raise ValueError("source-composed original PNG manifest changed")
    import zipfile
    with zipfile.ZipFile(corpus_zip) as archive:
        manifest=json.loads(archive.read("source-corpus.json"))
    source_bytes=registry_path.read_bytes()
    if digest(source_bytes)!=manifest["source_registry_sha256"]:
        raise ValueError("current registry differs from authenticated source ROM corpus")
    entries=json.loads(source_bytes)["entries"]
    ids=[x["representation_id"] for x in entries]
    if len(ids)!=len(set(ids)):
        raise ValueError("ambiguous original source composition registry")
    by_id={x["representation_id"]:x for x in entries}
    originals=manifest["source_representations"]
    if len(originals)!=59 or not set(originals).issubset(by_id):
        raise ValueError("original source registered representations missing")
    src_rgba={x["source_rgba_sha256"]:x for x in frozen["images"]}
    by_shape=defaultdict(set);by_rgba=defaultdict(set);rows=[]
    for identity,record in sorted(originals.items()):
        entry=by_id[identity]
        if entry["player"]!=record["player"]:
            raise ValueError("registered source player vs corpus mismatch")
        composition=composition_for_registry_entry(rom,entry)
        plane=rasterize_composed_palette_indices(rom,composition,entry["player"])
        palette=rgba_palette(rom,parse_id(entry["palette_asset_id"]))
        if len(palette)<16 or len(palette[0])!=4 or palette[0][3]!=0:
            raise ValueError("source palette zero lost transparency")
        rgba=b"".join(bytes(palette[v]) for v in plane)
        independent=rasterize_composed_player_rgba(
            rom,composition,entry["player"],parse_id(entry["palette_asset_id"]))
        if rgba!=independent or digest(rgba)!=record["source_rgba_sha256"]:
            raise ValueError("original source index plane not byte-identical to ROM PNG")
        alpha=bytes(palette[v][3] for v in plane)
        mask=bytes(int(v!=0) for v in plane)
        if (digest(alpha)!=record["source_alpha_sha256"] or
                digest(mask)!=record["source_binary_mask_sha256"]):
            raise ValueError("palette index mask differs from source alpha")
        source=src_rgba.get(record["source_rgba_sha256"])
        if source is None or source["source_binary_mask_sha256"]!=record["source_binary_mask_sha256"]:
            raise ValueError("source ring evidence lacks this original composition")
        centres=source["2d_ring_candidate"]["best_candidate_centres_xy_radius_logical_px"]
        census=palette_disk_census(plane,centres,palette)
        rows.append({
            "registered_original_representation_id":identity,
            "source_player":entry["player"],
            "source_palette_asset_id":entry["palette_asset_id"],
            "source_rgba_sha256":record["source_rgba_sha256"],
            "source_binary_mask_sha256":record["source_binary_mask_sha256"],
            "original_4bpp_index_plane_sha256":digest(plane),
            "palette_index_census":census,
        })
        by_shape[record["source_binary_mask_sha256"]].add(digest(plane))
        by_rgba[record["source_rgba_sha256"]].add(digest(plane))
    if len(rows)!=59 or len(by_shape)!=35 or len(by_rgba)!=41:
        raise ValueError("original ROM/source census not exact")
    return {
        "schema":SCHEMA,"original_USA_ROM_sha256":ORIGINAL_ROM_SHA256,
        "canonical_original_source_corpus_sha256":CORPUS_MANIFEST_SHA256,
        "original_registry_sha256":manifest["source_registry_sha256"],
        "source_kind":"ROM-composed authored registry 4bpp index planes, not live PPU frames",
        "actual_original_4bpp_tile_indices_reconstructed":True,
        "independent_source_emulator_PPU_timing_observed":False,
        "source_index_to_1994_physical_part_correspondence_verified":False,
        "registered_original_representations":len(rows),
        "unique_source_RGBA_images":len(by_rgba),
        "unique_source_binary_silhouettes":len(by_shape),
        "same_rgba_with_multiple_index_planes":sum(len(v)>1 for v in by_rgba.values()),
        "same_binary_mask_with_multiple_index_planes":sum(len(v)>1 for v in by_shape.values()),
        "per_original_representation":rows,
        "owner_likeness_approved":False,
        "shipping_art_approved":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--registry",type=Path,required=True)
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    result=original_source_audit(x.rom,x.registry,x.source_zip)
    publish_text_once(x.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="per_original_representation"},
                     indent=2,sort_keys=True))


if __name__=="__main__":
    main()
