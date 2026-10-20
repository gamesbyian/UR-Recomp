#!/usr/bin/env python3
"""Independent QA01 admission of RF080 real native event sidecar and STZ boundary.

Source-only. The complete actual original/native research ZIPs and executable
bytes must match pinned source identities. The sidecar is independently read:
malformed stderr is retained as a negative, never reconstructed or normalized.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

import qa01_rf079_bit_bpl_archive as qa

CASE_SHA = "e23139e64f75099a43c0c77b6c53f3c4c87c1afb17ae12f82448f05f878ac412"
BIN_SHA = "0f0baf99dac49e5e0e0edf4f09e28b3af3f89f3625250c7a0bda09cc7b9fdbd7"
SOURCE = "0873395628f3655916b072cf1cf12871537da6a1"
SIDECAR_SHA = "1cab9fd4f9384d2043394957cf794daf9187b7fae5dd3b4ab4e59615d88dd424"
STDERR_SHA = "0de2718c9aa339edca32c4c4881a8a79841f478dd2624121e4b13b7f5e4f153e"
ORIGINAL_LOG_SHA = "feba42a853b281b82b4430f3e9375edb7cb4421781c07e327ac2a1b0bf6cc050"
LEAF = re.compile(r"([a-f0-9]{64})  (snesref|native|snes9x_libretro[.]so)\Z")

def check(flag, reason):
    if not flag:
        raise ValueError(reason)

def digest(b):
    return hashlib.sha256(b).hexdigest()

def qualify_sidecar(raw):
    # The strict native stream must be an independent atomic physical line
    # stream. Unlike historic stderr, a partial RF044 prefix is an error here.
    check(digest(raw) == SIDECAR_SHA, "unqualified native event-sidecar SHA256")
    lines, rows, mixed = qa.physical_events(raw, qa.NTAG, 60819)
    check(len(lines) == len(rows) and not mixed
          and all(l.startswith(qa.NTAG) and l.count(qa.NTAG) == 1 for l in lines),
          "non-isolated source-native sidecar physical rows")
    stages = collections.Counter(row["stage"] for _, row in rows)
    expected = collections.Counter({"opcode":45103, "bit_real_return":6483,
            "bpl_actual_input":6483, "read":2705})
    expected.update({name:9 for name in
                     ("entry","resume_origin","after_push","compiled_rti","handler_return")})
    check(stages == expected, "actual native opcode/bit/branch count changed")
    for _, row in rows:
        if row["stage"] == "bit_real_return":
            check(row.get("guestPC") == "82D4EE" and row.get("D") == "0000"
                  and row.get("addr") == "0057" and row.get("value") in ("00","FF"),
                  "unqualified native paced BIT return")
        elif row["stage"] == "bpl_actual_input":
            check(row.get("guestPC") == "82D4F0" and row.get("N") in ("0","1")
                  and row.get("bitReadSeen") == "1",
                  "unqualified actual native BPL N input")
    return lines, rows, stages

def raw_byte_differences(original: bytes, native: bytes, expected_size: int):
    """Return every differing physical offset, without gameplay/stack masks."""
    check(len(original) == len(native) == expected_size,
          "missing or malformed complete original/native physical image")
    return [offset for offset,(a,b) in enumerate(zip(original,native)) if a != b]

def qualify(case_file: Path, binary_file: Path):
    with qa.source_zip(case_file, CASE_SHA, 200, 45_000_000) as case, \
         qa.source_zip(binary_file, BIN_SHA, 11, 25_000_000) as bins:
        c = json.loads(case.read("case-result.json"))
        check(c.get("source_sha") == SOURCE and c.get("case") == "zoom-zoo"
              and c.get("course_id") == "course:02"
              and c.get("release_credit") == 0
              and c.get("disposition") == "strict_candidate",
              "foreign original/native research origin")
        manifest=case.read("SHA256SUMS")
        check(manifest == bins.read("SHA256SUMS"), "nonidentical actual binary manifest")
        actual={}
        for line in manifest.decode("ascii").splitlines():
            m=LEAF.fullmatch(line)
            check(m is not None and m.group(2) not in actual, "foreign executable manifest")
            actual[m.group(2)]=m.group(1)
            check(digest(bins.read(m.group(2))) == m.group(1),
                  "actual compiled original/native binary SHA mismatch")
        check(len(actual) == 3 and actual["native"] == c["evidence"]["native_sha256"]
              and actual["snes9x_libretro.so"] == c["evidence"]["core_sha256"],
              "source/binary epoch mismatch")
        native_sidecar=case.read("rf079-native-rf047-strict.log")
        stderr=case.read("work/zoom-zoo/replay/native.log")
        original=case.read("work/zoom-zoo/replay/reference.log")
        check(digest(stderr) == STDERR_SHA and digest(original) == ORIGINAL_LOG_SHA,
              "historic stderr/original log bytes changed")
        check(b"QA01RF035NATIVE_TRUNCATED" in stderr
              and b"QA01RF047NATIVE_TRUNCATED" not in native_sidecar,
              "historic error or valid strict sidecar omitted")
        _, native, _=qualify_sidecar(native_sidecar)
        original_lines,orig,original_mixed=qa.physical_events(original,qa.OTAG,12958)
        check(not original_mixed, "unqualified original BIT/BPL physical rows")
        physical_stderr=[l for l in stderr.decode("utf8").splitlines()
                         if qa.NTAG in l]
        check(len(physical_stderr)==60819, "historic native stderr record count changed")
        mixed_stderr=collections.Counter()
        for l in physical_stderr:
            _,_,tail=l.partition(qa.NTAG)
            if not l.startswith(qa.NTAG):
                m=re.search(r"stage=([A-Za-z_]+)", tail)
                check(m is not None, "cannot count historic mixed physical row")
                mixed_stderr[m.group(1)]+=1
        check(mixed_stderr==collections.Counter({"read":73,"compiled_rti":2}),
              "raw native mixed physical rows were altered/silently repaired")
        checkpoints=[]
        for f in (1017,1018):
            original_after=qa.first_after(original_lines,orig,"stage=nmi_before",f,
                                          3 if f==1017 else 2)
            native_after=qa.first_after([l for l in native_sidecar.decode().splitlines()],
                                         native,"stage=handler_return",f,5)
            if f==1017:
                skipped,bit,bpl=original_after
                check(skipped["before"]=="82D4F0" and skipped["opcode"]=="10"
                      and skipped["after"]=="82D4EE"
                      and skipped["N"]=="0" and skipped["Nbyte"]=="00",
                      "original first opposite branch not actually observed")
            else:
                bit,bpl=original_after
            check(bit["before"]=="82D4EE" and bit["opcode"]=="24"
                  and bit["Nbyte"]=="FF" and bit["N"]=="1"
                  and bpl["before"]=="82D4F0" and bpl["opcode"]=="10"
                  and bpl["Nbyte"]=="FF" and bpl["N"]=="1"
                  and bpl["after"]=="82D4F2",
                  "original real executed BIT→BPL outcome changed")
            a,read,p,flag,next_pc=native_after
            check(a["stage"]=="opcode" and a["guestPC"]=="82D4EE"
                  and read["stage"]=="bit_real_return" and read["value"]=="FF"
                  and read["addr"]=="0057" and read["D"]=="0000"
                  and p["stage"]=="opcode" and p["guestPC"]=="82D4F0"
                  and flag["stage"]=="bpl_actual_input" and flag["N"]=="1"
                  and flag["bitReadSeen"]=="1" and next_pc["stage"]=="opcode"
                  and next_pc["guestPC"]=="82D4F2",
                  "native strict-sidecar BIT→BPL→STZ marker altered")
            checkpoints.append({
              "matching_host_frame_label_only":f,
              "original_additional_N0_BPL_cycle":f==1017,
              "original_source_post_BIT_Nbyte":"FF",
              "original_source_next_BPL_N":1,
              "original_source_next_PC":"82D4F2",
              "native_actual_paced_DP_0057_value":"FF",
              "native_BPL_negative_flag":1,
              "native_next_selected_PC":"82D4F2",
              "original_N_byte_is_postdispatch_not_raw_bus_return":True,
              "equivalent_original_native_instruction_phase_proven":False})
        root="work/zoom-zoo/replay/"
        samples={p.split("/")[-1] for p in case.namelist()
                 if p.startswith(root+"ref/") and p.endswith(".wram.bin")}
        check(len(samples)==44, "missing or extra sampled source original/native WRAM")
        all_differences=collections.Counter()
        exact_WRAM=0
        exact_SRAM=0
        for sample in samples:
            ref=case.read(root+"ref/"+sample)
            nat=case.read(root+"native/"+sample)
            changes=raw_byte_differences(ref,nat,131072)
            all_differences.update(changes)
            if not changes:
                exact_WRAM+=1
            check(all(ref[offset]==nat[offset] for offset in (0x57,0x59)),
                  "physical 0057/0059 sampled WRAM differed")
            suffix=sample.removesuffix(".wram.bin")
            old=case.read(root+"ref/"+suffix+".sram.bin")
            new=case.read(root+"native/"+suffix+".sram.bin")
            if not raw_byte_differences(old,new,8192):
                exact_SRAM+=1
        expected_differences={475:2,476:2,477:2,478:2,479:2,482:1,
                484:2,485:1,486:1,487:1,490:1,491:1,492:1,
                493:16,494:16,495:15,496:15,499:1}
        check(exact_WRAM==27 and exact_SRAM==44
              and all_differences==collections.Counter(expected_differences),
              "authentic 44 raw-pair WRAM/SRAM negative census altered")
        return {
          "schema":"ur-qa01-rf080-true-native-event-sidecar/1",
          "actual_case_zip_sha256":CASE_SHA,
          "actual_binary_zip_sha256":BIN_SHA,
          "original_native_source_checkout":SOURCE,
          "native_event_sidecar_sha256":SIDECAR_SHA,
          "native_stderr_sha256":STDERR_SHA,
          "original_log_sha256":ORIGINAL_LOG_SHA,
          "actual_binary_leaf_sha256":actual,
          "strict_native_sidecar_complete_isolated_ordinals":60819,
          "strict_native_actual_BIT_bus_return_events":6483,
          "strict_native_BPL_input_events":6483,
          "legacy_raw_stderr_mixed_physical_lines":75,
          "legacy_raw_stderr_RF035_truncation_retained":True,
          "source_local_branch_outcome_crosswalk":checkpoints,
          "paired_unmasked_full_WRAM_images":44,
          "fully_byte_equal_WRAM_pairs":exact_WRAM,
          "unequal_WRAM_pairs":44-exact_WRAM,
          "unmasked_full_WRAM_differing_byte_occurrences":sum(all_differences.values()),
          "all_unmasked_difference_address_occurrences":{
              f"7E:{offset:04X}":count for offset,count in sorted(all_differences.items())},
          "paired_full_original_native_SRAM_equal":exact_SRAM,
          "physical_WRAM_0057_0059_equal_sample_pairs":44,
          "original_actual_bus_read_0057_proven":False,
          "first_0059_STZ_writer_consumption_proven":False,
          "original_native_intraframe_phase_equivalence_proven":False,
          "continuous_original_native_Zoo_event_proven":False,
          "cold_Windows_PE_disk_persistence_proven":False,
          "accepted_USA_events":0,"accepted_Windows_gates":0,"adjudication":"HOLD"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",required=True,type=Path)
    p.add_argument("--binaries",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    verdict=qualify(a.case,a.binaries)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(verdict,sort_keys=True,indent=2)+"\n")
    print("RF080 real sidecar 60819/60819, sampled WRAM 44/44; first STZ writer HOLD 0/45")

if __name__=="__main__":
    main()
