#!/usr/bin/env python3
"""Rejoin 40 real Mesen source 4bpp planes to frozen 35-plane original tile ancestry.

No 3D pose labels or camera/geometry fitting. Verifies five immutable original
source archives and their internal SHA, reconstitutes historic 59 4bpp planes
from SHA-verified source images + independently obtained palette-index maps,
reproduces 170 historical tile-sharing edges, then checks 40 new original
executed-frame OAM/VRAM-derived source sprites. Pillow optional and offline.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import zipfile

from tools.art.audit_original_mesen_sparse_pose_correspondence import (
    SOURCE_ZIP_SHA, TICKS, audit_source, validate_receipt,
)
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-LIVE40-FROZEN-ORIGINAL-SOURCE-TILE-CONTENT-NOVELTY/1"
CORPUS_SHA="82e913865dfb5ab7936d27257651efa5b6d4ae1906eb1b33c2ea87fe1366fc9c"
INDEX_SHA="82775dd1fb96486a61d4e93f73ea081ef3a19ddf3cb34a22cd82084efcfc1d34"
TILE_SHA="aed5a4a0a206800f335001f24c664b4fa5d243ddffd9ec6dd346f14913aa63fc"
HOLDOUT_SHA="a6622c7b37159a1a558868b2908f1d95950f6c6bf9f1d42aa5230d06cd2b587a"
CORPUS_JSON_SHA="e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e"
INDEX_JSON_SHA="b6f59fc5f9030b44ca9345bf308e5df83901f8b9534a6f33b215fa39f8e3079e"
TILE_JSON_SHA="cccb78328307003b3f8148aa20ef7cca27c905e77610be2b3ffd1aa7e7d5f33f"
HOLDOUT_JSON_SHA="22cc8cd44d3e33ea535494ce12f12ae62ec536c60344fe3c4460d5d74ee5e178"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
MAX_SOURCE_ZIP=1_000_000
MAX_HISTORY_ZIP=150_000


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def exact_tiles(plane:bytes)->set[bytes]:
    """Content identity is 8x8 index-valued sprite tiles; discard blank tile."""
    if not isinstance(plane,bytes) or len(plane)!=4096 or any(v>15 for v in plane):
        raise ValueError("64x64 original source 4bpp index plane required")
    tiles=set()
    for tile_y in range(8):
        for tile_x in range(8):
            data=b"".join(plane[(tile_y*8+y)*64+tile_x*8:
                               (tile_y*8+y)*64+tile_x*8+8]
                          for y in range(8))
            if any(data):
                tiles.add(data)
    return tiles


def components(rows:list[dict])->list[dict]:
    """Group novel source planes by transitive shared exact nonblank 8x8 bytes."""
    if not isinstance(rows,list) or not rows:
        raise ValueError("nonempty novel original 4bpp source tiles required")
    parent=list(range(len(rows)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]
            i=parent[i]
        return i
    seen=set()
    for i,item in enumerate(rows):
        identity=(item.get("tick"),item.get("racer"))
        if identity in seen or (type(identity[0]) is not int or
                               identity[1] not in ("blue","red") or
                               not isinstance(item.get("tiles"),set) or
                               not item["tiles"] or
                               any(type(v) is not bytes or len(v)!=64 or not any(v)
                                   for v in item["tiles"]) or
                               type(item.get("shares_fit")) is not bool or
                               type(item.get("shares_withheld")) is not bool):
            raise ValueError("malformed novel original source tile component")
        seen.add(identity)
        for j in range(i):
            if item["tiles"] & rows[j]["tiles"]:
                parent[root(i)]=root(j)
    groups=defaultdict(list)
    for i,item in enumerate(rows):
        groups[root(i)].append(item)
    result=[]
    for group in groups.values():
        identities=sorted([[x["tick"],x["racer"]] for x in group])
        result.append({
            "original_ticks_and_racers": identities,
            "has_exact_nonblank_tile_shared_with_precommitted_fit":
                any(x["shares_fit"] for x in group),
            "has_exact_nonblank_tile_shared_with_precommitted_withheld":
                any(x["shares_withheld"] for x in group),
        })
    return sorted(result,key=lambda x:(-len(x["original_ticks_and_racers"]),
                                       x["original_ticks_and_racers"]))


def pinned_zip(path:Path,expected_sha:str,max_bytes:int)->zipfile.ZipFile:
    if (not path.is_file() or path.stat().st_size>max_bytes or
            sha(path.read_bytes())!=expected_sha):
        raise ValueError("not exact historically authenticated original archive")
    return zipfile.ZipFile(path)


def historical_original_tiles(corpus:zipfile.ZipFile,index:zipfile.ZipFile,
                              lineage:zipfile.ZipFile,holdout:zipfile.ZipFile):
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("offline historical original PNG index replay requires Pillow") from exc
    def checked(archive,name,expected):
        payload=archive.read(name)
        if sha(payload)!=expected:
            raise ValueError("original historic JSON SHA differs")
        return json.loads(payload)
    src=checked(corpus,"source-corpus.json",CORPUS_JSON_SHA)
    idx=checked(index,"art4k-index-provenance.json",INDEX_JSON_SHA)
    tile=checked(lineage,"art4k-original-tile-lineage.json",TILE_JSON_SHA)
    roles=checked(holdout,"frozen-original-tile-disjoint-holdout.json",HOLDOUT_JSON_SHA)
    if (src.get("source_rom_sha256")!=ROM_SHA or
            idx.get("original_USA_ROM_sha256")!=ROM_SHA or
            tile.get("source_rom_sha256")!=ROM_SHA or
            roles.get("original_source_rom_sha256")!=ROM_SHA or
            idx.get("canonical_original_source_corpus_sha256")!=CORPUS_JSON_SHA or
            len(idx.get("per_original_representation",[]))!=59):
        raise ValueError("source authentic original archive identities differ")
    planes={}
    unique_ids=set()
    for entry in idx["per_original_representation"]:
        rid=entry["registered_original_representation_id"]
        if rid in unique_ids or rid not in src["source_representations"]:
            raise ValueError("duplicate/missing original source representation")
        unique_ids.add(rid)
        rec=src["source_representations"][rid]
        png=corpus.read(rec["local_file"])
        if sha(png)!=rec["local_png_sha256"]:
            raise ValueError("historic original source PNG SHA changed")
        with Image.open(io.BytesIO(png)) as image:
            if image.size!=(64,64):
                raise ValueError("historic original image size changed")
            rgba=image.convert("RGBA").tobytes()
        if sha(rgba)!=rec["source_rgba_sha256"] or sha(rgba)!=entry["source_rgba_sha256"]:
            raise ValueError("historical original source RGBA SHA changed")
        named=entry["palette_index_census"]["opaque_palette_indices"]
        palette={}
        counts=Counter()
        for key,value in named.items():
            colour=tuple(value["source_rgba8"])
            indexvalue=int(key)
            if (indexvalue not in range(1,16) or len(colour)!=4 or
                    colour[3]!=255 or colour in palette or
                    value["original_4bpp_palette_index"]!=indexvalue):
                raise ValueError("ambiguous original 4bpp palette RGB -> index mapping")
            palette[colour]=indexvalue
        plane=bytearray()
        for start in range(0,len(rgba),4):
            colour=tuple(rgba[start:start+4])
            if colour[3]==0:
                plane.append(0)
            elif colour in palette:
                plane.append(palette[colour])
                counts[palette[colour]]+=1
            else:
                raise ValueError("original PNG contains unregistered palette colour")
        for key,value in named.items():
            if counts[int(key)]!=value["opaque_source_pixels"]:
                raise ValueError("historic original palette index pixel census changed")
        raw=bytes(plane)
        identity=sha(raw)
        if identity!=entry["original_4bpp_index_plane_sha256"]:
            raise ValueError("historic original source 4bpp plane SHA changed")
        if identity in planes and planes[identity]!=raw:
            raise ValueError("historical source 4bpp hash collision")
        planes[identity]=raw
    if set(planes)!=set(tile["per_original_index_plane"]) or len(planes)!=35:
        raise ValueError("not the historical 35 original source index planes")
    content={key:exact_tiles(value) for key,value in planes.items()}
    for key,record in tile["per_original_index_plane"].items():
        if len(content[key])!=record["distinct_nonblank_tile_contents"]:
            raise ValueError("historical original tile count differs")
    payload_users=defaultdict(set)
    for key,tiles in content.items():
        for payload in tiles:payload_users[payload].add(key)
    if (len(payload_users)!=250 or
            tile.get("unique_exact_8x8_tile_payloads")!=251 or
            sum(len(users)>1 for users in payload_users.values())!=62):
        raise ValueError("historical original tile reuse census differs")
    edges={}
    for i,a in enumerate(sorted(content)):
        for b in sorted(content)[i+1:]:
            count=len(content[a]&content[b])
            if count:edges[(a,b)]=count
    expected={(v["left_source_index_sha256"],v["right_source_index_sha256"]):
              v["shared_nonblank_exact_tile_contents"]
              for v in tile["shared_exact_opaque_tile_pairs"]}
    if len(edges)!=170 or edges!=expected:
        raise ValueError("historical original 170 shared-tile edges disagree")
    fit=set(roles["original_fitting_index_plane_shas"])
    withheld=set(roles["original_withheld_index_plane_shas"])
    strict=set(roles["fully_tile_disjoint_original_withheld_index_plane_shas"])
    if (len(fit)!=16 or len(withheld)!=19 or len(strict)!=6 or
            fit|withheld!=set(planes) or fit&withheld or
            not strict.issubset(withheld) or
            any(content[a]&content[b] for a in fit for b in strict)):
        raise ValueError("historical original 16/19/6 role split changed")
    return content,fit,withheld,strict


def evaluate(live_zip:Path, historical_corpus_zip:Path,index_zip:Path,
             tile_zip:Path,holdout_zip:Path,receipt_path:Path)->dict:
    receipt=json.loads(receipt_path.read_text())
    validate_receipt(receipt)
    original=audit_source(live_zip,receipt)
    if (original["actual_source_zip_sha256"]!=SOURCE_ZIP_SHA or
            original["source_pixel_accounting"]!=
            {"opaque":12937,"exact":12416,"red_plus_13":521}):
        raise ValueError("original Mesen screen/PPU 20-tick pixel proof missing")
    with (pinned_zip(historical_corpus_zip,CORPUS_SHA,MAX_HISTORY_ZIP) as historical,
          pinned_zip(index_zip,INDEX_SHA,MAX_HISTORY_ZIP) as indices,
          pinned_zip(tile_zip,TILE_SHA,MAX_HISTORY_ZIP) as lineage,
          pinned_zip(holdout_zip,HOLDOUT_SHA,MAX_HISTORY_ZIP) as roles,
          pinned_zip(live_zip,SOURCE_ZIP_SHA,MAX_SOURCE_ZIP) as live):
        old,fit,withheld,strict=historical_original_tiles(
            historical,indices,lineage,roles)
        fit_tiles=set().union(*(old[k] for k in fit))
        withheld_tiles=set().union(*(old[k] for k in withheld))
        strict_tiles=set().union(*(old[k] for k in strict))
        historic_tiles=fit_tiles|withheld_tiles
        rows=[]
        novel=[]
        for sample in receipt["samples"]:
            tick=sample["tick"]
            oam=decode_oam(live.read(f"frame-{tick:06d}-oam.bin"))
            vram=live.read(f"frame-{tick:06d}-vram.bin")
            cgram=live.read(f"frame-{tick:06d}-cgram.bin")
            for racer,slot in (("blue",96),("red",97)):
                obj=decode_source_obj(oam[slot],vram,cgram,
                     oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
                plane_sha=sha(obj["plane"])
                tiles=exact_tiles(obj["plane"])
                if obj["opaque_count"]!=sample[racer]["opaque"] or not tiles:
                    raise ValueError("original OAM source sprite identity changed")
                role=("fit" if plane_sha in fit else
                      "withheld" if plane_sha in withheld else "unclassified")
                row={
                    "tick":tick,"racer":racer,"original_source_index_plane_sha256":plane_sha,
                    "frozen_source_role":role,
                    "distinct_nonblank_8x8_source_tiles":len(tiles),
                    "historical_fit_planes_sharing_nonblank_tile":
                        sum(bool(tiles&old[k]) for k in fit),
                    "historical_withheld_planes_sharing_nonblank_tile":
                        sum(bool(tiles&old[k]) for k in withheld),
                    "historical_strict_six_planes_sharing_nonblank_tile":
                        sum(bool(tiles&old[k]) for k in strict),
                    "distinct_original_nonblank_tiles_absent_from_historical_35":
                        len(tiles-historic_tiles),
                }
                rows.append(row)
                if role=="unclassified":
                    novel.append({"tick":tick,"racer":racer,"tiles":tiles,
                                  "shares_fit":bool(tiles&fit_tiles),
                                  "shares_withheld":bool(tiles&withheld_tiles)})
        if len(rows)!=40 or len({r["original_source_index_plane_sha256"] for r in rows})!=40:
            raise ValueError("not 40 distinct actual original-source 4bpp planes")
        if Counter(x["frozen_source_role"] for x in rows)!=Counter(
                {"fit":1,"withheld":1,"unclassified":38}):
            raise ValueError("historical source identity join changed")
        new_tiles=set().union(*(r["tiles"] for r in novel))
        groups=components(novel)
        tile_sources=[(exact_tiles(decode_source_obj(
                     decode_oam(live.read(f"frame-{s['tick']:06d}-oam.bin"))[slot],
                     live.read(f"frame-{s['tick']:06d}-vram.bin"),
                     live.read(f"frame-{s['tick']:06d}-cgram.bin"),
                     oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)["plane"]))
                     for s in receipt["samples"] for slot in (96,97)]
        cross_pairs=sum(bool(a&b) for i,a in enumerate(tile_sources)
                        for b in tile_sources[i+1:])
        clean=[g for g in groups
               if not g["has_exact_nonblank_tile_shared_with_precommitted_fit"] and
                  not g["has_exact_nonblank_tile_shared_with_precommitted_withheld"]]
        counts={
            "new_original_index_planes":len(novel),
            "new_planes_sharing_any_exact_tile_with_historical_fit":
                sum(r["shares_fit"] for r in novel),
            "new_planes_sharing_any_exact_tile_with_historical_withheld":
                sum(r["shares_withheld"] for r in novel),
            "new_planes_sharing_no_historical_exact_nonblank_tile":
                sum(not r["shares_fit"] and not r["shares_withheld"] for r in novel),
            "distinct_new_live_source_nonblank_tiles":len(new_tiles),
            "new_tile_contents_absent_from_historical":len(new_tiles-historic_tiles),
            "original_live40_source_pairs_sharing_at_least_one_tile":cross_pairs,
            "connected_components_of_38_new_index_planes":len(groups),
            "components_without_legacy_fit_or_withheld_tile_connection":len(clean),
            "source_planes_in_unconnected_clean_components":
                sum(len(g["original_ticks_and_racers"]) for g in clean),
        }
        expected={"new_original_index_planes":38,
                  "new_planes_sharing_any_exact_tile_with_historical_fit":29,
                  "new_planes_sharing_any_exact_tile_with_historical_withheld":0,
                  "new_planes_sharing_no_historical_exact_nonblank_tile":9,
                  "distinct_new_live_source_nonblank_tiles":307,
                  "new_tile_contents_absent_from_historical":247,
                  "original_live40_source_pairs_sharing_at_least_one_tile":86,
                  "connected_components_of_38_new_index_planes":11,
                  "components_without_legacy_fit_or_withheld_tile_connection":3,
                  "source_planes_in_unconnected_clean_components":9}
        if counts!=expected or sorted(len(x["original_ticks_and_racers"]) for x in clean)!=[1,4,4]:
            raise ValueError("real original 40-sprite source-tile result changed")
        return {
            "schema":SCHEMA,
            "actual_original_source_zip_sha256":SOURCE_ZIP_SHA,
            "historical_source_corpus_zip_sha256":CORPUS_SHA,
            "historical_index_provenance_zip_sha256":INDEX_SHA,
            "historical_tile_lineage_zip_sha256":TILE_SHA,
            "historical_frozen_holdout_zip_sha256":HOLDOUT_SHA,
            "all_original_59_source_RGB_to_4bpp_index_shas_verified":True,
            "historical_35_original_index_planes_verified":True,
            "historical_170_exact_nonblank_tile_sharing_edges_verified":True,
            "original_Mesen_40_completed_screen_sprite_registrations_verified":True,
            "frozen_historical_16_fit_19_withheld_6_strict_unchanged":True,
            "counts":counts,
            "new_38_source_tile_connected_components":groups,
            "per_actual_original_sprite":rows,
            "new_source_fit_or_3D_holdout_assignment_made":False,
            "source_1994_3D_camera_mesh_bones_or_pose_labels_recovered":False,
            "owner_likeness_approved":False,
        }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ("original-20-zip","historical-corpus-zip","historical-index-zip",
                 "historical-tile-zip","historical-holdout-zip","receipt","out"):
        p.add_argument("--"+flag,type=Path,required=True)
    a=p.parse_args()
    result=evaluate(a.original_20_zip,a.historical_corpus_zip,a.historical_index_zip,
                    a.historical_tile_zip,a.historical_holdout_zip,a.receipt)
    publish_text_once(a.out,json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"schema":SCHEMA,"counts":result["counts"],
                      "source_3d_recovered":False},sort_keys=True))


if __name__=="__main__":
    main()
