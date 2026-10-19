#!/usr/bin/env python3
"""RF069: fail closed if patched original Snes9x getset reads are stale in ELF.

2014 libretro Makefile only tracks %.cpp->%.o, NOT included getset.h.
An incremental build can mix stock read functions with patched stack writers
under LTO. This tool checks the *compiled ELF*, not merely header text.
Only acts on disposable original research binaries. Requires binutils.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

SYMBOLS = {
    "read_byte": "_Z10S9xGetBytej",
    "read_word": "_Z10S9xGetWordj9s9xwrap_t",
    "write_byte": "_Z10S9xSetBytehj",
    "write_word": "_Z10S9xSetWordtj9s9xwrap_t15s9xwriteorder_t",
}
TARGET_NM = re.compile(r"^[0-9a-fA-F]+\s+[TtWw]\s+(\S+)$", re.M)
GETENV = re.compile(r"\bcallq?\s+[^\n]*<getenv(?:@plt|@@[^>]*)?>")

def symbol_groups(nm_text: str) -> dict[str, list[str]]:
    syms=TARGET_NM.findall(nm_text)
    groups={name:sorted(set(s for s in syms if s==mangled or s.startswith(mangled+".")))
            for name,mangled in SYMBOLS.items()}
    if any(not group for group in groups.values()):
        raise ValueError("original Snes9x getter/setter function missing from linked ELF")
    return groups

# GCC/LTO is allowed to outline the source recorder into a static helper.
# A call to that exact ELF helper is only acceptable if its emitted machine
# code still contains BOTH RF044/RF063 environment guards, the RF063 shared
# ordinal update, and the actual source stderr writer.
HELPER_PREFIX="_ZL17ur_rf044_orig_busPKcjtj"
CALL_TARGET=re.compile(r"\bcallq?\s+[^\n]*<([^>]+)>")
RF063_GLOBAL=re.compile(r"<ur_rf063_source_bus_seq>")
REAL_PRINT=re.compile(r"<(?:__fprintf_chk|fprintf)(?:@plt)?>")

def audited_outlined_helpers(nm_text:str, disassemblies:dict[str,str])->list[str]:
    helpers=sorted(set(s for s in TARGET_NM.findall(nm_text)
                       if s==HELPER_PREFIX or s.startswith(HELPER_PREFIX+".")))
    allowed=[]
    for h in helpers:
        dump=disassemblies.get(h,"")
        # Under the pinned RF063 getset adapter these two getenv calls gate
        # RF044's existing logger and RF063's source-local event sequence.
        if (f"<{h}>:" in dump and len(GETENV.findall(dump))>=2 and
                RF063_GLOBAL.search(dump) and REAL_PRINT.search(dump)):
            allowed.append(h)
    return allowed

def audit(nm_text:str, disassemblies:dict[str,str]) -> dict:
    groups=symbol_groups(nm_text)
    helpers=set(audited_outlined_helpers(nm_text,disassemblies))
    missing=[]
    methods={}
    for role,names in groups.items():
        methods[role]={}
        for name in names:
            dump=disassemblies.get(name,"")
            if not dump or f"<{name}>:" not in dump:
                missing.append({"operation":role,"symbol":name,"reason":"disassembly missing"})
                continue
            if GETENV.search(dump):
                methods[role][name]="direct_getenv_guard"
                continue
            calls=set(CALL_TARGET.findall(dump))
            proven=sorted(calls.intersection(helpers))
            if proven:
                methods[role][name]="call_verified_outlined_original_RF044_RF063_recorder"
                continue
            missing.append({"operation":role,"symbol":name,
                            "reason":"no direct source probe guard or verified outlined helper call"})
    if missing:
        raise ValueError("RF069 original ELF contains stale/uninstrumented getter/setter variants: "
                         + json.dumps(missing,sort_keys=True))
    return {
        "schema":"ur-qa01-rf069-original-ELF-getset-entry-guards/2",
        "original_executable_getset_variants":
            {role:names for role,names in groups.items()},
        "verified_outlined_RF044_RF063_helper_symbols":sorted(helpers),
        "per_original_executable_variant_probe_mechanism":methods,
        "all_original_read_and_write_variants_have_probe_guard":True,
        "instrumented_RF044_RF063_getset_header_reachable_from_all_visible_variants":True,
        "guest_ROM_executed":False,
        "native_original_semantic_parity_proven":False,
        "actual_bus_read_attribution_proven":False,
        "accepted_USA_events":0,
    }

def inspect_elf(path: Path, *, nm="nm", objdump="objdump")->dict:
    if not path.is_file():
        raise ValueError("missing instrumented original binary")
    nmt=subprocess.run([nm,"-an",str(path)],check=True,
                       stdout=subprocess.PIPE,text=True).stdout
    groups=symbol_groups(nmt)
    disasm={}
    symbols={name for names in groups.values() for name in names}
    symbols.update(s for s in TARGET_NM.findall(nmt)
                   if s==HELPER_PREFIX or s.startswith(HELPER_PREFIX+"."))
    for name in sorted(symbols):
        disasm[name]=subprocess.run([objdump,"-d","--disassemble="+name,
                                     str(path)],check=True,
                                     stdout=subprocess.PIPE,text=True).stdout
    result=audit(nmt,disasm)
    result["instrumented_original_binary_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
    return result

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=inspect_elf(a.binary)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("RF069 original getter/setter entry probes verified via direct or fully audited outlined ELF recorder; gameplay HOLD")

if __name__=="__main__":
    main()
