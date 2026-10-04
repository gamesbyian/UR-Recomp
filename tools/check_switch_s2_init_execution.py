#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def check(root=ROOT):
    errors=[]
    c=json.loads((root/"analysis/switch-s2-init-execution-contract.json").read_text())
    s=(root/"platform/switch/s2_execution_probe/source/main.c").read_text()
    for token in ("RtlRegisterGame(&kGameInfo)","SnesInit(","RtlRunFrame(0)","snes_state_digest_parts","hardware_observation_only=1","deterministic_parity_claim=0"):
        if token not in s: errors.append(f"missing execution-contract token: {token}")
    if c.get("checkpoints") != [0,1,60,120]: errors.append("checkpoint set drifted")
    if "compile/link/package only" not in c.get("ci_claim",""): errors.append("CI claim must remain compile-only")
    return errors
if __name__=="__main__":
    errors=check()
    [print("SWITCH_S2_EXEC_ERROR:",e) for e in errors]
    raise SystemExit(1 if errors else 0)
