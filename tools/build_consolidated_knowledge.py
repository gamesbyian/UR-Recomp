#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"data"
NAMES=["Dragster","Zoom Zoo","Bowl","Switcher","Monster","Looper","MegaJump","Jumps","Flat Fun","Infinity","Dragrace","Ping Pong","Hill Climb","Hybrid","Short Cut","Wario Paint","Crock","Downer","East","Hairpin Hill","Wobble","Twinpeak","Skier","Loopback","Small Cut","Last One","Marathon","Circle","Plinkey","Jumpover","Down+Up","Highroad","Spine","Boo!","Fire Escape","Vertical","Flash","Little Dipper","Fruitbat","123 Jump","Griller","Two Loops","Neon","Hamster","To and Fro"]
TOURS=["Crawler","Shuffler","Walker","Hopper","Jumper","Bounder","Runner","Sprinter","Hunter"]
CLAIMS=[
{"id":"course-ordinal-track-order","subject":"course-corpus","predicate":"stream_order_matches_shipped_track_order","value":True,"status":"cross_build_supported","sources":["reference/notes/course-order-and-stunt-timer.md","analysis/generated/course-resource-list-manifest.json"]},
{"id":"course-stunt-duration-45","subject":"course-type:stunt","predicate":"duration_seconds","value":45,"status":"historical_independent","sources":["reference/notes/course-order-and-stunt-timer.md"]},
{"id":"course-header-product-1024","subject":"course-corpus","predicate":"normalized_header_dimension_product","value":1024,"status":"static_proven","sources":["analysis/generated/course-resource-list-manifest.json","docs/COURSE-FORMAT.md"]},
{"id":"course-historical-64-unit-block","subject":"course-storage","predicate":"historical_block_size_world_units","value":[64,64],"status":"external_unreproduced","sources":["reference/notes/course-layout-history.md","reference/notes/course-reverse-engineering-history.md"]},
{"id":"state-04b7-signed-speed","subject":"7E:04B7","predicate":"historical_semantics","value":"player 1 signed X speed","status":"runtime_proven","sources":["reference/notes/tas-and-sram-research.md","analysis/generated/symbols.json"]},
{"id":"active-display-oam-uniracers","subject":"renderer:oam","predicate":"uses_active_display_oam_behavior","value":True,"status":"historical_independent","sources":["reference/notes/oam-active-display.md","reference/catalog.yml"]},
{"id":"rnc-method1-course-corpus","subject":"course-corpus","predicate":"compression","value":"RNC Method 1","status":"static_proven","sources":["analysis/generated/rnc-stream-manifest.json","docs/COURSE-FORMAT.md"]},
{"id":"dragster-activation-after-visibility","subject":"course:01:checkpoint-finish","predicate":"visibility_precedes_behavior_activation","value":True,"status":"runtime_proven","sources":["analysis/generated/object-activation-runtime-boundary-2026-10-02.md"]},
]
def load(p): return json.loads((ROOT/p).read_text())
def addr(x):
    if x is None:return None
    s=str(x).replace(chr(96),"").strip();m=re.search(r"([0-9A-Fa-f]{2}):([0-9A-Fa-f]{4})",s)
    return f"{m.group(1).upper()}:{m.group(2).upper()}" if m else s
def anum(x):
    x=addr(x)
    if not x or ":" not in x:return None
    b,o=x.split(":");return (int(b,16)<<16)|int(o,16)
def courses():
    streams=load("analysis/generated/rnc-stream-manifest.json")["roms"]["usa-retail"]["streams"]
    rows=load("analysis/generated/course-resource-list-manifest.json")["builds"]["usa-retail"]["courses"]
    sample={x["index"]:x for x in load("analysis/generated/course-presentation-contract-sample.json")["courses"]}
    sb={x["index"]:x for x in streams}
    assert len(rows)==len(streams)==45
    out=[]
    for c in rows:
        i=c["index"];s=sb[i];w,h=c["layout_dims"]
        r={"id":f"course:{i:02d}","stream_index":i,"name":NAMES[i-1],"name_status":"historical_independent","tour":TOURS[c["tour_index"]-1],"tour_index":c["tour_index"],"tour_slot":c["tour_slot"],"track_kind":c["track_kind"],
        "rom":{"offset":s["offset"],"packed_size":s["packed_size"],"decoded_size":s["unpacked_size"],"packed_sha256":s["packed_sha256"],"decoded_sha256":s["unpacked_sha256"],"compression_ratio":round(s["packed_size"]/s["unpacked_size"],8)},
        "header":{"layout_dims":[w,h],"dimension_product":c["layout_dim_product"],"stunt_time_or_mode":c["stunt_time_or_mode"],"spawn_or_landmark_a":c["spawn_or_landmark_a"],"spawn_or_landmark_b":c["spawn_or_landmark_b"],"resource_cursor_initial":c["resource_cursor_initial"]},
        "derived_presentation_geometry":{"basis":"promoted course-family presentation contract","status":"derived_from_promoted","coarse_sector_world_units":64,"fine_cell_world_units":16,"coarse_grid":[w*4,h*4],"coarse_entry_count":w*h*16,"world_extent":[w*256,h*256],"aspect_ratio":round(w/h,8)},
        "resources":{"ids":c["resource_ids"],"count":c["resource_count"],"terminator_offset":c["resource_terminator_offset"],"bytes_after_terminator":c["bytes_after_terminator"],"bytes_from_initial_cursor_through_eof":c["decoded_size"]-c["resource_cursor_initial"],"sequence_sha256":hashlib.sha256(bytes(c["resource_ids"])).hexdigest()},
        "sources":["analysis/generated/rnc-stream-manifest.json","analysis/generated/course-resource-list-manifest.json","reference/notes/course-order-and-stunt-timer.md"]}
        if i in sample:
            q=sample[i];r["presentation_contract_sample"]={"status":"static_proven","fine_record_count":q["fine_record_count"],"resource_count":q["resource_count"],"c000_total":q["c000_total"],"a000_total":q["a000_total"],"normal_surface_word_count":q["normal_surface_word_count"],"checks":q["checks"],"source":"analysis/generated/course-presentation-contract-sample.json"}
        if i==1:r["runtime_landmarks"]={"spawn_world":[1088,800],"historical_finish_x_probe":25278,"source":"analysis/generated/dragster-presentation-spatial-contract.json"}
        out.append(r)
    return {"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Normalized one-record-per-course query surface.","courses":out}
