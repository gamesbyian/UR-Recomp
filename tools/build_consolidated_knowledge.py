#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"data"
NAMES=["Dragster","Zoom Zoo","Bowl","Switcher","Monster","Wobble","Twinpeak","Skier","Loopback","Small Cut","Looper","MegaJump","Jumps","Flat Fun","Infinity","Last One","Marathon","Circle","Plinkey","Jumpover","Dragrace","Ping Pong","Hill Climb","Hybrid","Short Cut","Down+Up","Highroad","Spine","Boo!","Fire Escape","Wario Paint","Crock","Downer","East","Hairpin Hill","Vertical","Flash","Little Dipper","Fruitbat","123 Jump","Griller","Two Loops","Neon","Hamster","To and Fro"]
TOURS=["Crawler","Jumper","Shuffler","Bounder","Walker","Runner","Hopper","Sprinter","Hunter"]
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
def code_addr(x):
    x=addr(x)
    if not x or ":" not in x:return x
    b,o=x.split(":");bank=int(b,16)
    if bank < 0x40: bank += 0x80
    return f"{bank:02X}:{o}"
def anum(x):
    x=code_addr(x)
    if not x or ":" not in x:return None
    b,o=x.split(":");return (int(b,16)<<16)|int(o,16)
def courses():
    streams=load("analysis/generated/rnc-stream-manifest.json")["roms"]["usa-retail"]["streams"]
    rows=load("analysis/generated/course-resource-list-manifest.json")["builds"]["usa-retail"]["courses"]
    sample={x["index"]:x for x in load("analysis/generated/course-presentation-contract-sample.json")["courses"]}
    landmarks={re.sub(r"[^a-z0-9]","",x["name"].lower()):x for x in load("analysis/generated/dessyreqt-course-landmarks.json")["tracks"]}
    sb={x["index"]:x for x in streams}
    assert len(rows)==len(streams)==45
    out=[]
    for c in rows:
        i=c["index"];s=sb[i];w,h=c["layout_dims"]
        r={"id":f"course:{i:02d}","stream_index":i,"name":NAMES[i-1],"name_status":"cross_source_reconciled","tour":TOURS[c["tour_index"]-1],"tour_index":c["tour_index"],"tour_slot":c["tour_slot"],"track_kind":c["track_kind"],
        "rom":{"offset":s["offset"],"packed_size":s["packed_size"],"decoded_size":s["unpacked_size"],"packed_sha256":s["packed_sha256"],"decoded_sha256":s["unpacked_sha256"],"compression_ratio":round(s["packed_size"]/s["unpacked_size"],8)},
        "header":{"layout_dims":[w,h],"dimension_product":c["layout_dim_product"],"stunt_time_or_mode":c["stunt_time_or_mode"],"spawn_or_landmark_a":c["spawn_or_landmark_a"],"spawn_or_landmark_b":c["spawn_or_landmark_b"],"resource_cursor_initial":c["resource_cursor_initial"]},
        "derived_presentation_geometry":{"basis":"promoted course-family presentation contract","status":"derived_from_promoted","coarse_sector_world_units":64,"fine_cell_world_units":16,"coarse_grid":[w*4,h*4],"coarse_entry_count":w*h*16,"world_extent":[w*256,h*256],"aspect_ratio":round(w/h,8)},
        "resources":{"ids":c["resource_ids"],"count":c["resource_count"],"terminator_offset":c["resource_terminator_offset"],"bytes_after_terminator":c["bytes_after_terminator"],"bytes_from_initial_cursor_through_eof":c["decoded_size"]-c["resource_cursor_initial"]},
        "sources":["analysis/generated/rnc-stream-manifest.json","analysis/generated/course-resource-list-manifest.json","reference/notes/course-order-and-stunt-timer.md"]}
        landmark=landmarks[re.sub(r"[^a-z0-9]","",r["name"].lower())]
        r["historical_landmarks"]={"status":"historical_independent","track_id":landmark["track_id"],"start_x":landmark["start_x"],"finish_x":landmark["finish_x"],"start_matches_header_a_x16":landmark["start_x"]==c["spawn_or_landmark_a"][0]*16,"source":"analysis/generated/dessyreqt-course-landmarks.json"}
        if i in sample:
            q=sample[i];r["presentation_contract_sample"]={"status":"static_proven","fine_record_count":q["fine_record_count"],"resource_count":q["resource_count"],"c000_total":q["c000_total"],"a000_total":q["a000_total"],"normal_surface_word_count":q["normal_surface_word_count"],"checks":q["checks"],"source":"analysis/generated/course-presentation-contract-sample.json"}
        if i==1:r["runtime_landmarks"]={"spawn_world":[1088,800],"historical_finish_x_probe":25278,"source":"analysis/generated/dragster-presentation-spatial-contract.json"}
        out.append(r)
    return {"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Normalized one-record-per-course query surface.","courses":out,"identity_mapping":{"historical_track_id_rule":"dessyreqt_track_id = stream_index - 1","holds_for_all_45":all(x["historical_landmarks"]["track_id"]==x["stream_index"]-1 for x in out),"status":"cross_source_reconciled","sources":["analysis/generated/dessyreqt-course-landmarks.json","analysis/generated/course-resource-list-manifest.json"]}}
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
    desk=load("analysis/generated/dessyreqt-workspace-index.json")
    motion=load("analysis/generated/wram-motion-atlas.json")
    nitro=load("analysis/generated/nitrodon-reconciliation.json")
    return {"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Normalized promoted state semantics plus cross-build racer relations.","entries":out,"regional_racer_relations":rr,"historical_paired_racer_leads":{"status":"historical_independent","fields":desk["paired_racer_leads"],"source":"analysis/generated/dessyreqt-workspace-index.json"},"regional_motion_clusters":{"status":"cross_build_supported","clusters":[{"build":x["build"],"delta":x["delta"],"anchor_count":x["anchor_count"],"field_count":x["field_count"],"usa_words":x["usa_words"],"candidate_words":x["candidate_words"]} for x in motion["clusters"]],"source":"analysis/generated/wram-motion-atlas.json"},"reconciled_semantic_overrides":{"status":"reconciled","fields":nitro["corrected_symbols"],"source":"analysis/generated/nitrodon-reconciliation.json"}}
