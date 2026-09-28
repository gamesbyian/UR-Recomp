#!/usr/bin/env python3
"""Cheap guard against accidentally tracking obvious ROM-derived files."""
from __future__ import annotations
import subprocess
from pathlib import Path

BAD_EXT={".sfc",".smc",".fig",".swc",".rom",".srm",".state",".sav"}
BAD_PREFIX=("private/","generated/","src/gen/","assets/extracted/","assets/generated/")

def main():
    out=subprocess.check_output(["git","ls-files"],text=True,encoding="utf-8")
    bad=[]
    for raw in out.splitlines():
        path=raw.replace("\\","/")
        if Path(path).suffix.lower() in BAD_EXT or path.startswith(BAD_PREFIX):
            bad.append(path)
    if bad:
        print("Potentially unsafe tracked files:")
        for p in bad: print(" ",p)
        return 1
    print("Tracked-file hygiene check passed.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
