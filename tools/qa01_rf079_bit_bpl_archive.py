#!/usr/bin/env python3
"""QA01: original RF079 BIT/BPL physical source evidence, never guest admission.

Verifies archived immutable executed ROM/core/native source bytes and exact
actual selected post-op/returned-opcode events. No emulator runs, no clock
alignment, no second guest reads, and no release credits.
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

CASE_SHA="2721255d5f642422e414ec42db68d950f19382cd9b061e7e71846acd102c82e1"
BIN_SHA="3566cf6b3d9e1abf054e3e86420087c4590544ff4650b07286c1c9efc5745086"
SOURCE_SHA="71b0e217b747295a58a343567c8c3f6e1bddf2f7"
ORIGINAL_LOG_SHA="bf36108b5fa45bd01e3be4983b7602b9b722bfc6d40d9a7b2da39ffdec59ae37"
NATIVE_LOG_SHA="105902f7dbcc8fe3ba2f3aebc6e29637c2eee769bf1dcc24773eca596e47fbd7"
FIELD=re.compile(r"([A-Za-z][A-Za-z0-9]*)=([^\s]+)")
ROW=re.compile(r"(\d+) (.*)\Z")
MANIFEST=re.compile(r"([a-f0-9]{64})  (snesref|native|snes9x_libretro[.]so)\Z")
OTAG="QA01RF079ORIG seq="
NTAG="QA01RF047NATIVE seq="

def require(flag,msg):
    if not flag:raise ValueError(msg)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def source_zip(path, expected_sha, expected_count, max_total):
    require(path.is_file() and not path.is_symlink(),"missing or symlinked immutable source")
    raw=path.read_bytes()
    require(0<len(raw)<32_000_000 and digest(raw)==expected_sha,"wrong exact source ZIP sha256")
    z=zipfile.ZipFile(io.BytesIO(raw))
    infos=z.infolist()
    require(len(infos)==expected_count and
            len({i.filename for i in infos})==expected_count and
            sum(i.file_size for i in infos)<max_total,
            "wrong genuine original ZIP population")
    for i in infos:
        n=i.filename
        require(0<len(n)<512 and not i.is_dir() and not(i.flag_bits&1)
                and not n.startswith("/") and chr(92) not in n and ":" not in n
                and all(x not in ("",".","..") and not x.endswith((" ","."))
                        for x in n.split("/"))
                and all(ord(c)>=32 and ord(c)!=127 for c in n)
                and stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG)
                and i.file_size<20_000_000,
                "unsafe special, ambiguous or oversized archive entry")
    require(z.testzip() is None,"source ZIP member CRC altered")
    return z

def physical_events(raw, tag, expected):
    lines=raw.decode("utf8").splitlines()
    events=[]
    mixed=collections.Counter()
    for index,line in enumerate(lines):
        if tag not in line:continue
        require(line.count(tag)==1,"ambiguous duplicate source event tag")
        prefix,_,suffix=line.partition(tag)
        m=ROW.fullmatch(suffix)
        require(m is not None and int(m.group(1))==len(events)+1,
                "noncontiguous or malformed real event sequence")
        tokens=FIELD.findall(m.group(2))
        require(bool(tokens) and " ".join(k+"="+v for k,v in tokens)==m.group(2),
                "malformed source observation field list")
        row=dict(tokens)
        require(len(row)==len(tokens),"duplicate source event field")
        row["seq"]=len(events)+1
        events.append((index,row))
        if prefix:mixed[row.get("stage","post_op")]+=1
    require(len(events)==expected,"missing actual retained source records")
    return lines,events,mixed

def first_after(lines,events,marker,frame,limit):
    hits=[i for i,l in enumerate(lines) if marker in l and
          "f="+str(frame)+" " in l]
    require(len(hits)==1,"missing or duplicate physical NMI boundary")
    nmi_line=hits[0]
    later=[(i,row) for i,row in events
           if i>nmi_line and row.get("f")==str(frame)]
    require(len(later)>=limit,"actual observed post-NMI source records absent")
    return [r for _,r in later[:limit]]

def inspect(case_zip, binary_zip):
    with source_zip(case_zip,CASE_SHA,199,45_000_000) as c, \
         source_zip(binary_zip,BIN_SHA,11,25_000_000) as b:
        case=json.loads(c.read("case-result.json"))
        require(case.get("source_sha")==SOURCE_SHA and
                case.get("case")=="zoom-zoo" and
                case.get("course_id")=="course:02" and
                case.get("release_credit")==0 and
                case.get("disposition")=="strict_candidate",
                "foreign case/binary execution origin or false release credit")
        original_manifest=c.read("SHA256SUMS")
        require(original_manifest==b.read("SHA256SUMS"),
                "case and binary executable SHA256SUMS disagree")
        leaves={}
        for line in original_manifest.decode("ascii").splitlines():
            m=MANIFEST.fullmatch(line)
            require(m is not None and m.group(2) not in leaves,
                    "foreign or repeated compiled executable")
            leaves[m.group(2)]=m.group(1)
            require(digest(b.read(m.group(2)))==m.group(1),
                    "actual compiled executable bytes mismatch")
        require(len(leaves)==3 and
                case["evidence"]["native_sha256"]==leaves["native"] and
                case["evidence"]["core_sha256"]==leaves["snes9x_libretro.so"],
                "genuine source/binary epoch not bound")
        orig=c.read("work/zoom-zoo/replay/reference.log")
        native=c.read("work/zoom-zoo/replay/native.log")
        require(digest(orig)==ORIGINAL_LOG_SHA and digest(native)==NATIVE_LOG_SHA,
                "original actual replay logs changed")
        require(b"QA01RF079ORIG_TRUNCATED" not in orig and
                b"QA01RF047NATIVE_TRUNCATED" not in native,
                "genuine bounded observer overflow")
        ol,oe,om=physical_events(orig,OTAG,12958)
        nl,ne,nm=physical_events(native,NTAG,60819)
        require(not om and
                collections.Counter(r["f"] for _,r in oe)==
                collections.Counter({"1017":6458,"1018":6500}) and
                collections.Counter(r["opcode"] for _,r in oe)==
                collections.Counter({"24":6479,"10":6479}) and
                all(r["D"]=="0000" and r["M"]=="1" and
                    r["Nbyte"] in ("00","FF") and r["N"] in ("0","1")
                    and r["phase"]=="after_real_guest_opcode"
                    for _,r in oe),
                "original post-executed actual BIT/BPL source population changed")
        stages=collections.Counter(r.get("stage") for _,r in ne)
        expected={"opcode":45103,"read":2705,"bit_real_return":6483,
                  "bpl_actual_input":6483}
        expected.update({x:9 for x in
                         ("entry","resume_origin","after_push","compiled_rti","handler_return")})
        require(stages==collections.Counter(expected) and
                nm==collections.Counter({"read":73,"compiled_rti":2}),
                "native source population or 75 physical mixed rows changed")
        per_frame=[]
        for frame in (1017,1018):
            before=first_after(ol,oe,"stage=nmi_before",frame,3 if frame==1017 else 2)
            after=first_after(nl,ne,"stage=handler_return",frame,5)
            if frame==1017:
                a,bit,branch=before
                require(a["before"]=="82D4F0" and a["opcode"]=="10"
                        and a["after"]=="82D4EE" and a["N"]=="0" and
                        a["Nbyte"]=="00", "original extra BPL-to-BIT cycle absent")
            else:
                bit,branch=before
            require(bit["before"]=="82D4EE" and bit["opcode"]=="24"
                    and bit["after"]=="82D4F0" and bit["Nbyte"]=="FF"
                    and bit["N"]=="1" and branch["before"]=="82D4F0"
                    and branch["opcode"]=="10" and branch["N"]=="1"
                    and branch["Nbyte"]=="FF" and branch["after"]=="82D4F2",
                    "original BIT N=1/BPL fallthrough unproven")
            first,returned,following,used,next_pc=after
            require(first["stage"]=="opcode" and first["guestPC"]=="82D4EE"
                    and first["tier"]=="aot" and returned["stage"]=="bit_real_return"
                    and returned["guestPC"]=="82D4EE" and
                    returned["D"]=="0000" and returned["addr"]=="0057"
                    and returned["value"]=="FF" and
                    following["stage"]=="opcode" and following["guestPC"]=="82D4F0"
                    and used["stage"]=="bpl_actual_input" and
                    used["guestPC"]=="82D4F0" and used["N"]=="1"
                    and used["bitReadSeen"]=="1" and
                    next_pc["stage"]=="opcode" and next_pc["guestPC"]=="82D4F2",
                    "native actual BIT return/BPL negative flag unqualified")
            per_frame.append({
                "matching_host_label_only":frame,
                "original_first_post_NMI_selected_PC":("82D4F0" if frame==1017 else "82D4EE"),
                "original_extra_N0_branch_before_BIT":frame==1017,
                "original_post_BIT_65816_Nbyte":"FF",
                "original_next_BPL_negative_flag":1,
                "original_BPL_falls_through_to_PC":"82D4F2",
                "native_actual_paced_DP_0057_return":"FF",
                "native_BPL_N_after_BIT":1,
                "native_selected_BPL_fallthrough_PC":"82D4F2",
                "instruction_time_original_native_read_parity_proven":False
            })
        return {
            "schema":"ur-qa01-rf079-real-bit-bpl-original-native-archive/1",
            "case_sha256":CASE_SHA,"compiled_binary_zip_sha256":BIN_SHA,
            "execution_source_checkout_sha":SOURCE_SHA,
            "actual_compiled_executable_sha256":leaves,
            "original_log_sha256":ORIGINAL_LOG_SHA,"native_log_sha256":NATIVE_LOG_SHA,
            "original_post_instruction_observations":len(oe),
            "native_source_local_RF047_observations":len(ne),
            "native_direct_page_bit_return_observations":stages["bit_real_return"],
            "native_BPL_flag_input_observations":stages["bpl_actual_input"],
            "native_interleaved_physical_lines":sum(nm.values()),
            "bounded_post_NMI_branch_convergence":per_frame,
            "actual_original_bus_read_DP_0057_proven":False,
            "same_intraclock_original_native_NMI_phase_proven":False,
            "first_causally_consumed_differing_guest_byte_proven":False,
            "entire_unsampled_USA_Zoo_event_qualified":False,
            "shipping_Windows_PE_and_cold_disk_durability_proven":False,
            "accepted_USA_events":0,"accepted_Windows_gates":0,"adjudication":"HOLD"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",type=Path,required=True)
    p.add_argument("--binaries",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=inspect(a.case,a.binaries)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("Source-original and native RF079 BIT/BPL branch outcome bounded; first consumed byte HOLD, 0/45")

if __name__=="__main__":
    main()