def code():
    sy=load("analysis/generated/symbols.json");co=load("analysis/generated/cross-build-symbol-correspondence.json");ce=load("analysis/generated/comparative-structural-census.json");cb=defaultdict(list)
    for x in co.get("functions",[]):cb[(x.get("name"),code_addr(x.get("usa")))].append(x)
    fs=[]
    for s in sy["entries"]:
        if s.get("kind")!="function":continue
        a=code_addr(s.get("address"));n=anum(a);inside=[]
        for r in ce["regions"]:
            lo,hi=anum(r["usa_start"]),anum(r["usa_end"])
            if n is not None and lo is not None and lo<=n<=hi:inside.append({"source":r["source"],"region":r["name"],"usa_start":r["usa_start"],"usa_end":r["usa_end"]})
        fs.append({"id":f"function:{s.get('name')}","name":s.get("name"),"usa":a,"confidence":s.get("confidence"),"notes":s.get("evidence_/_notes") or s.get("notes"),"cross_build":cb.get((s.get("name"),a),[]),"containing_structural_regions":inside,"sources":["analysis/generated/symbols.json","analysis/generated/cross-build-symbol-correspondence.json","analysis/generated/comparative-structural-census.json"]})
    return {"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Queryable semantic-function and bounded-region join.","functions":fs,"regions":ce["regions"],"census_totals":ce["totals"]}
def presentation():
    r=load("analysis/generated/racer-presentation-family.json")
    evidence=dict(r["evidence"])
    evidence["widescreen_plus8_sequence_boundary"]={
        "status":"closed_for_current_widescreen_decision",
        "event":"object-tail-141",
        "control_sequence_selector":1,
        "plus8_sequence_selector":3,
        "sequence_cursor_both":1,
        "sequence_writer":"83:EB57 -> 82:8952/8956 -> STA $0DE9,Y; Y=2 targets P2 $0DEB",
        "selector_source":"$7710B1 six-state presentation/frontend counter; 83:EB3F..EB51 maps 0/1->1, 2/3->3, 4/5->5",
        "counter_raw_classes":{"control":"0/1","plus8":"2/3"},
        "counter_writers":["83:C8EF..C8FB clamp/reset","83:C9E2..C9F2 modulo-6 advance"],
        "control_frame_id":"0x0A45",
        "plus8_frame_id":"0x0A8D",
        "persistent_chain":"$0DEB -> $0F4F -> $0F97 -> $0FEB",
        "first_vram_divergence":"object-tail-142",
        "upload_chain":"83:F0BB -> 83:F296 -> 83:F2BB -> NMI DMA",
        "oam_equal_through_early_gap":True,
        "raw_counter_note":"Exact member within each two-value raw class is not directly dumped; that ambiguity cannot alter the selected sequence or causal conclusion.",
        "evidence":"analysis/generated/widescreen-plus8-presentation-sequence-closure-2026-10-02.md",
        "workflow_run":36978866214,
    }
    return {"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Multi-family semantic presentation-asset query surface.","families":[{"id":r["family"],"source":"analysis/generated/racer-presentation-family.json","replacement_key":r["replacement_key"],"frames":r["frames"],"graphics":r["graphics"],"palettes":r["palettes"],"observed_states":r["observed_states"],"roundtrip":r["roundtrip"],"evidence":evidence,"piece_semantics":r["piece_semantics"],"inferred_record_structure":{"status":"mechanically_recovered","header_bytes":4,"header_role":"30-cell occupancy lattice plus two reserved-zero bits","rule":"five six-position major groups, scanned MSB-first; every set occupancy position consumes the next packed 16-bit word","observed_frames":len(r["frames"]),"holds_for_all_observed_frames":all(x["occupancy_layout"]["reserved_zero_value"]==0 and len(x["pieces"])==x["packed_word_count"] for x in r["frames"]),"implication":"header position -> packed-word index is now directly queryable for the retained racer family; packed records feed tile/presentation staging before fixed-slot OAM composition","source":"tools/extract_racer_presentation_family.py"}}]}

