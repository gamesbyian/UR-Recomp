#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def check(root:Path=ROOT)->list[str]:
    errors=[]
    c=json.loads((root/"analysis/switch-s2-executable-link-contract.json").read_text())
    src=(root/c["host_source"]).read_text()
    if c.get("gate")!="S2-executable-link": errors.append("wrong gate")
    for token in ("SnesInit","RtlRunFrame"):
        if token in src: errors.append(f"host must not start simulation: {token}")
    for token in c["host_contract"]["definitions"]:
        if token not in src: errors.append(f"host missing contract symbol: {token}")
    if "simulation_started=0" not in src: errors.append("probe must report simulation_started=0")
    return errors
if __name__=="__main__":
    e=check()
    [print("SWITCH_S2_LINK_ERROR:",x) for x in e]
    raise SystemExit(1 if e else 0)
