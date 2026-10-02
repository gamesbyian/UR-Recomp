#!/usr/bin/env python3
"""Build a neutral presentation-facing spatial/resource contract for Dragster."""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from analyze_course_resource_lists import parse_course_resource_list
from analyze_rnc_streams import find_streams
from compare_europe_usa_snes2asm_homologs import cpu_to_offset
from rnc_method1 import unpack_method1

ROOT=Path(__file__).resolve().parents[1]
ROM=ROOT/"reference/roms/retail/Uniracers_USA.sfc"
LANDMARKS=ROOT/"analysis/generated/dessyreqt-course-landmarks.json"
JSON_OUT=ROOT/"analysis/generated/dragster-presentation-spatial-contract.json"
MD_OUT=ROOT/"analysis/generated/dragster-presentation-spatial-contract.md"
SPATIAL_BASE=0x000F
SECTOR_COUNT=1024
SECTOR_WORLD_UNITS=64
RESOURCE_DESC_TABLE_CPU="82:B7DA"
KNOWN_DRAGSTER_C000=[0x00,0x00,0x12,0x1C,0x00,0x00]+[0x14]*9+[0x02]*5

def descriptor(rom,rid):
    base=cpu_to_offset(RESOURCE_DESC_TABLE_CPU)
    raw=rom[base+rid*5:base+rid*5+5]
    size=raw[3]|(raw[4]<<8)
    return {
      "resource_id":rid,"resource_id_hex":f"{rid:02X}",
      "descriptor_bytes":raw.hex(" "),
      "source_bank":raw[0]&0x7F,"source_offset":raw[1]|(raw[2]<<8),
      "special_or_compressed_flag":bool(raw[0]&0x80),
      "size":size,"a000_span":size>>2,"c000_span":size>>7,
    }

def sector_index(world_x):
    return (world_x&0xFFFF)//SECTOR_WORLD_UNITS

def sector_record(decoded,plane_count,index):
    return [decoded[SPATIAL_BASE+p*SECTOR_COUNT+index] for p in range(plane_count)]

