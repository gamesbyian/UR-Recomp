#!/usr/bin/env python3
"""RF056: independent raw 128KiB Bowl original/native transition-delta audit.

Read the *existing* source-authentic three-guest USA Bowl artifact ZIP. Never
replay frames, mask bytes, shift actual controller inputs, adjust the CPU/APU,
rewrite guest memory, or grant release/USA event acceptance. Cross-frame pairs
are a diagnostic comparison across previously recorded unchanged executions.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path

SOURCE_SHA="d8fc9099ea2827c6a919ec01bd2c49472701803c"
ZIP_SHA="c2262b40e43b4e167cbdf291623b0e34207561187e103af39eca7a46fa4b0edc"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
MOVIE_SHA="06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442"
SRAM_SHA="a6af0ddf25ae5feafba301100938f5ef81137ee76dcdc483a04fb6e961347828"
FRAMES=(334,338,339,340,341,342,343,344,345,346,349,354)
MOVIE_FRAMES=(334,339,340,341,342,343,344,354)
MENU={0xC6:(1,0),0xC8:(5,4)}
SRAM_DIFF={0xEF6:(1,0),0xF31:(1,0),0xF33:(5,4)}
W_BYTES=131072
S_BYTES=8192

def full_diff(a:bytes,b:bytes)->list[tuple[int,int,int]]:
    if len(a)!=len(b):raise ValueError("raw full-image byte lengths unequal")
    return [(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y]

def transitions(before:bytes,after:bytes)->list[tuple[int,int,int]]:
    """Every genuine byte mutation, not a masked/selected consumer."""
    return full_diff(before,after)

def certify(ref:dict[int,bytes],native:dict[int,bytes],
            sref:dict[int,bytes],snative:dict[int,bytes],
            movie:dict[int,bytes],smovie:dict[int,bytes])->dict:
    for label,groups,expected in (
            ("WRAM",(ref,native,movie),W_BYTES),
            ("SRAM",(sref,snative,smovie),S_BYTES)):
        for group in groups:
            if any(len(v)!=expected for v in group.values()):
                raise ValueError("RF056 incomplete genuine full "+label+" snapshots")
    if set(ref)!=set(FRAMES) or set(native)!=set(FRAMES):
        raise ValueError("Bowl original/native independent exact offset set incomplete")
    if set(movie)!=set(MOVIE_FRAMES) or set(smovie)!=set(MOVIE_FRAMES):
        raise ValueError("actual historical source-movie offset set incomplete")
    for f in FRAMES:
        if {x:(a,b) for x,a,b in full_diff(sref[f],snative[f])}!=SRAM_DIFF:
            raise ValueError("unmasked original/native earned Bowl SRAM changed")
    # Source 2014 movie already differs from the fresh original at +334;
    # never attribute its historical +342 entry to the native clock alone.
    if (len(full_diff(movie[334],ref[334]))!=44 or
            len(full_diff(smovie[334],sref[334]))!=71):
        raise ValueError("2014 movie and fresh original are wrongly conflated")
    if any(ref[f]!=ref[334] for f in (338,339)):
        raise ValueError("fresh original pre-transition state unexpectedly changed")
    if any(native[f]!=native[334] for f in (338,339,340,341,342)):
        raise ValueError("fresh native pre-transition state unexpectedly changed")
    for f,amount in ((334,2),(339,2),(340,33),(341,666),(342,688),(343,671),(344,289)):
        if len(full_diff(ref[f],native[f]))!=amount:
            raise ValueError("same-frame original/native strict progression negative changed")
    matched={}
    for original,guest,expected in ((340,343,2),(341,344,2),
                                     (342,345,6),(343,346,2)):
        diffs=full_diff(ref[original],native[guest])
        if len(diffs)!=expected:
            raise ValueError("cross-frame actual raw guest matching regressed")
        if original in (340,341,343) and {i:(a,b) for i,a,b in diffs}!=MENU:
            raise ValueError("cross-frame mismatch includes non-menu data")
        if original==342 and {i for i,_,_ in diffs}!={0xC6,0xC8,0x1ED,0x1EE,0x1EF,0x1F0}:
            raise ValueError("cross-frame NMI stack residual differs")
        matched[f"{original}->{guest}"]=len(diffs)
    # Full original 128KiB delta triples, including before/after value, not
    # just count or checksum, MUST be identical at the displaced native frame.
    exact={}
    for r0,r1,n0,n1,expected in ((339,340,342,343,31),
                                  (340,341,343,344,642)):
        lhs=transitions(ref[r0],ref[r1])
        rhs=transitions(native[n0],native[n1])
        if len(lhs)!=expected or lhs!=rhs:
            raise ValueError("real 3-frame displaced transition byte triples unequal")
        exact[f"{r0}-{r1}_original__{n0}-{n1}_native"]=len(lhs)
    # Deliberately retain the subsequent 4-byte stack liveness disagreement:
    # evidence is not full event or CPU instruction parity.
    later_r=transitions(ref[341],ref[342])
    later_n=transitions(native[344],native[345])
    if (len(later_r),len(later_n),len(set(later_r)&set(later_n)))!=(220,219,216):
        raise ValueError("subsequent NMI stack return phase divergence changed")
    return {
        "schema":"rf056-original-native-USA-Bowl-three-frame-delta-triple-identity-v1",
        "source_run_sha":SOURCE_SHA,"exact_artifact_sha256":ZIP_SHA,
        "raw_original_native_WRAM_sample_count":len(FRAMES)*2,
        "raw_original_native_SRAM_sample_count":len(FRAMES)*2,
        "raw_historical_movie_WRAM_and_SRAM_offsets_count":len(MOVIE_FRAMES),
        "masked_WRAM_or_SRAM_bytes":0,
        "strict_same_frame_original_native_unmasked_difference_counts":
            {str(f):len(full_diff(ref[f],native[f])) for f in FRAMES},
        "cross_guest_existing_raw_128KiB_frame_pairs_difference_counts":matched,
        "two_displaced_complete_frame_byte_transition_sets_equal":exact,
        "next_pair_original_220_native_219_transition_overlap":216,
        "persistent_original_native_menu_counter_differences":
            {"7E:00C6":[1,0],"7E:00C8":[5,4]},
        "persistent_3_SRAM_record_differences":
            {"0EF6":[1,0],"0F31":[1,0],"0F33":[5,4]},
        "historical_movie_to_fresh_original_already_differs_44_WRAM_71_SRAM_at_334":True,
        "source_original_to_native_shared_absolute_CPU_clock_epoch_proven":False,
        "actual_first_trigger_instruction_and_controller_consumer_proven":False,
        "all_frame_cpu_apu_or_audio_fidelity_proven":False,
        "gameplay_behavior_or_input_rephased":False,
        "independently_accepted_complete_USA_events":0,
    }

def report(path:Path)->dict:
    if hashlib.sha256(path.read_bytes()).hexdigest()!=ZIP_SHA:
        raise ValueError("RF056 original immutable Bowl artifact SHA256 mismatch")
    with zipfile.ZipFile(path) as z:
        if len(z.namelist())!=78:
            raise ValueError("missing genuine source/fresh-original/native captures")
        producer=json.loads(z.read("bowl-report.json"))
        qa=json.loads(z.read("bowl-independent-raw-audit.json"))
        if (producer["rom_sha256"]!=ROM_SHA or
                producer["original_movie_sha256"]!=MOVIE_SHA or
                producer["source_sram_sha256"]!=SRAM_SHA or
                producer["course_id"]!="course:03" or
                qa["accepted_event_credit"]!=0):
            raise ValueError("actual original source or independent QA contract changed")
        def r(mode:str,kind:str,offset:int)->bytes:
            if mode=="movie":
                prefix="bowl/source/source-bowl-switcher-"
            else:
                prefix=f"bowl/replay/{mode}/bowl-next-switcher-"
            return z.read(f"{prefix}{offset}.{kind}.bin")
        return certify(
            {n:r("ref","wram",n) for n in FRAMES},
            {n:r("native","wram",n) for n in FRAMES},
            {n:r("ref","sram",n) for n in FRAMES},
            {n:r("native","sram",n) for n in FRAMES},
            {n:r("movie","wram",n) for n in MOVIE_FRAMES},
            {n:r("movie","sram",n) for n in MOVIE_FRAMES})

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    receipt=json.dumps(report(a.case),sort_keys=True,indent=2)+"\n"
    if a.out:a.out.write_text(receipt,encoding="utf8")
    else:print(receipt,end="")
if __name__=="__main__":main()
