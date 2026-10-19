#!/usr/bin/env python3
"""RF073: digest-bound native RF047 NMI brackets from the authentic RF054 case.

Native read-helper visibility is NOT total guest-bus coverage. One framed
native return cannot establish an original/native same-phase equivalence.
RF047's single-syscall event writes can have *other logger fragments before*
the marker; recover exact event payloads by native-owned event sequence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

SCHEMA="ur-qa01-rf073-native-nmi-return-brackets/1"
ARCHIVE_SHA256="3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c"
NATIVE_SHA256="e7aa6bb4340acbdaa1cc38ff39f601dd0a8dbba24d6a244ffcad82fe8bbd705f"
ORIGINAL_SHA256="308b8e70122fa1f0ba7edcdc4c8d16e4df0137dc289533f0dc1d90bafae14c5a"
NATIVE="work/zoom-zoo/replay/native.log"
ORIGINAL="work/zoom-zoo/replay/reference.log"
TAG="QA01RF047NATIVE seq="
RECORD=re.compile(r"QA01RF047NATIVE seq=(\d+) (.*)$")
FIELDS=re.compile(r"([A-Za-z][A-Za-z0-9]*)=([^\s]+)")
FRAMES=tuple(range(1017,1026))

def require(ok:bool,why:str)->None:
    if not ok: raise ValueError(why)

def parse_native(raw:str)->tuple[list[dict],list[dict]]:
    require("QA01RF047NATIVE_TRUNCATED" not in raw,
            "RF047 source witness overflow/truncation")
    events=[]; contaminated=[]
    for line_no,line in enumerate(raw.splitlines(),1):
        if TAG not in line: continue
        require(line.count(TAG)==1,"RF047 events concatenated")
        offset=line.index(TAG)
        match=RECORD.fullmatch(line[offset:])
        require(match is not None,"RF047 atomic event suffix damaged")
        seq=int(match.group(1)); rest=match.group(2)
        pairs=FIELDS.findall(rest)
        require(bool(pairs) and " ".join(f"{k}={v}" for k,v in pairs)==rest,
                "RF047 event has malformed or unparsed fields")
        f=dict(pairs)
        require(len(f)==len(pairs) and seq==len(events)+1,
                "RF047 duplicate/missing/reordered native event")
        f["seq"]=seq
        try: frame=int(f["f"])
        except (ValueError,KeyError) as e:
            raise ValueError("RF047 frame missing") from e
        require(frame in FRAMES,"RF047 event outside source window")
        if offset:
            contaminated.append({"seq":seq,"line":line_no,
                                 "untrusted_other_logger_prefix":line[:offset]})
        events.append(f)
    require(len(events)==2741,"RF047 genuine native event count changed")
    return events,contaminated

def parse_source(original:str)->dict[int,dict]:
    rows=[]
    for line in original.splitlines():
        if not line.startswith("QA01RF044ORIGNMI "):continue
        rest=line.split(" ",1)[1];pairs=FIELDS.findall(rest)
        require(" ".join(f"{k}={v}" for k,v in pairs)==rest,
                "RF044 real original NMI fields malformed")
        f=dict(pairs)
        require(len(f)==len(pairs),"RF044 duplicate original source fields")
        try:
            frame=int(f["f"]);f1=int(f["f1"])
            old=bytes.fromhex(f["old"]);new=bytes.fromhex(f["new"])
            pc=int(f["pc"],16)
        except (ValueError,KeyError) as e:
            raise ValueError("original NMI source event incomplete") from e
        require(frame in FRAMES and f1==frame and len(old)==len(new)==5,
                "original source NMI frame/stack invalid")
        require(f["S0"]=="01F0" and f["S1"]=="01EC",
                "real source NMI stack SP movement changed")
        require(new[0]==0x26 and new[3]==0x82 and
                (new[1]|new[2]<<8)==(pc&65535) and pc>>16==0x82,
                "original NMI PC/status/bank snapshot inconsistent")
        rows.append((frame,{"frame":frame,
                           "original_guest_PC_context":f["pc"],
                           "original_raw_5_stack_bytes":new.hex().upper(),
                           "original_saved_PC_low":new[1]}))
    require([f for f,_ in rows]==list(FRAMES),
            "nine unique ordered original NMI rows missing")
    return dict(rows)

def inspect(native:str,original:str)->dict:
    events,contaminated=parse_native(native)
    original_frames=parse_source(original)
    per_frame={fr:[] for fr in FRAMES}
    for e in events: per_frame[int(e["f"])].append(e)
    brackets=[]
    for fr in FRAMES:
        ev=per_frame[fr]
        edges=[(i,e) for i,e in enumerate(ev) if e["stage"]!="read"]
        require([e["stage"] for _,e in edges]==
                ["entry","after_push","compiled_rti","handler_return"],
                f"native NMI brackets incomplete frame {fr}")
        (i0,entry),(i1,push),(i2,rti),(i3,done)=edges
        require(i0==0 and i1==i0+1 and i3==i2+1,
                f"native NMI stage order corrupted frame {fr}")
        reads=ev[i1+1:i2]
        require(len(reads)==1 and reads[0]["stage"]=="read",
                f"native stack helper read in compiled NMI ambiguous frame {fr}")
        rd=reads[0]
        require(rd["nmi"]=="1" and rd["bank"]=="00" and
                rd["addr"]=="01ED" and rd["width"]=="1" and
                rd["value"]=="0026" and rd["S"]=="01ED",
                f"native actual status consumption identity changed frame {fr}")
        require(entry["S"]=="01F0" and push["S"]=="01EC" and
                rti["S"]==done["S"]=="01F0" and
                entry["resume"]==push["resume"]==done["resume"]=="82D4EE" and
                push["stack"]==done["stack"]=="26EED482",
                f"native NMI raw stack/frame identity changed frame {fr}")
        require(rti["opcodePC"]=="008588" and rti["returnPC"]=="808588" and
                done["PB"]=="80",f"native compiled RTI marker context changed frame {fr}")
        require(int(entry["master"])<=int(rd["master"])==
                int(rti["master"])==int(done["master"]),
                f"native own NMI master time regressed frame {fr}")
        require(rd["value"][-2:]==push["stack"][:2],
                "native actual status read differs from after-push raw byte")
        next_read=ev[i3+1] if len(ev)>i3+1 else None
        require(next_read is not None and next_read["stage"]=="read" and
                next_read["nmi"]=="0" and next_read["addr"]=="01F1" and
                next_read["value"]=="0026",
                f"native post-handler first stack helper read changed frame {fr}")
        src=original_frames[fr]
        require(src["original_raw_5_stack_bytes"].startswith("26"),
                "original source NMI status changed in same authentic case")
        brackets.append({
            "native_frame":fr,
            "native_after_push_seq":push["seq"],
            "native_after_push_raw_4_bytes":push["stack"],
            "native_resume_PC":push["resume"],
            "native_true_status_stack_helper_read_seq":rd["seq"],
            "native_true_status_stack_helper_read_value":rd["value"],
            "native_compiled_RTI_seq":rti["seq"],
            "native_compiled_RTI_opcodePC_field":rti["opcodePC"],
            "native_compiled_RTI_returnPC_field":rti["returnPC"],
            "native_handler_return_seq":done["seq"],
            "native_first_post_handler_stack_helper_read_seq":next_read["seq"],
            "native_saved_PC_or_PB_helper_reads_during_NMI":0,
            "original_guest_PC_context":src["original_guest_PC_context"],
            "original_post_real_NMI_raw_5_stack_bytes":src["original_raw_5_stack_bytes"],
            "original_native_PC_low_byte_differ_in_paired_host_frame":
                src["original_saved_PC_low"]!=int(push["stack"][2:4],16),
            "original_native_intra_frame_semantic_phase_proven_equal":False
        })
    comp={b["native_compiled_RTI_seq"] for b in brackets}
    return {
        "schema":SCHEMA,"native_RF047_event_count":len(events),
        "native_RF047_event_ordinals_contiguous":True,
        "native_RF047_other_logger_prefix_fragment_count":len(contaminated),
        "native_RF047_compiled_RTI_events_with_prefix_fragments":
            sum(e["seq"] in comp for e in contaminated),
        "native_RF047_atomic_event_payloads_recovered":True,
        "authentic_native_NMI_frame_count":len(brackets),
        "native_compiled_NMI_brackets_with_one_actual_status_helper_read":len(brackets),
        "native_saved_PC_or_PB_helper_reads_between_push_and_compiled_RTI":0,
        "source_original_NMI_status_26_all_nine":True,
        "source_original_native_NMI_saved_PC_low_differences":
            sum(b["original_native_PC_low_byte_differ_in_paired_host_frame"]
                for b in brackets),
        "native_RF044_legacy_read_log_can_be_fragmented":True,
        "compiled_RTI_opcodePC_field_is_qualified_actual_fetch_PC":False,
        "all_native_guest_bus_read_paths_observed":False,
        "original_native_same_intra_frame_semantic_phase_proven":False,
        "native_first_differing_stack_byte_consumer_proven":False,
        "cross_emulator_clocks_rebased":False,
        "accepted_complete_USA_events":0,
        "brackets":brackets
    }

def authenticated_case(path:Path)->dict:
    blob=path.read_bytes()
    require(hashlib.sha256(blob).hexdigest()==ARCHIVE_SHA256,
            "RF073 exact source/native case SHA256 mismatch")
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        require(len(names)==len(set(names)) and len(names)==18 and z.testzip() is None,
                "RF073 genuine archive integrity/member drift")
        native=z.read(NATIVE);original=z.read(ORIGINAL)
        require(hashlib.sha256(native).hexdigest()==NATIVE_SHA256 and
                hashlib.sha256(original).hexdigest()==ORIGINAL_SHA256,
                "RF073 true original/native log bytes differ")
        case=json.loads(z.read("case-result.json"))
    e=case["evidence"]
    require(case["disposition"]=="strict_candidate" and case["release_credit"]==0
            and e["original_event_frames"]==5163
            and e["next_bowl_bounded"]["fresh_native_entry_offset"]==267
            and e["next_bowl_bounded"]["fresh_original_entry_offset"]==267
            and e["native_frame_shift"]==0,
            "RF073 genuine original/native progression/source controls changed")
    r=inspect(native.decode("utf8"),original.decode("utf8"))
    r.update({
        "exact_authenticated_RF054_zip_sha256":ARCHIVE_SHA256,
        "actual_original_log_sha256":ORIGINAL_SHA256,
        "actual_native_log_sha256":NATIVE_SHA256,
        "source_commit_sha":case["source_sha"],
        "native_executable_sha256":e["native_sha256"],
        "original_core_sha256":e["core_sha256"],
        "ROM_sha256":e["rom_sha256"],
        "original_movie_sha256":e["movie_sha256"],
        "converted_guest_input_sha256":e["input_sha256"],
        "source_Zoo_result_relative_frames":5163,
        "next_Bowl_source_and_native_offset":267
    })
    return r

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=authenticated_case(a.archive)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("RF073 native compiled NMI status-helper bracket qualified; same-phase original/native HOLD")

if __name__=="__main__":main()
