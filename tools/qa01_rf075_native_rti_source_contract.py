#!/usr/bin/env python3
"""RF075: source-pinned compiled vs interpreted 65816 RTI semantics.

No SNES ROM execution. The codegen's compiled RTI consumes P but SKIPS the
stacked PC/PB loads; the interpreted RTI ACTUALLY pulls P, PC, PB. The host
scheduler owns the compiled continuation. This difference is a *conditional*
fidelity risk, never itself proof of a consumed differing byte or event pass.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

UPSTREAM="075fbe4c8e0d97b0013be541795c39cb644a9709"
FILES={
 "compiled_codegen":("recompiler/v2/codegen.py","e9e2b0f816f40d79d816f7189980f6f40d123c46"),
 "interpreted_cpu":("runner/src/snes/interp816.c","484b3f017b4077521dc6fc7dc54ea99ed23c54aa"),
 "interrupt_push":("runner/src/cpu_state.h","bfc90ab8b6409224e505ef34b2c10a11aa3e12f4"),
 "host_frame_driver":("runner/src/beam_frame_driver.c","769bd864cf08ed1d1b652b6d5d548b87b256a236"),
 "native_bridge":("runner/src/snes/interp_bridge.c","23d8621887eeeb8d77619197335ac5b977151a75"),
}

def require(condition:bool,message:str)->None:
    if not condition: raise ValueError(message)

def excerpt(s:str,left:str,right:str,name:str)->str:
    require(s.count(left)==1,f"RF075 ambiguous/missing {name} start")
    region=s.split(left,1)[1]
    require(right in region,f"RF075 missing {name} end")
    return region.split(right,1)[0]

def verify(codegen:str,interpreter:str,stack:str,beam:str,bridge:str)->dict:
    out=excerpt(codegen,"def _emit_return(op: Return) -> List[str]:",
                "    # ── Option-1 cpu->S return-frame ABI (RTS / RTL) ──", "compiled Return")
    rti=excerpt(out,"    if op.interrupt:\n","        ]\n","compiled RTI") + "        ]\n"
    require(rti.count('cpu_read8(cpu, 0x00, cpu->S)')==1 and
            'cpu->P = cpu_read8(cpu, 0x00, cpu->S)' in rti and
            'cpu_p_to_mirrors(cpu);' in rti and
            'cpu->S + 2' in rti and
            'if (!cpu->emulation) cpu->S = (uint16)(cpu->S + 1)' in rti and
            'return RECOMP_RETURN_NORMAL;' in rti,
            "RF075 compiled RTI no longer has exact one-status-read, discarded PC/PB stack ABI")
    require('cpu->PC' not in rti and 'cpu->PB =' not in rti and
            'cpu_dispatch_pc' not in rti,
            "RF075 compiled RTI unexpectedly uses restored guest PC/PB")
    interpreted=excerpt(interpreter,"    case 0x40: { // rti imp",
                        "    case 0x41:","interpreted RTI")
    require("interp816_setFlags(cpu, interp816_pullByte(cpu));" in interpreted and
            "cpu->pc = interp816_pullWord(cpu);" in interpreted and
            "cpu->k = interp816_pullByte(cpu);" in interpreted and
            interpreted.index("interp816_pullByte(cpu)") <
            interpreted.index("interp816_pullWord(cpu)") <
            interpreted.rindex("interp816_pullByte(cpu)"),
            "RF075 interpreted RTI no longer genuinely restores stacked P/PC/PB")
    pushed=excerpt(stack,"static inline void cpu_push_interrupt_frame_at(CpuState *cpu, uint32 pc24) {",
                   "/* Generated host-C control flow", "native interrupt push")
    require(pushed.count("cpu_write8(cpu, 0x00, cpu->S,")==4 and
            'cpu_mirrors_to_p(cpu);' in pushed and
            "(uint8)(pc24 >> 16)" in pushed and
            "(uint8)(pc24 >> 8)" in pushed and
            "(uint8)pc24" in pushed and
            "cpu->P" in pushed,
            "RF075 architectural NMI stack entry frame changed")
    driver=excerpt(beam,"static void run_interrupt(uint32_t vector, uint64_t deadline) {",
                   "void snes_beam_frame_driver_run_frame(void)", "actual host NMI call")
    a=driver.find("cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);")
    b=driver.find("interp_bridge_run_interrupt(&g_cpu, vector);")
    c=driver.find("update_resume_pc();")
    require(0<=a<b<c and driver.count("cpu_push_interrupt_frame_at(")==1 and
            "cpu_read8(" not in driver and "cpu->PC" not in driver,
            "RF075 host frame driver NMI push/guest interrupt/continuation order changed")
    native=excerpt(bridge,"static int bridge_native_handoff(CpuState *cpu, Interp816 *in,",
                   "/* " if False else "    if (s_lle_unwind_active) {", "native compiled RTI handoff")
    require("cpu_dispatch_pc_from(cpu, target, cpu->S, target)" in native and
            "if (stop_on_rti)\n            return 1;" in native and
            'sync_cpu_to_interp(cpu, in);' in native,
            "RF075 compiled RTI host return path changed")
    interpreter_stop=excerpt(bridge,"if (stop_on_rti && op == 0x40) {",
                             "        /* Resolved-landing capture","interpreter RTI boundary")
    require("sync_interp_to_cpu(&in, cpu);" in interpreter_stop and
            "return 1;" in interpreter_stop,
            "RF075 interpreted genuine RTI completion no longer returns at NMI boundary")
    return {
      "schema":"ur-qa01-rf075-original-source-native-RTI-ABI-static-contract/1",
      "pinned_upstream_snesrecomp":UPSTREAM,
      "compiled_RTI_guest_status_load_count":1,
      "compiled_RTI_guest_saved_PC_load_count":0,
      "compiled_RTI_guest_saved_PB_load_count":0,
      "compiled_RTI_guest_PC_PB_discarded_by_stack_advance":True,
      "compiled_RTI_returns_via_host_C_control_flow":True,
      "interpreted_RTI_stacked_status_PC_PB_restored":True,
      "interrupt_push_writes_actual_provided_resume_PC_bytes":True,
      "host_interrupt_push_before_dispatch_before_scheduler_resume_update":True,
      "potential_compatibility_condition":
          "if guest rewrites stacked PC/PB or host resume PC differs from architectural interruption continuation, compiled C-return cannot follow the byte-restored guest return target",
      "any_such_guest_stack_rewrite_actually_observed":False,
      "original_native_equivalent_interruption_instruction_phase_proven":False,
      "native_actual_fetched_opcode_pc_proven":False,
      "first_actually_consumed_differing_byte_proven":False,
      "all_gameplay_frames_equal":False,
      "accepted_USA_events":0,
      "accepted_Windows_QA_gates":0,
    }

def git_blob_sha(blob:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()

def inspect_root(root:Path)->dict:
    src={}
    observed={}
    for role,(path,expected) in FILES.items():
        raw=(root/path).read_bytes()
        actual=git_blob_sha(raw)
        require(actual==expected, f"RF075 pinned Baldosa source blob drift: {path}")
        src[role]=raw.decode("utf8")
        observed[path]=actual
    result=verify(src["compiled_codegen"],src["interpreted_cpu"],
                  src["interrupt_push"],src["host_frame_driver"],
                  src["native_bridge"])
    result["exact_upstream_source_git_blobs"]=observed
    result["pinned_all_five_unmodified_source_blobs_verified"]=True
    return result

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True,
                   help="Exact disposable Baldosa/snesrecomp at pinned commit")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    report=inspect_root(a.root.resolve())
    encoded=json.dumps(report,sort_keys=True,indent=2)+"\n"
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(encoded)
    else:
        print(encoded,end="")
    print("RF075 compiled RTI vs interpreted RTI distinct; first native differing-value consumer remains HOLD")

if __name__=="__main__":
    main()
