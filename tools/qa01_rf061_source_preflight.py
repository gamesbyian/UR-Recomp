#!/usr/bin/env python3
"""Fail-closed RF061 preflight against pinned, disposable Baldosa v2 sources.

Runs BEFORE expensive native regeneration or authentic Zoo replay. Source
staging being valid does not prove generated live M1X0 markers executed.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import qa01_rf047_executed_guest_pc_witness as witness

EXPECTED_EMITTER="075fbe4c8e0d97b0013be541795c39cb644a9709"
SKIP='            if ii in skip_emit_idx:\n'
CONTINUE='                continue\n'
IR='            for op in ir_ops:\n'


def inspect(root: Path) -> dict:
    emitter=root/witness.EMITTER
    bridge=root/witness.BRIDGE
    beam=root/witness.BEAM
    if not all(p.is_file() for p in (emitter,bridge,beam)):
        raise ValueError("missing pinned disposable Baldosa sources")
    src=emitter.read_text()
    ir=bridge.read_text()
    nmi=beam.read_text()
    if witness.STAMP in src or witness.STAMP in ir or witness.STAMP in nmi:
        raise ValueError("RF061 executed-PC already staged: preflight clean original sources")
    ast.parse(src)
    # A valid hook inserted at the wrong scope might compile and NEVER execute.
    # Require the skipped synthetic instruction to continue first, then the
    # original instruction's clock charge and real IR exactly once in order.
    if not (src.count(SKIP)==1 and
            src.find(CONTINUE,src.index(SKIP))<src.index(witness.EMITTER_SITE)<
            src.index(IR) and src.count(witness.EMITTER_SITE)==1):
        raise ValueError("Baldosa decoded-instruction execution-loop structure changed")
    if "for ii, (di_insn, ir_ops) in enumerate(pairs):" not in src:
        raise ValueError("decoded instruction pair iterator missing")
    if nmi.count("static void ur_rf047_nmi_snapshot(const char *stage, uint32_t vector) {")!=1:
        raise ValueError("RF047 base NMI recorder not staged")
    transformed=witness.patch(nmi,src,ir)
    ast.parse(transformed[1])
    c=transformed[1]
    call='ur_rf047_mark_executed_pc(0x{di_insn.addr & 0xFFFFFF:06X}u, 1u);'
    if c.count(call)!=1 or not (c.index(SKIP)<c.index(call)<c.index(IR)):
        raise ValueError("executed-PC patch did not land before original IR")
    if not all(f"0x{pc:06X}" in c for pc in witness.TARGET_PCS):
        raise ValueError("target PCs absent from emitted live-mode instrument")
    return {
        "schema":"ur-qa01-rf061-source-preflight/1",
        "expected_upstream_snesrecomp_commit":EXPECTED_EMITTER,
        "emitter_sha256":hashlib.sha256(src.encode()).hexdigest(),
        "bridge_sha256":hashlib.sha256(ir.encode()).hexdigest(),
        "native_NMI_observer_sha256":hashlib.sha256(nmi.encode()).hexdigest(),
        "actual_decoded_PC_site_source_staging_valid":True,
        "all_MX_variants_generated_and_executed":False,
        "live_Snd_UploadBlockList_82EF_M1X0_marker_executed":False,
        "first_actual_bus_read_guest_PC_bound":False,
        "accepted_USA_events":0
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    v=inspect(a.root.resolve())
    rendered=json.dumps(v,sort_keys=True,indent=2)+"\n"
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(rendered)
    else:
        print(rendered,end="")


if __name__=="__main__":
    main()
