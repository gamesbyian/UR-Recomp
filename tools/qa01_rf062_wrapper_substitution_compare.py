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
    from qa01_rf062_same_binary_ab import strictly_qualified_original_path_variation
    original=strictly_qualified_original_path_variation(r1.encode(),r2.encode())
    require(original["source_nonpath_log_equality_proven"],
            "original emulator actual execution differs outside exact working-directory paths")
    a=(wrapped/NATIVE).read_text()
    b=(control/NATIVE).read_text()
    require("QA01RF054NATIVEBUS_TRUNCATED" not in a+b and
            "QA01RF062NATIVE " not in a+b,
            "native helper trace truncated or runtime diagnostic logging enabled")
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
    # Do not turn a negative into a failing source producer. A *difference*
    # is scientifically informative, and must be retained for causal followup.
    return {
        "schema":SCHEMA, "original_native_same_source_rom_movie_inputs":True,
        "native_executables_differ_only_at_verified_generated_guest_site":True,
        "wrapped_native_executable_sha256":sha(wrapped_bin),
        "control_native_executable_sha256":sha(control_bin),
        "genuine_CPU_helper_count_unwrapped":len(unwrapped),
        "genuine_CPU_helper_count_wrapped":len(native),
        "ordered_helper_register_and_address_matches":matched,
        "first_observed_helper_edit":edits[0] if edits else None,
        "all_helper_observed_address_register_rows_equal":all_rows,
        "all_helper_native_local_master_cycles_equal":master,
        "original_nonpath_source_log_equal":True,
        "all_mesh_and_result_followthrough_control_equal":all(same_mesh.values()),
        "mesh_and_followthrough_components":same_mesh,
        "bounded_wrapper_substitution_noninterference_supported":
            all_rows and master and all(same_mesh.values()),
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