def build(query_start=None,query_end=None):
    rom=ROM.read_bytes()
    streams=find_streams(rom)
    if len(streams)!=45: raise SystemExit(f"expected 45 streams, got {len(streams)}")
    rom_off,packed,_=streams[0]
    decoded=unpack_method1(packed)
    parsed=parse_course_resource_list(decoded)
    cursor=parsed["resource_cursor_initial"]
    spatial_bytes=cursor-SPATIAL_BASE
    if spatial_bytes%SECTOR_COUNT: raise SystemExit("Dragster pre-resource region is not 1024-cell plane aligned")
    plane_count=spatial_bytes//SECTOR_COUNT
    if plane_count!=33: raise SystemExit(f"expected 33 spatial planes, got {plane_count}")

    resources=[]; ac=cc=0
    for rid in parsed["resource_ids"]:
        d=descriptor(rom,rid)
        d["a000_range"]=[ac,ac+d["a000_span"]-1]
        d["c000_range"]=[cc,cc+d["c000_span"]-1]
        ac+=d["a000_span"]; cc+=d["c000_span"]
        resources.append(d)
    if cc!=len(KNOWN_DRAGSTER_C000): raise SystemExit("C000 materialization length disagrees with confirmed Dragster snapshot")

    ids=set(parsed["resource_ids"]); planes=[]
    for p in range(plane_count):
        start=SPATIAL_BASE+p*SECTOR_COUNT
        block=decoded[start:start+SECTOR_COUNT]; c=Counter(block)
        planes.append({
          "plane":p,"decoded_base":start,"runtime_base":f"7F:{start:04X}",
          "min":min(block),"max":max(block),"distinct":len(c),
          "zero_fraction":round(c.get(0,0)/len(block),6),
          "fraction_lt_c000_size":round(sum(v<cc for v in block)/len(block),6),
          "fraction_equal_resource_id":round(sum(v in ids for v in block)/len(block),6),
          "top_values":[[v,n] for v,n in c.most_common(12)],
        })

    lm=json.loads(LANDMARKS.read_text())
    drag=next(t for t in lm["tracks"] if t["track_id"]==0)
    anchors=[]
    for name,x,status in [
      ("spawn",parsed["spawn_or_landmark_a"][0]*16,"runtime_confirmed_at_initialization"),
      ("historical_finish_probe",drag["finish_x"],"historical_probe"),
    ]:
        i=sector_index(x)
        anchors.append({"name":name,"world_x":x,"sector_index":i,"sector_record":sector_record(decoded,plane_count,i),"status":status})

    result={
      "schema_version":1,
      "course":{"name":"Dragster","stream_index":1,"rom_offset":rom_off,"decoded_size":len(decoded),
                "layout_dims":parsed["layout_dims"],"spawn_or_landmark_a":parsed["spawn_or_landmark_a"],
                "spawn_or_landmark_b":parsed["spawn_or_landmark_b"],"spawn_world_scale":16},
      "presentation_spatial_contract":{
        "cell_count":SECTOR_COUNT,"sector_world_units":SECTOR_WORLD_UNITS,
        "world_x_domain":[0,SECTOR_COUNT*SECTOR_WORLD_UNITS-1],
        "world_x_domain_note":"Neutral 16-bit/1024-sector query domain from the runtime 64-unit sector cadence; header dimensions are not treated as Cartesian world extents.",
        "spatial_base_decoded":SPATIAL_BASE,"resource_list_offset":cursor,
        "spatial_byte_count":spatial_bytes,"plane_count":plane_count,"storage":"plane-major",
        "plane_stride":SECTOR_COUNT,
        "runtime_landmarks":{"plane_0_base":"7F:000F","plane_32_base":"7F:800F","evidence":"CourseSectorNeighborhoodGather 81:8A4A..8B94"},
        "planes":planes,"anchors":anchors},
      "resources":{
        "tail_ids":parsed["resource_ids"],"terminator_offset":parsed["resource_terminator_offset"],
        "a000_total":ac,"c000_total":cc,"entries":resources,
        "confirmed_c000_snapshot":KNOWN_DRAGSTER_C000,
        "checkpoint_finish":{"resource_id":0x24,"c000_range":next(d["c000_range"] for d in resources if d["resource_id"]==0x24),
                             "behavior_code":0x14,"semantic":"race/circuit checkpoint-finish resource family"}},
      "validation":{
        "decoded_payload_runtime_base":"7F:0000",
        "decoded_payload_runtime_match":"33814/33815 bytes at settled Dragster; cursor byte is mutable",
        "resource_materialization":"descriptor-derived A000/C000 spans agree with frame-exact runtime cursors",
        "surface_path":"sector gather -> 20-byte workspace -> Course_SampleRuntimeSurface -> A000/C000",
        "visual_corpus":"reference/imported/reverse-engineering/dessyreqt/Maps/01 Crawler/01 Dragster.png",
        "historical_world_x_anchors":{"source":"analysis/generated/dessyreqt-course-landmarks.json","warning":lm.get("warning")}},
      "boundaries":{
        "proven":[
          "Dragster bytes 0x000F..0x840E are exactly 33 plane-major arrays of 1024 bytes.",
          "The resource list begins immediately at 0x840F.",
          "Runtime course lookup uses bases 7F:000F and 7F:800F, exactly plane 0 and plane 32 in this decomposition.",
          "The resource list deterministically materializes six resources into A000/C000 spans.",
          "Resource 0x24 owns C000 slots 6..14, all confirmed checkpoint/finish code 0x14 on Dragster."
        ],
        "not_claimed":[
          "Header dimensions 256x4 are not treated as Cartesian world extents.",
          "Individual meanings of all 33 spatial planes are not assigned.",
          "The exact plane/workspace field that selects a particular A000/C000 resource slot is not named here.",
          "Gameplay activation/liveness is outside this contract."
        ]}}
    if query_start is not None and query_end is not None:
        a,b=sorted((query_start,query_end)); first,last=sector_index(a),sector_index(b)
        indices=list(range(first,last+1)) if last>=first else list(range(first,SECTOR_COUNT))+list(range(last+1))
        result["query"]={"world_x_start":a,"world_x_end":b,"sector_indices":indices,
                         "records":[{"sector_index":i,"attributes":sector_record(decoded,plane_count,i)} for i in indices]}
    return result

