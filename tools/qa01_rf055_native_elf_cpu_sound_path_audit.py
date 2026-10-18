#!/usr/bin/env python3
"""RF055: offline and read-only verification of actual native CPU ROM/port path.

Supply the genuine original/native Zoo case ZIP, its exact native binaries
ZIP and the RF047 baseline case ZIP. Does not execute a game, fetch a ROM,
change emulator timing, or infer a source-PC from the compiled function name.
Requires 'nm' and 'objdump' from binutils on Linux.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, tempfile, zipfile
from pathlib import Path

LOG = "work/zoom-zoo/replay/native.log"
NAME = "Snd_UploadBlockList_82EF_M1X0.part.0"
SCOPE = "Snd_UploadBlockList_82EF_M1X0"
READ = "QA01RF054NATIVEBUS kind=read8 "
WRITE = "QA01RF054NATIVE kind=writer "
CONTROLS = ("zoo_race_mesh", "zoo_next_bowl_handoff", "source_terminal_followthrough")
CASE_SHA = "18bfc0fd6c9efb4d0d849930aded4657f4d8079be065b0f0e294c08439dbb84a"
BINARY_SHA = "2b47a6596362c68d39f1b7d1ca8e9491ab7fa7d4cfd87b99b880404681139dc2"
ELF_SHA = "cac96d0ba41ce21eee5d310477ac1266c3fceea1490f7cb52ec98105db09db9e"
KV = re.compile(r"([a-zA-Z][a-zA-Z0-9_]*)=([^\s]+)")
ASM = re.compile(r"^\s*([0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{2}\s+)+)(.*)$")
SYM = re.compile(r"^([0-9a-fA-F]+)\s+\w\s+" + re.escape(NAME) + r"$")

def digest(v:bytes)->str:
    return hashlib.sha256(v).hexdigest()

def genuine_cpu_records(log:str)->tuple[list[dict],list[dict]]:
    if "QA01RF054NATIVE_TRUNCATED" in log or "QA01RF054NATIVEBUS_TRUNCATED" in log:
        raise ValueError("CPU original/native observer truncated")
    reads=[dict(KV.findall(s)) for s in log.splitlines() if s.startswith(READ)]
    writes=[dict(KV.findall(s)) for s in log.splitlines() if s.startswith(WRITE)]
    if len(reads)!=656 or len(writes)!=1312:
        raise ValueError("real source CPU read/write counts incomplete")
    for i,(rd,w3,w2) in enumerate(zip(reads,writes[::2],writes[1::2])):
        if (rd.get("kind")!="read8" or any(x.get("scope")!=SCOPE for x in (rd,w3,w2))
            or any(x.get("frame")!="6124" for x in (rd,w3,w2))):
            raise ValueError("native source execution scope/frame wrong")
        if (int(rd["seq"])!=i+1 or int(w3["seq"])!=2*i+1
            or int(w2["seq"])!=2*i+2
            or int(rd["addr"],16)!=0x11C589+i
            or int(rd["addr"],16)!=0x110000+int(rd["Y"],16)):
            raise ValueError("executed ROM operand/ordinal discontinuity")
        if ((w3["addr"],w2["addr"])!=("002143","002142")
            or any(x["Y"]!=rd["Y"] for x in (w3,w2))
            or any(x.get("dp63")!="00" or x.get("dp64")!="00"
                   or x.get("dp65")!="11" for x in (rd,w3,w2))):
            raise ValueError("actual CPU pointer or APU ports disagree")
        if (int(w3["master"])-int(rd["master"])!=30
            or int(w2["master"])-int(w3["master"])!=50
            or any((int(x["A"],16)&255)!=int(x["val"],16) for x in (w3,w2))):
            raise ValueError("executed native CPU data publication/timing discrepancy")
    if (reads[491]["addr"]!="11C774" or
        tuple(map(int,(reads[491]["master"],writes[982]["master"],writes[983]["master"])))
            !=(2188739002,2188739032,2188739082)):
        raise ValueError("exact original/native late source-matched sound transfer absent")
    return reads,writes

# Native ELF callsite sequence evidence is static. There are OTHER cpu_read8
# sites in this function: the RF054 bus logger did NOT capture return address.
PATH = (
    (0x6aeb39,"rol    dx,0x8"),
    (0x6aeb96,"call   3e270 <cpu_read16_paced>"),
    (0x6aebae,"call   3e040 <cpu_read8_paced>"),
    (0x6aebc3,"add    esi,eax"),
    (0x6aebcf,"call   3e040 <cpu_read8_paced>"),
    (0x6aec3e,"mov    edx,0x2143"),
    (0x6aec4a,"call   3e620 <cpu_write8_paced>"),
    (0x6aec79,"rol    cx,0x8"),
    (0x6aecb5,"mov    edx,0x2142"),
    (0x6aecc4,"call   3e620 <cpu_write8_paced>"),
)

def inspect_elf_text(nm:str,objdump:str)->list[dict]:
    matches=[int(m.group(1),16) for s in nm.splitlines() if (m:=SYM.match(s))]
    if matches!=[0x6aea70]:
        raise ValueError("native live mode-qualified function missing or changed")
    code={int(m.group(1),16):m.group(3).strip() for s in objdump.splitlines()
          if (m:=ASM.match(s))}
    for addr,insn in PATH:
        if insn not in code.get(addr,""):
            raise ValueError("native ELF AOT CPU indexed load/write call path changed")
    if sum("cpu_read8_paced" in s for s in code.values())<3:
        raise ValueError("native ELF competing helper codepaths unexpectedly absent")
    return [{"x86_va":f"0x{a:x}","operation":code[a]} for a,_ in PATH]

def inspect_paced_helper_timestamp_stage(read_dis:str,write_dis:str)->dict:
    """Actual x86 wrapper master-clock charge occurs before CPU bus helper.

    RF054 logs cpu_read8, and RtlApuWrite is downstream of cpu_write8.
    Neither is the start of an original 65816 instruction at a common epoch.
    """
    required={
        "read8":(read_dis,
                 (0x3e0f2,"mov    QWORD PTR [rbp+0x28],rax"),
                 (0x3e132,"jmp    3c4b0 <cpu_read8>")),
        "write8":(write_dis,
                  (0x3e6d5,"mov    QWORD PTR [rbp+0x28],rax"),
                  (0x3e716,"jmp    3d5b0 <cpu_write8>")),
    }
    out={}
    for name,(dis,store,dispatch) in required.items():
        code={int(m.group(1),16):m.group(3).strip() for line in dis.splitlines()
              if (m:=ASM.match(line))}
        if (store[0]>=dispatch[0] or store[1] not in code.get(store[0],"")
            or dispatch[1] not in code.get(dispatch[0],"")):
            raise ValueError("RF055 paced CPU master charge/order to actual bus helper changed")
        out[name]={
            "paced_wrapper_master_clock_store_va":f"0x{store[0]:x}",
            "subsequent_actual_CPU_memory_helper_jump_va":f"0x{dispatch[0]:x}",
            "cpu_master_cycles_advanced_before_actual_CPU_bus_helper":True,
        }
    return out

def audit(case:Path,binary:Path,baseline:Path)->dict:
    if digest(case.read_bytes())!=CASE_SHA or digest(binary.read_bytes())!=BINARY_SHA:
        raise ValueError("exact independently pinned source/binary artifact ZIP changed")
    with zipfile.ZipFile(case) as z,zipfile.ZipFile(baseline) as b:
        if len(z.namelist())!=18:
            raise ValueError("authentic original/native Zoo case truncated")
        r=json.loads(z.read("producer-report.json"))
        old=json.loads(b.read("producer-report.json"))
        if any(r[k]!=old[k] for k in CONTROLS):
            raise ValueError("full strict original/native Zoo/Bowl/earned SRAM controls drifted")
        c=json.loads(z.read("case-result.json"))
        if c.get("disposition")!="strict_candidate":
            raise ValueError("independent USA event acceptance unexpectedly changed")
        reads,writes=genuine_cpu_records(z.read(LOG).decode("utf8","replace"))
    with zipfile.ZipFile(binary) as z:
        elf=z.read("native")
    if digest(elf)!=ELF_SHA:
        raise ValueError("actual replay binary identity wrong")
    with tempfile.TemporaryDirectory() as td:
        f=Path(td)/"native"
        f.write_bytes(elf)
        nm=subprocess.run(["nm","-nC",str(f)],check=True,capture_output=True,text=True).stdout
        dis=subprocess.run(["objdump","-d","-M","intel","--disassemble="+NAME,str(f)],
                           check=True,capture_output=True,text=True).stdout
        read_dis=subprocess.run(
            ["objdump","-d","-M","intel","--disassemble=cpu_read8_paced",str(f)],
            check=True,capture_output=True,text=True).stdout
        write_dis=subprocess.run(
            ["objdump","-d","-M","intel","--disassemble=cpu_write8_paced",str(f)],
            check=True,capture_output=True,text=True).stdout
    return {
        "schema":"rf055-genuine-native-elf-cpu-upload-path-audit-v1",
        "case_sha256":CASE_SHA,"native_elf_sha256":ELF_SHA,
        "executed_ROM_read8":len(reads),"executed_CPU_port_writes":len(writes),
        "all_656_ROM_read_to_port3_CPU_master_clocks":30,
        "all_656_port3_to_port2_CPU_master_clocks":50,
        "compiled_live_mode_x86_call_path":inspect_elf_text(nm,dis),
        "real_cpu_helper_timestamp_stage":inspect_paced_helper_timestamp_stage(read_dis,write_dis),
        "full_RF047_strict_original_native_Zoo_Bowl_SRAM_controls_equal":True,
        "specific_x86_callsite_dynamically_stamped":False,
        "native_guest_instruction_PC_dynamically_stamped":False,
        "absolute_original_native_CPU_SPC_phase_registered":False,
        "independently_accepted_complete_USA_events":0,
    }

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    p.add_argument("--binary",type=Path,required=True)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    data=json.dumps(audit(a.case,a.binary,a.baseline),indent=2,sort_keys=True)+"\n"
    if a.out:a.out.write_text(data,encoding="utf8")
    else:print(data,end="")
if __name__=="__main__":main()
