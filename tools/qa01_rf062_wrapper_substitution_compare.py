#!/usr/bin/env python3
"""Read-only frozen-source RF062 wrapped-vs-unwrapped native case comparator."""
import argparse
import hashlib
import json
import difflib
from pathlib import Path

SCHEMA="ur-qa01-rf062-native-wrapper-only-substitution/1"
IDENTITY=("rom_sha256","original_movie_sha256","original_movie_window_sha256",
          "input_sha256","reference_core_sha256","reference_script_sha256")
FIELDS=("addr","A","Y","D","dp63","dp64","dp65")
CONTROLS=("zoo_race_mesh","zoo_next_bowl_handoff",
          "source_terminal_followthrough")
OG="work/zoom-zoo/replay/reference.log"
NATIVE="work/zoom-zoo/replay/native.log"

def require(ok,reason):
    if not ok: raise ValueError(reason)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def events(text,prefix):
    rows=[]
    for line in text.splitlines():
        if line.startswith(prefix):
            vals=[p.split("=",1) for p in line.split()[1:] if "=" in p]
            require(len(vals)==len(dict(vals)),"duplicate actual helper fields")
            rows.append(dict(vals))
    return rows


def retained_memory_control(wrapped:Path,control:Path,source:dict,baseline:dict)->dict:
    from qa01_zoo_raw_archive_audit import CHECKPOINT_COUNT, BOWL_OFFSETS
    mesh=source.get("zoo_race_mesh",{}).get("samples",[])
    control_mesh=baseline.get("zoo_race_mesh",{}).get("samples",[])
    require(len(mesh)==len(control_mesh)==CHECKPOINT_COUNT==78,
            "missing 78 full frame raw original/native checkpoints")
    actual=[r.get("race_relative_frame") for r in mesh]
    require(actual==[r.get("race_relative_frame") for r in control_mesh]
            and actual==sorted(set(actual)) and actual[0]==0
            and actual[-1]==5120,
            "actual independent relative Zoo WRAM phases differ")
    handoff=source.get("zoo_next_bowl_handoff",{})
    control_handoff=baseline.get("zoo_next_bowl_handoff",{})
    require(handoff.get("sample_offsets")==list(BOWL_OFFSETS) and
            control_handoff.get("sample_offsets")==list(BOWL_OFFSETS),
            "source-earned original/native Bowl handoff population absent")
    tags=[("race-entered" if n==0 else f"scene-{n:05d}",n,"course")
          for n in actual]
    tags.extend((f"zoo-next-bowl-{n:03d}",n,"Bowl") for n in BOWL_OFFSETS)
    mismatches=[]
    files=0
    for label,num,phase in tags:
        for side in ("ref","native"):
            for kind,expected_size in (("wram",131072),("sram",8192)):
                base=Path("work")/"zoom-zoo"/"replay"/side/(label+"."+kind+".bin")
                left,right=wrapped/base,control/base
                require(left.is_file() and right.is_file() and
                        not left.is_symlink() and not right.is_symlink() and
                        left.stat().st_size==right.stat().st_size==expected_size,
                        "incomplete actual original/native full raw memory at "+str(base))
                a,b=left.read_bytes(),right.read_bytes()
                files+=2
                if a!=b:
                    mismatches.append({
                        "phase":phase,"offset":num,"guest":side,"memory":kind,
                        "number_of_changed_bytes":sum(x!=y for x,y in zip(a,b)),
                        "wrapped_sha256":hashlib.sha256(a).hexdigest(),
                        "unwrapped_sha256":hashlib.sha256(b).hexdigest(),
                    })
    return {
        "full_raw_images_independently_reopened":files,
        "unique_relative_race_frames":len(actual),
        "earned_Bowl_handoff_offsets":len(BOWL_OFFSETS),
        "original_and_native_exact_variant_raw_memory_equal":not mismatches,
        "first_12_between_variant_raw_memory_differences":mismatches[:12],
        "number_of_between_variant_raw_memory_differences":len(mismatches),
        "every_unsampled_CPU_opcode_or_frame_proven_equivalent":False,
    }