def render_md(r):
    c=r["course"]; s=r["presentation_spatial_contract"]; res=r["resources"]
    lines=["# Dragster presentation spatial/resource contract","",
      "Generated by tools/build_course_presentation_contract.py. This is deliberately a Widescreen-facing contract, not an editor-complete course format.","",
      "## Spatial slab","",
      f"- decoded stream: 1 ({c['name']}), {c['decoded_size']} bytes;",
      f"- spatial bytes: 0x{s['spatial_base_decoded']:04X}..0x{s['resource_list_offset']-1:04X} = {s['spatial_byte_count']} bytes;",
      f"- exact decomposition: **{s['plane_count']} planes × {s['cell_count']} cells**;",
      f"- plane stride: 0x{s['plane_stride']:04X}; plane 0 is 7F:000F, plane 32 is 7F:800F;",
      f"- runtime sector cadence: {s['sector_world_units']} world units, yielding a neutral 0..{s['cell_count']-1} sector-index domain.","",
      "The 256×4 header pair is retained as a layout/display shape only. It is not promoted to a Cartesian world extent: Dragster's confirmed/historical world-X anchors exceed a 256×64 interpretation.","",
      "## Resource materialization","",
      "| ID | descriptor | size | A000 range | C000 range |","|---:|---|---:|---|---|"]
    for e in res["entries"]:
        lines.append(f"| {e['resource_id_hex']} | {e['descriptor_bytes']} | 0x{e['size']:04X} | {e['a000_range'][0]}..{e['a000_range'][1]} | {e['c000_range'][0]}..{e['c000_range'][1]} |")
    lines += ["",f"Totals: A000={res['a000_total']} bytes; C000={res['c000_total']} bytes.","",
      "Resource 0x24 owns C000 slots 6..14; the confirmed Dragster snapshot contains nine 0x14 cells there, and 0x14 dispatches to the checkpoint/finish handler.","",
      "## Presentation-facing query","",
      "World X is reduced on a 64-unit cadence to a 0..1023 sector index. For any requested X interval, the tool emits the exact 33-byte plane vector for every touched sector. This is a neutral record for correlating camera-visible space with course data while field semantics remain evidence-driven.","",
      "Example: python3 tools/build_course_presentation_contract.py --query-x 1088 1408","",
      "## Validation and stop boundary",""]
    lines += [f"- proven: {x}" for x in r["boundaries"]["proven"]]
    lines += [f"- deliberately open: {x}" for x in r["boundaries"]["not_claimed"]]
    lines += ["","Generalization should first test whether another representative course exposes the same 1024-cell plane-major organization and locate its resource-list boundary. Do not decode all 45 plane fields merely for completeness.",""]
    return "\\n".join(lines)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--json-out",type=Path,default=JSON_OUT); ap.add_argument("--md-out",type=Path,default=MD_OUT)
    ap.add_argument("--query-x",nargs=2,type=int,metavar=("START","END")); args=ap.parse_args()
    q=args.query_x or (None,None); r=build(*q)
    args.json_out.parent.mkdir(parents=True,exist_ok=True); args.json_out.write_text(json.dumps(r,indent=2)+"\\n"); args.md_out.write_text(render_md(r))
    print(json.dumps(r,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
