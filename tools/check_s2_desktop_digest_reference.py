#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def check(root=ROOT):
    errors=[]
    c=json.loads((root/"analysis/s2-desktop-digest-reference-contract.json").read_text())
    s=(root/c["host_source"]).read_text()
    for token in ("RtlRegisterGame(&kGameInfo)","SnesInit(","RtlRunFrame(0)","snes_state_digest_parts"):
        if token not in s: errors.append(f"missing reference token: {token}")
    if c.get("checkpoints") != [0,1,60,120]: errors.append("checkpoint set drifted")
    if c.get("frames") != 120 or c.get("inputs") != 0: errors.append("fixture sequence drifted")
    return errors
if __name__=="__main__":
    e=check()
    [print("S2_REFERENCE_ERROR:",x) for x in e]
    raise SystemExit(1 if e else 0)