def compare(wrapped:Path,control:Path, static:Path,wrapped_bin:Path,
            control_bin:Path)->dict:
    source=json.loads((wrapped/"producer-report.json").read_text())
    baseline=json.loads((control/"producer-report.json").read_text())
    exactly=json.loads(static.read_text())
    require(exactly.get("schema")=="ur-qa01-rf062-wrapper-only-generated-c-diff/1" and
            exactly.get("only_one_live_generated_c_file_changed") is True,
            "genuine one-site compiled source comparison absent")
    require(all(source.get(k)==baseline.get(k) and isinstance(source.get(k),str)
                and source[k] for k in IDENTITY),
            "ROM/SMV/core/movie-window/real input identity differs")
    require(source.get("native_executable_sha256")==sha(wrapped_bin) and
            baseline.get("native_executable_sha256")==sha(control_bin) and
            sha(wrapped_bin)!=sha(control_bin),
            "actual two compiled native executables not authenticated and distinct")
    for guest, fn in (("original","ref.input"),("native","pinned-baldosa.input")):
        a=(wrapped/"work/zoom-zoo/replay"/fn).read_bytes()
        b=(control/"work/zoom-zoo/replay"/fn).read_bytes()
        require(a and a==b,"actual "+guest+" supplied controls not byte identical")
    r1=(wrapped/OG).read_text()
    r2=(control/OG).read_text()
    # From separately merged same-native-binary independent examiner.
    from qa01_rf062_same_binary_ab import (strictly_qualified_original_path_variation,
         strictly_qualified_native_logging_variation)
    original=strictly_qualified_original_path_variation(r1.encode(),r2.encode())
    require(original["source_nonpath_log_equality_proven"],
            "original emulator actual execution differs outside exact working-directory paths")
    a=(wrapped/NATIVE).read_text()
    b=(control/NATIVE).read_text()
    require("QA01RF054NATIVEBUS_TRUNCATED" not in a+b and
            "QA01RF062NATIVE " not in a+b,
            "native helper trace truncated or runtime diagnostic logging enabled")
    native_log_control=strictly_qualified_native_logging_variation(b.encode(),a.encode())
    native,unwrapped=events(a,"QA01RF054NATIVEBUS "),events(b,"QA01RF054NATIVEBUS ")
    for name,rows in (("wrapped",native),("unwrapped",unwrapped)):
        require(rows and [int(r["seq"]) for r in rows]==list(range(1,len(rows)+1))
                and all(r["frame"]=="6124" and r["kind"]=="read8" and
                        r["scope"]=="Snd_UploadBlockList_82EF_M1X0" for r in rows),
                name+" genuine CPU sound helper observation not qualified")
    left=[tuple(r[k] for k in FIELDS) for r in unwrapped]
    right=[tuple(r[k] for k in FIELDS) for r in native]
    ops=difflib.SequenceMatcher(None,left,right,autojunk=False).get_opcodes()
    matched=sum(i2-i1 for t,i1,i2,j1,j2 in ops if t=="equal")
    edits=[{"type":t,"unwrapped":[i1,i2],"wrapped":[j1,j2]}
           for t,i1,i2,j1,j2 in ops if t!="equal"]
    all_rows=len(native)==len(unwrapped)==matched
    master=all_rows and all(x["master"]==y["master"]
                            for x,y in zip(unwrapped,native))
    same_mesh={key:source.get(key)==baseline.get(key)
               and isinstance(source.get(key),dict)
               for key in CONTROLS}
    raw=retained_memory_control(wrapped,control,source,baseline)
    # Do not turn a negative into a failing source producer. A *difference*
    # is scientifically informative, and must be retained for causal followup.
    return {
        "schema":SCHEMA, "original_native_same_source_rom_movie_inputs":True,
        "generated_guest_code_only_one_sound_read_site_changed":True,
        "additional_native_runtime_helper_introduced_by_RF062":True,
        "wrapped_native_executable_sha256":sha(wrapped_bin),
        "control_native_executable_sha256":sha(control_bin),
        "genuine_CPU_helper_count_unwrapped":len(unwrapped),
        "genuine_CPU_helper_count_wrapped":len(native),
        "ordered_helper_register_and_address_matches":matched,
        "first_observed_helper_edit":edits[0] if edits else None,
        "all_helper_observed_address_register_rows_equal":all_rows,
        "all_helper_native_local_master_cycles_equal":master,
        "original_nonpath_source_log_equal":True,
        "native_nonhost_metadata_log_equal":native_log_control["all_other_native_lines_byte_equal_after_strict_host_metadata"],
        "native_log_control":native_log_control,
        "actual_full_original_native_raw_memory_between_variants":raw,
        "all_mesh_and_result_followthrough_control_equal":all(same_mesh.values()),
        "mesh_and_followthrough_components":same_mesh,
        "bounded_wrapper_substitution_noninterference_supported":
            all_rows and master and all(same_mesh.values()) and
            raw["original_and_native_exact_variant_raw_memory_equal"] and
            native_log_control["all_other_native_lines_byte_equal_after_strict_host_metadata"],
        "undetected_CPU_instructions_or_CPU_joypad_polls_equivalent_proven":False,
        "native_source_original_instruction_epoch_equal_proven":False,
        "sound_PCM_full_course_fidelity_proven":False,
        "accepted_USA_events":0
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--wrapped",type=Path,required=True)
    p.add_argument("--control",type=Path,required=True)
    p.add_argument("--static",type=Path,required=True)
    p.add_argument("--wrapped-binary",type=Path,required=True)
    p.add_argument("--control-binary",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=compare(a.wrapped,a.control,a.static,a.wrapped_binary,a.control_binary)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("RF062 exact wrapper-only guest replay",result["bounded_wrapper_substitution_noninterference_supported"],"; original/native USA acceptance 0")

if __name__=="__main__":main()