def resource_catalog():
    cs=courses()["courses"]
    out={"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Normalized course-resource incidence, ordering, and promoted semantic anchors.","corpus":{"course_count":45,"resource_id_count":len({rid for row in cs for rid in row["resources"]["ids"]})},"promoted_resources":[{"id":36,"hex":"0x24","name":"checkpoint_finish_resource_family","confidence":"promoted","incidence":{"courses":36,"track_kinds":["race-a","circuit-a","race-b","circuit-b"],"stunt_courses":0},"semantic_evidence":["Dragster resource 0x24 owns C000 offsets 6..14 and contributes nine object-code 0x14 cells.","Object code 0x14 dispatches to Race_HandleCheckpointFinish.","Resource 0x24 occurs in all 36 race/circuit courses and none of 9 stunt courses across preserved builds."],"sources":["analysis/generated/checkpoint-resource-family-2026-10-01.md","analysis/generated/dragster-resource-span-attribution-2026-09-30.md","analysis/generated/course-resource-list-manifest.json"]}],"structural_bundles":[{"id":"bundle-03-08","resource_ids":[3,4,5,6,7,8],"hex":["0x03","0x04","0x05","0x06","0x07","0x08"],"carrier_courses":43,"all_carriers_preserve_order":True,"all_carriers_preserve_adjacency":True,"absent_courses":["Dragster","Circle"],"interpretation":"strong structural bundle candidate; semantics intentionally unnamed"},{"id":"bundle-09-0B","resource_ids":[9,10,11],"hex":["0x09","0x0A","0x0B"],"carrier_courses":42,"all_carriers_preserve_order":True,"all_carriers_preserve_adjacency":True,"absent_courses":["Dragster","Circle","Two Loops"],"interpretation":"strong structural bundle candidate; semantics intentionally unnamed"},{"id":"universal-01-02","resource_ids":[1,2],"hex":["0x01","0x02"],"carrier_courses":45,"all_carriers_preserve_order":True,"all_carriers_preserve_adjacency":False,"adjacency_exception":"Circle inserts resource 0x12 between 0x01 and 0x02","interpretation":"universal ordered core, but not a guaranteed adjacent pair"},{"id":"paired-incidence-16-18","resource_ids":[22,24],"hex":["0x16","0x18"],"carrier_courses":39,"all_carriers_preserve_order":True,"all_carriers_preserve_adjacency":False,"interpretation":"identical course-incidence signature and stable order; structural relation candidate"}],"list_level_invariants":{"stunt_lists_have_no_duplicate_resource_ids":all(len(x["resources"]["ids"])==len(set(x["resources"]["ids"])) for x in cs if x["track_kind"]=="stunt"),"stunt_course_count":9,"note":"Duplicate resource IDs occur in several race/circuit lists, so uniqueness is a mode-correlated structural property rather than a global list property."},"sources":["analysis/data/course-corpus.json","analysis/generated/course-resource-list-manifest.json"]}

    out["cross_build_conservation"]={"builds":["usa-retail","europe-retail","legacy-beta","pal-prototype-1994-11-29"],"exact_bundle_carrier_counts":{"0x03-0x08":43,"0x09-0x0B":42,"0x01-0x02":45,"0x16-0x18":39,"0x24":36},"note":"Carrier counts and ordering/adjacency behavior for these structural groups are preserved across all four builds."}
    out["europe_retail_changed_course_resource_deltas"]={"known_changed_streams":[4,16,20,26,27,35,36],"unchanged_resource_lists":[4,16,20,27,35],"changed_resource_lists":[{"stream_index":26,"course":"Down+Up","change":"append resource 0x22"},{"stream_index":36,"course":"Vertical","change":"append resource 0x22"}],"other_header_delta":{"stream_index":4,"course":"Switcher","change":"spawn A Y 26 -> 22; dimensions and resource list unchanged"},"implication":"Most Europe-retail course payload changes are internal to course-local content rather than high-level resource selection."}
    return out

def progression():
    return json.loads((OUT/"progression-model.json").read_text()) if (OUT/"progression-model.json").exists() else {}

def all_data():
    ids=[x["id"] for x in CLAIMS];assert len(ids)==len(set(ids))
    return {"course-corpus.json":courses(),"state-schema.json":state(),"code-semantics.json":code(),"presentation-assets.json":presentation(),"course-resource-catalog.json":resource_catalog(),"evidence-claims.json":{"schema_version":1,"generated_by":"tools/build_consolidated_knowledge.py","purpose":"Selective atomic claims for cross-source inference.","claims":CLAIMS}}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--check",action="store_true");args=ap.parse_args();stale=[]
    for name,payload in all_data().items():
        p=OUT/name;text=json.dumps(payload,indent=2)+"\n"
        if args.check:
            if not p.exists() or p.read_text()!=text:stale.append(str(p.relative_to(ROOT)))
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    if stale:raise SystemExit("stale consolidated data: "+", ".join(stale))
if __name__=="__main__":main()