def state():
    sy=load("analysis/generated/symbols.json"); rel=load("analysis/generated/regional-racer-state-relations.json")["builds"];out=[];by={}
    for s in sy["entries"]:
        if s.get("kind")=="function":continue
        r={"id":f"state:{addr(s.get('address'))}","kind":s.get("kind"),"address":addr(s.get("address")),"name":s.get("name"),"width":s.get("width"),"confidence":s.get("confidence"),"notes":s.get("notes") or s.get("evidence_/_notes"),"sources":["analysis/generated/symbols.json"]};out.append(r)
        if r["name"]:by[r["name"]]=r
    rr=[]
    for build,b in rel.items():
        for name,q in b["relations"].items():
            x={"build":build,"semantic_name":name,"persistent":q["persistent"],"working":q["working"],"bidirectional":q["bidirectional"],"routine":b["routine"],"source":"analysis/generated/regional-racer-state-relations.json"};rr.append(x)
            if name in by:by[name].setdefault("regional_relations",[]).append(x)
    return {"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Normalized promoted state semantics plus cross-build racer relations.","entries":out,"regional_racer_relations":rr}
def code():
    sy=load("analysis/generated/symbols.json");co=load("analysis/generated/cross-build-symbol-correspondence.json");ce=load("analysis/generated/comparative-structural-census.json");cb=defaultdict(list)
    for x in co.get("functions",[]):cb[(x.get("name"),addr(x.get("usa")))].append(x)
    fs=[]
    for s in sy["entries"]:
        if s.get("kind")!="function":continue
        a=addr(s.get("address"));n=anum(a);inside=[]
        for r in ce["regions"]:
            lo,hi=anum(r["usa_start"]),anum(r["usa_end"])
            if n is not None and lo is not None and lo<=n<=hi:inside.append({"source":r["source"],"region":r["name"],"usa_start":r["usa_start"],"usa_end":r["usa_end"]})
        fs.append({"id":f"function:{s.get('name')}","name":s.get("name"),"usa":a,"confidence":s.get("confidence"),"notes":s.get("evidence_/_notes") or s.get("notes"),"cross_build":cb.get((s.get("name"),a),[]),"containing_structural_regions":inside,"sources":["analysis/generated/symbols.json","analysis/generated/cross-build-symbol-correspondence.json","analysis/generated/comparative-structural-census.json"]})
    return {"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Queryable semantic-function and bounded-region join.","functions":fs,"regions":ce["regions"],"census_totals":ce["totals"]}
def presentation():
    r=load("analysis/generated/racer-presentation-family.json")
    return {"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Multi-family semantic presentation-asset query surface.","families":[{"id":r["family"],"source":"analysis/generated/racer-presentation-family.json","replacement_key":r["replacement_key"],"frames":r["frames"],"graphics":r["graphics"],"palettes":r["palettes"],"observed_states":r["observed_states"],"roundtrip":r["roundtrip"],"evidence":r["evidence"]}]}
def all_data():
    ids=[x["id"] for x in CLAIMS];assert len(ids)==len(set(ids))
    return {"course-corpus.json":courses(),"state-schema.json":state(),"code-semantics.json":code(),"presentation-assets.json":presentation(),"evidence-claims.json":{"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Selective atomic claims for cross-source inference.","claims":CLAIMS}}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--check",action="store_true");args=ap.parse_args();stale=[]
    for name,payload in all_data().items():
        p=OUT/name;text=json.dumps(payload,indent=2)+"\n"
        if args.check:
            if not p.exists() or p.read_text()!=text:stale.append(str(p.relative_to(ROOT)))
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    if stale:raise SystemExit("stale consolidated data: "+", ".join(stale))
if __name__=="__main__":main()
