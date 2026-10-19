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

def audit(nm_text:str, disassemblies:dict[str,str]) -> dict:
    groups=symbol_groups(nm_text)
    missing=[]
    for role,names in groups.items():
        for name in names:
            dump=disassemblies.get(name,"")
            if not dump or f"<{name}>:" not in dump:
                missing.append({"operation":role,"symbol":name,"reason":"disassembly missing"})
            elif GETENV.search(dump) is None:
                missing.append({"operation":role,"symbol":name,"reason":"missing original getset getenv guard"})
    if missing:
        raise ValueError("RF069 original ELF contains stale/uninstrumented getter/setter variants: "
                         + json.dumps(missing,sort_keys=True))
    return {
        "schema":"ur-qa01-rf069-original-ELF-getset-entry-guards/1",
        "original_executable_getset_variants":
            {role:names for role,names in groups.items()},
        "all_original_read_and_write_variants_have_probe_guard":True,
        "instrumented_RFO44_getset_header_compiled_into_all_visible_variants":True,
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
    for names in groups.values():
        for name in names:
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
    print("RF069 all linked source original read and write getset symbols contain a real probe guard; gameplay HOLD")

if __name__=="__main__":
    main()
