#!/usr/bin/env python3
"""QA01: independent immutable RF076 original fetched-PC vs native selected PC.

Source-only forensic consumer: no guest run, no timing normalization, no
first-consumed-byte or full-event acceptance claims. Original ZIPs expire.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import io
import json
import re
import stat
import zipfile
from pathlib import Path

CASE_SHA="402d3ee176307af4415fc24d579b00fb7c763996e02dfefe537f0c698b848b55"
BIN_SHA="713cac1696fdeacd4b079f3b53e768b879f5f7a506c77e2b617cf24e3452188d"
SOURCE_SHA="654aa6f7de100ff37f9133ae11039e7471a0456c"
ORIG_LOG_SHA="5940ec4b69f6b41fff4ae0af88925efc84d4b322286adb720cf429e0dfdf6dc7"
NATIVE_LOG_SHA="7f0c65060502ece76780978da19421d598037b17a476ccb2723e389eeec21c4c"
FIELDS=re.compile(r"([A-Za-z][A-Za-z0-9]*)=([^\s]+)")
ROW=re.compile(r"(\d+) (.*)\Z")
BINARY_ROW=re.compile(r"([0-9a-f]{64})  (snesref|native|snes9x_libretro[.]so)\Z")
FRAME_LABELS=range(1017,1026)

def need(ok, msg):
    if not ok:
        raise ValueError(msg)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def opened_zip(path, expected, expected_members, size_limit):
    need(path.is_file() and not path.is_symlink(), "missing/symlinked research ZIP")
    raw=path.read_bytes()
    need(0<len(raw)<32_000_000 and sha(raw)==expected, "original ZIP SHA256 mismatch")
    z=zipfile.ZipFile(io.BytesIO(raw))
    members=z.infolist()
    need(len(members)==expected_members and
         len({m.filename for m in members})==expected_members and
         sum(m.file_size for m in members)<size_limit, "original member population altered")
    for m in members:
        n=m.filename
        need(0<len(n)<512 and not m.is_dir() and not(m.flag_bits&1)
             and chr(92) not in n and ":" not in n and not n.startswith("/")
             and all(c not in ("",".","..") and not c.endswith((" ","."))
                     for c in n.split("/"))
             and all(ord(c)>=32 and ord(c)!=127 for c in n)
             and stat.S_IFMT(m.external_attr>>16) in (0,stat.S_IFREG)
             and m.file_size<20_000_000, "ambiguous, unsafe, or oversized ZIP member")
    need(z.testzip() is None, "original ZIP member CRC changed")
    return z

def read_events(raw, tag, count):
    rows=[]
    stages=collections.Counter()
    interleaved=collections.Counter()
    for line in raw.decode("utf8").splitlines():
        if tag not in line:
            continue
        need(line.count(tag)==1, "multiple event tags on one physical line")
        before,_,suffix=line.partition(tag)
        m=ROW.fullmatch(suffix)
        need(m is not None and int(m.group(1))==len(rows)+1,
             "noncontiguous or malformed real event seq")
        pairs=FIELDS.findall(m.group(2))
        need(bool(pairs) and " ".join(k+"="+v for k,v in pairs)==m.group(2),
             "truncated real event field")
        d=dict(pairs)
        need(len(pairs)==len(d) and int(d["f"]) in FRAME_LABELS,
             "duplicate event field or outside authentic bounded frame")
        d["seq"]=len(rows)+1
        rows.append(d)
        stages[d["stage"]]+=1
        if before:
            interleaved[d["stage"]]+=1
    need(len(rows)==count, "missing source-local event population")
    return rows,stages,interleaved

def inspect(case_path, binaries_path):
    with opened_zip(case_path,CASE_SHA,418,70_000_000) as c, \
         opened_zip(binaries_path,BIN_SHA,10,25_000_000) as b:
        classified=json.loads(c.read("case-result.json"))
        need(classified["source_sha"]==SOURCE_SHA and classified["case"]=="zoom-zoo"
             and classified["course_id"]=="course:02"
             and classified["disposition"]=="strict_candidate"
             and classified["release_credit"]==0, "foreign original/native execution identity")
        manifest=c.read("SHA256SUMS")
        need(manifest==b.read("SHA256SUMS"), "case and actual ELF manifest differ")
        actual={}
        for row in manifest.decode("ascii").splitlines():
            m=BINARY_ROW.fullmatch(row)
            need(m is not None and m.group(2) not in actual, "invalid ELF manifest")
            actual[m.group(2)]=m.group(1)
            need(sha(b.read(m.group(2)))==m.group(1), "original actual executable bytes changed")
        need(len(actual)==3
             and actual["native"]==classified["evidence"]["native_sha256"]
             and actual["snes9x_libretro.so"]==classified["evidence"]["core_sha256"],
             "actual binary hashes not tied to case")
        original=c.read("work/zoom-zoo/replay/reference.log")
        native=c.read("work/zoom-zoo/replay/native.log")
        need(sha(original)==ORIG_LOG_SHA and sha(native)==NATIVE_LOG_SHA,
             "immutable genuine original/native execution log changed")
        need(b"QA01RF076ORIGPC_TRUNCATED" not in original
             and b"QA01RF047NATIVE_TRUNCATED" not in native,
             "bounded source recorder truncated")
        orig,oc,om=read_events(original,"QA01RF076ORIGPC seq=",45063)
        nat,nc,nm=read_events(native,"QA01RF047NATIVE seq=",47853)
        need(oc==collections.Counter({"fetch":45045,"nmi_pending":9,"nmi_before":9})
             and not om, "original actual fetch/NMI source sequence or isolation changed")
        need(nc==collections.Counter({"opcode":45103,"read":2705,**{
             k:9 for k in ("entry","resume_origin","after_push","compiled_rti","handler_return")}})
             and nm==collections.Counter({"read":73,"compiled_rti":2}),
             "native original/source stage or physically mixed rows changed")
        source=json.loads(c.read("rf076-original-fetch.json"))
        native_verdict=json.loads(c.read("rf076-native-opcode-vs-scheduler.json"))
        ring=json.loads(c.read("rf074-native-resume-origin.json"))
        need(source["schema"]=="ur-qa01-rf076-original-true-fetched-PC-NMI-order/1"
             and source["source_events"]==len(orig)
             and source["source_observed_selected_actual_opcode_fetches"]==oc["fetch"]
             and source["source_observed_nmi_before_marker_count"]==9
             and source["complete_nine_original_NMI_frames_observed"] is True
             and source["missing_original_NMI_frames"]==[]
             and all(source[k] is False for k in (
                 "original_native_same_binary_source_epoch_proven",
                 "original_native_semantically_aligned_NMI_proven",
                 "first_differing_consumed_stack_byte_proven",
                 "original_opcode_fetches_unselected_sites_observed"))
             and source["accepted_USA_events"]==0, "original fetched-PC proof inflated")
        need(native_verdict["native_NMI_brackets"]==9
             and native_verdict["native_event_count"]==len(nat)
             and native_verdict["native_opcode_target_event_count"]==nc["opcode"]
             and native_verdict["same_semantic_phase_original_native_proven"] is False
             and native_verdict["first_differing_consumed_byte_proven"] is False
             and native_verdict["accepted_USA_events"]==0
             and ring["native_resume_assignment_bound_to_actual_NMI_before_push_count"]==9
             and ring["accepted_USA_events"]==0, "native selected marker promoted to guest parity")
        need(len(source["source_NMI_brackets"])==len(native_verdict["native_frames"])==9,
             "incomplete original/native nine-bracket source population")
        comparisons=[]
        for f,ob,nb in zip(FRAME_LABELS,
                           source["source_NMI_brackets"],native_verdict["native_frames"]):
            keys=("last_selected_original_opcode_fetch_before_NMI",
                  "original_NMI_wake_pending_event","original_NMI_before_push_event",
                  "first_selected_original_opcode_fetch_after_NMI")
            pre,pending,before,post=(ob[k] for k in keys)
            need([x["stage"] for x in (pre,pending,before,post)]==
                 ["fetch","nmi_pending","nmi_before","fetch"]
                 and all(x["original_host_frame"]==f for x in (pre,pending,before,post))
                 and [x["source_local_seq"] for x in (pre,pending,before,post)]==
                 list(range(pre["source_local_seq"],pre["source_local_seq"]+4)),
                 "actual original NMI source stage or opcode ordinal drift")
            for x in (pre,pending,before,post):
                actual_line=orig[x["source_local_seq"]-1]
                need(actual_line["stage"]==x["stage"] and int(actual_line["f"])==f
                     and actual_line["actualFetchedPC"]==x["source_guest_PC_context"]
                     and (actual_line.get("fetchedOpcode")==x["raw_fetched_opcode_if_fetch"]
                          if x["stage"]=="fetch" else x["raw_fetched_opcode_if_fetch"] is None),
                     "source original fetched PC report unsupported by actual log bytes")
            need(pending["waiting_for_interrupt"] is False
                 and before["waiting_for_interrupt"] is False
                 and ob["original_source_wake_incremented_PC"] is False
                 and ob["original_source_wake_pc_after"]==
                     ob["original_source_wake_pc_before"]==before["source_guest_PC_context"],
                 "original WAI wake/PC context altered")
            marker=nb["first_observed_target_opcode_after_handler_before_next_NMI"]
            need(nb["native_NMI_frame_label"]==f and
                 nb["scheduler_saved_resume_PC"]=="82D4EE"
                 and marker["frame"]==f and marker["decoded_guest_opcode_PC"]=="82D4EE"
                 and marker["actual_guest_emitter_tier"]=="aot",
                 "native post-RTI first selected opcode marker changed")
            need(post["source_guest_PC_context"] in ("82D4EE","82D4F0") and
                 post["raw_fetched_opcode_if_fetch"]==
                 ("24" if post["source_guest_PC_context"]=="82D4EE" else "10"),
                 "original decoded real opcode mismatch")
            comparisons.append({
                "matching_host_frame_label_only":f,
                "original_NMI_pending_PC":pending["source_guest_PC_context"],
                "original_real_first_selected_post_NMI_PC":post["source_guest_PC_context"],
                "original_real_opcode_byte":post["raw_fetched_opcode_if_fetch"],
                "native_first_selected_post_RTI_PC":marker["decoded_guest_opcode_PC"],
                "selected_host_label_PCs_unequal":post["source_guest_PC_context"]!="82D4EE",
                "original_PC_observation_ordinal":post["source_local_seq"],
                "native_PC_observation_ordinal":marker["seq"],
                "same_intraframe_semantic_phase_proven":False})
        unequal=[row["matching_host_frame_label_only"] for row in comparisons
                 if row["selected_host_label_PCs_unequal"]]
        need(unequal==[1017,1019,1021,1023], "real four-of-nine host-label mismatch altered")
        prefix="work/zoom-zoo/replay/"
        labels={name.split("/")[-1] for name in c.namelist()
                if name.startswith(prefix+"ref/") and name.endswith(".sram.bin")}
        need(len(labels)==97, "missing independently retained 97 paired SRAM images")
        for label in labels:
            a=c.read(prefix+"ref/"+label);bb=c.read(prefix+"native/"+label)
            need(len(a)==len(bb)==8192 and a==bb, "actual source/native SRAM differs")
        return {
            "schema":"ur-qa01-rf076-original-fetched-PC-source-archive/1",
            "original_case_ZIP_sha256":CASE_SHA,"original_binaries_ZIP_sha256":BIN_SHA,
            "actual_compiled_binary_sha256":actual,"exact_source_checkout_sha":SOURCE_SHA,
            "original_log_sha256":ORIG_LOG_SHA,"native_log_sha256":NATIVE_LOG_SHA,
            "original_actual_selected_opcode_fetch_count":oc["fetch"],
            "original_actual_nmi_brackets":9,"native_selected_opcode_markers":nc["opcode"],
            "native_NMI_brackets":9,"native_nonatomic_physical_RF047_rows":sum(nm.values()),
            "real_original_native_equal_raw_SRAM_pairs":97,
            "different_selected_post_NMI_PCs_at_matching_host_frame_labels":unequal,
            "per_host_frame_source_local_observations":comparisons,
            "original_native_semantic_phase_proven":False,
            "first_actually_consumed_differing_operand_proven":False,
            "full_unsampled_race_CPU_equivalence_proven":False,
            "Windows_disk_cold_recovery_proven":False,
            "accepted_USA_events":0,"release_QA_gates":0,"adjudication":"HOLD"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",required=True,type=Path)
    p.add_argument("--binaries",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    report=inspect(args.case,args.binaries)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("RF076 authenticated original 9 fetch/NMI and native 9 AOT brackets: four host-label differences, HOLD 0/45")

if __name__=="__main__":
    main()
