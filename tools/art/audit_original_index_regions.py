#!/usr/bin/env python3
"""Full authenticated 59-representation original-ROM index-region producer.

Numerical output only. Reuses the original #3057 ROM/PNG byte-for-byte
source audit; neither sprites nor tile-index arrays are published.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import zipfile

from tools.art.audit_original_racer_palette_indices import (
    original_source_audit,composition_for_registry_entry,
    rasterize_composed_palette_indices,digest)
from tools.art.audit_art4k_original_wheel_ring import validate_corpus_and_measure
from tools.art.index_region_descriptors import describe_index_regions
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-AUTHENTICATED-ORIGINAL-INDEX-REGION-CORPUS/1"

def grouped_descriptors(records:list)->dict:
    """Deduplicate by exact index SHA, while preserving all colourway ring ties."""
    if not isinstance(records,list) or not records:
        raise ValueError("missing authenticated 4bpp source input")
    groups={}
    for rec in records:
        plane=rec["indices"];touched=rec["touched"]
        key=digest(plane)
        if key!=rec["expected_index_sha256"] or digest(touched)!=rec["expected_touched_sha256"]:
            raise ValueError("source input changed since actual authenticated ROM producer")
        if key not in groups:
            groups[key]={"indices":plane,"touched":touched,"centres":set(),"rgbs":set()}
        group=groups[key]
        if group["indices"]!=plane or group["touched"]!=touched:
            raise ValueError("index SHA reused with divergent pixel provenance")
        for centre in rec["centres"]:
            if (not isinstance(centre,(list,tuple)) or len(centre)!=3 or
                    any(type(v) is not int for v in centre)):
                raise ValueError("invalid source 2D ring centre")
            group["centres"].add(tuple(centre))
        group["rgbs"].add(rec["rgba_sha256"])
    output={}
    for key,entry in sorted(groups.items()):
        desc=describe_index_regions(entry["indices"],entry["touched"],
                                    [list(x) for x in sorted(entry["centres"])])
        desc["source_colourway_image_count"]=len(entry["rgbs"])
        desc["all_colourway_2d_ring_hypotheses_retained"]=True
        output[key]=desc
    return output

def produce(rom_path:Path,registry_path:Path,corpus_zip:Path)->dict:
    """Complete original SHA guards must pass before constructing descriptors."""
    original=original_source_audit(rom_path,registry_path,corpus_zip)
    if (original["registered_original_representations"]!=59 or
            original["unique_source_RGBA_images"]!=41 or
            original["unique_source_binary_silhouettes"]!=35):
        raise ValueError("not the authenticated 59/41/35 source corpus")
    audited=validate_corpus_and_measure(corpus_zip)
    with zipfile.ZipFile(corpus_zip) as z:
        raw=json.loads(z.read("source-corpus.json"))
    original_reps=raw["source_representations"]
    registry={e["representation_id"]:e for e in json.loads(registry_path.read_bytes())["entries"]}
    expected={r["registered_original_representation_id"]:r
              for r in original["per_original_representation"]}
    ring_by_rgba={r["source_rgba_sha256"]:
                  r["2d_ring_candidate"]["best_candidate_centres_xy_radius_logical_px"]
                  for r in audited["images"]}
    rom=rom_path.read_bytes()
    items=[];provenance=[]
    for identity in sorted(original_reps):
        entry=registry[identity];record=expected[identity]
        composition=composition_for_registry_entry(rom,entry)
        indices,touched=rasterize_composed_palette_indices(
            rom,composition,entry["player"],return_touched=True)
        item={
            "indices":indices,"touched":touched,
            "expected_index_sha256":record["original_4bpp_index_plane_sha256"],
            "expected_touched_sha256":record["original_4bpp_tile_written_mask_sha256"],
            "rgba_sha256":record["source_rgba_sha256"],
            "centres":ring_by_rgba[record["source_rgba_sha256"]],
        }
        items.append(item)
        provenance.append({
            "original_representation_id":identity,
            "source_index_sha256":item["expected_index_sha256"],
            "source_rgba_sha256":item["rgba_sha256"],
            "original_ring_centres_xy_radius":item["centres"],
        })
    groups=grouped_descriptors(items)
    if len(groups)!=35 or len(provenance)!=59:
        raise ValueError("authenticated 35 distinct source index planes not recovered")
    return {
        "schema":SCHEMA,
        "source_rom_sha256":original["original_USA_ROM_sha256"],
        "historical_source_registry_sha256":original["original_registry_sha256"],
        "source_corpus_manifest_sha256":original["canonical_original_source_corpus_sha256"],
        "verified_original_source_representations":59,
        "verified_source_RGBA_images":41,
        "unique_binary_silhouettes":35,
        "unique_index_planes":35,
        "original_1994_3d_part_identity_verified":False,
        "original_1994_camera_calibrated":False,
        "owner_likeness_approved":False,
        "per_representation_provenance":provenance,
        "unique_index_plane_regions":groups,
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom",type=Path,required=True)
    parser.add_argument("--registry",type=Path,required=True)
    parser.add_argument("--source-zip",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    opts=parser.parse_args()
    result=produce(opts.rom,opts.registry,opts.source_zip)
    publish_text_once(opts.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items()
                      if k not in ("per_representation_provenance","unique_index_plane_regions")},
                     sort_keys=True,indent=2))

if __name__=="__main__":
    main()
