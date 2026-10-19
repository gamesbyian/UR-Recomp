#!/usr/bin/env python3
"""RF057: require authentic original CPU trace with identical historical guest images.

The original retail-USA 2014 Bowl three-guest baseline is RF056 archive
12151982503, unchanged and independently verified. No instruction or input
replay, no frame normalization, no masks. Fail if even one source original,
fresh original or native full WRAM/SRAM captured image differs.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path
import qa01_rf056_bowl_temporal_byte_transition_audit as rf056
import qa01_rf057_original_bowl_transition_cpu_report as rf057

BASELINE_SHA=rf056.ZIP_SHA
GUEST_PREFIXES=("bowl/replay/ref/","bowl/replay/native/","bowl/source/")
EXPECTED_ORIGINAL_NATIVE_IMAGES=48
EXPECTED_HISTORICAL_SOURCE_IMAGES=16
EXPECTED_TOTAL=EXPECTED_ORIGINAL_NATIVE_IMAGES+EXPECTED_HISTORICAL_SOURCE_IMAGES

def image_members(zip_file:zipfile.ZipFile)->set[str]:
    return {n for n in zip_file.namelist()
            if n.startswith(GUEST_PREFIXES) and
            (n.endswith(".wram.bin") or n.endswith(".sram.bin"))}

def compare_raw(a:dict[str,bytes],b:dict[str,bytes])->dict:
    if set(a)!=set(b) or len(a)!=EXPECTED_TOTAL:
        raise ValueError("RF057 missing or extra original/native/source movie raw guest images")
    source=guest=0
    for name in sorted(a):
        expected=131072 if name.endswith(".wram.bin") else 8192
        if len(a[name])!=expected or len(b[name])!=expected:
            raise ValueError("RF057 incomplete full unmasked WRAM/SRAM source image")
        if a[name]!=b[name]:
            raise ValueError("RF057 actual guest/sourcemovie raw image diverged: "+name)
        if name.startswith("bowl/source/"):source+=1
        else:guest+=1
    if guest!=EXPECTED_ORIGINAL_NATIVE_IMAGES or source!=EXPECTED_HISTORICAL_SOURCE_IMAGES:
        raise ValueError("RF057 guest/source raw image scope incomplete")
    return {"original_native_full_WRAM_SRAM_raw_images_exact":guest,
            "historical_source_movie_full_WRAM_SRAM_raw_images_exact":source,
            "unmasked_bytes_excluded":0}

def report(case:Path,baseline:Path)->dict:
    if hashlib.sha256(baseline.read_bytes()).hexdigest()!=BASELINE_SHA:
        raise ValueError("RF057 immutable RF056 source original baseline SHA256 changed")
    with zipfile.ZipFile(case) as z,zipfile.ZipFile(baseline) as q:
        source_log_name="bowl/replay/reference.log"
        if source_log_name not in z.namelist():
            raise ValueError("RF057 original source CPU log missing from genuine case")
        original=rf057.inspect(z.read(source_log_name).decode("utf8","replace"))
        new=json.loads(z.read("bowl-report.json"))
        old=json.loads(q.read("bowl-report.json"))
        for key in ("rom_sha256","original_movie_sha256",
                    "source_sram_sha256","input_sha256",
                    "bowl_next_switcher_handoff"):
            if key not in new or new[key]!=old[key]:
                raise ValueError("RF057 immutable original/native Bowl result/input/source differs: "+key)
        a={name:z.read(name) for name in image_members(z)}
        b={name:q.read(name) for name in image_members(q)}
        bytes_result=compare_raw(a,b)
    original.update(bytes_result)
    original["rf056_immutable_original_baseline_sha256"]=BASELINE_SHA
    original["rf057_new_case_sha256"]=hashlib.sha256(case.read_bytes()).hexdigest()
    original["original_game_cpu_sound_rom_controller_source_identity_preserved"]=True
    original["actual_cpu_read_of_joypad_hardware_registers_proven"]=False
    original["real_first_65816_transition_predicate_consumed_proven"]=False
    original["accepted_complete_USA_events"]=0
    return original

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("new_RF057_case",type=Path)
    ap.add_argument("--baseline",type=Path,required=True)
    ap.add_argument("--out",type=Path)
    x=ap.parse_args()
    s=json.dumps(report(x.new_RF057_case,x.baseline),indent=2,sort_keys=True)+"\n"
    if x.out:x.out.write_text(s,encoding="utf8")
    else:print(s,end="")
if __name__=="__main__":main()
