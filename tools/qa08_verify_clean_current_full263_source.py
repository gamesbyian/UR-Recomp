#!/usr/bin/env python3
"""Verify immutable genuine compiled clean Win32 full-263 source archive.

This is an evidence replay of the source-only observer from held diagnostic
#1820, NOT an original renderer, trial brightness math or QA gate.
"""
import argparse, hashlib, io, json, zipfile
from pathlib import Path
ZIP_SHA = "6c01183698777683394794fc84ccde34667678548e51cf866e279b167d8dfff3"
JSON_SHA = "34e1b9e8b837d9dc327402508a7969024a33e932376cb057ab7bd49b07eca756"
INNER_SHA = "b74a839d67e1fe13cc6488969ad867046bfc57e64d96f047cd364f123c774347"
PE = "19db56a839b5f0291aedf8d2a5bad8f7d4ea450bb5fa926bdd609bdea4ef51d7"
CRC = "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
ORIGINAL = "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
CLEAN = "91e0bf8f5d7b86b188526740d825af890a99b02ecc05093f9a2143fa56ce49cd"
HEADER = (b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
          b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
def sha(data):
    return hashlib.sha256(data).hexdigest()
def verify(path:Path)->dict:
    raw=path.read_bytes()
    if sha(raw)!=ZIP_SHA: raise ValueError("real compiled PE ZIP source identity drift")
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        if set(outer.namelist()) != {"qa08-premath-full263-ab.json","qa08-premath-source-images.zip"}:
            raise ValueError("unexpected real source artifact inventory")
        control=outer.read("qa08-premath-full263-ab.json")
        source=outer.read("qa08-premath-source-images.zip")
    if sha(control)!=JSON_SHA or sha(source)!=INNER_SHA:
        raise ValueError("source frame manifest or source-image ZIP hash mismatch")
    r=json.loads(control)
    values={
        "actual_Windows_PE_sha256":PE,
        "original_2014_Snes9x_source_sha256":ORIGINAL,
        "current_unmodified_Windows_native_source_sha256":CLEAN,
        "native_actual_5484_guest_CRC_SHA256":CRC,
        "all_263_full_logical_256x224_source_frames":263,
        "all_pixels_source_bound":263*256*224,
        "baseline_wrong_RGB5":890205,
        "experimental_wrong_RGB5":890205,
        "baseline_exact_frames":132,
        "experimental_exact_frames":132,
        "corrected_real_pixels":0,"newly_wrong_real_pixels":0,
        "source_frames_better":0,"source_frames_worse":0,
        "clean_263_native_P7_all_bytes_equal_prior_RF017_source":True,
        "actual_2014_original_callback_f_minus_1_to_guest_f":True,
        "QA08_QA10_4K_art_release_accepted":False
    }
    for k,v in values.items():
        if r.get(k)!=v:raise ValueError("native source frame parity / acceptance invariant changed "+k)
    if len(r.get("per_frame",[]))!=263:
        raise ValueError("truncated original/native frame census")
    seen=set();unique=set()
    with zipfile.ZipFile(io.BytesIO(source)) as frames:
        expected={"qa08-premath-full263-ab.json"}|{
            f"source/ur-baldosa-original-source-{f:06}.pam" for f in range(1280,5473,16)}
        if set(frames.namelist())!=expected or frames.read("qa08-premath-full263-ab.json")!=control:
            raise ValueError("different or duplicated native source member inventory")
        for i,row in enumerate(r["per_frame"]):
            frame=1280+i*16
            name=f"source/ur-baldosa-original-source-{frame:06}.pam"
            img=frames.read(name)
            if (row["guest"]!=frame or row["original_callback"]!=frame-1 or
                not img.startswith(HEADER) or len(img)!=len(HEADER)+256*224*4 or
                sha(img)!=row["experimental_P7_sha256"] or
                row["experimental_wrong"]!=row["original_baseline_wrong"] or
                row["newly_wrong"]!=0 or row["corrected"]!=0):
                raise ValueError("real complete source image altered or wrong frame")
            seen.add(frame);unique.add(sha(img))
    if len(seen)!=263 or len(unique)!=243:
        raise ValueError("missing full source temporal image census")
    return {
      "schema":"QA08-genuine-current-clean-Win32-263-original-source-images/1",
      "current_compiled_original_PPU_Win32_PE_SHA256":PE,
      "actual_windows_source_artifact_id":12124754077,
      "source_outer_zip_sha256":ZIP_SHA,
      "source_manifest_sha256":JSON_SHA,
      "source_nested_images_zip_sha256":INNER_SHA,
      "independent_2014_original_Snes9x_source_zip_sha256":ORIGINAL,
      "separate_current_RF017_clean_P7_archive_sha256":CLEAN,
      "original_genuine_two_pad_guest_5484_CRC_sha256":CRC,
      "registered_original_callback_f_minus_1_to_native_f":True,
      "full_256x224_source_RGB5_pixel_positions":263*256*224,
      "all_263_native_P7_full_images_SHA256_verified":True,
      "unique_native_source_image_hashes":len(unique),
      "all_263_images_byte_equal_independent_clean_RF017_PPU":True,
      "old_clean_source_wrong_RGB5":890205,
      "current_clean_source_wrong_RGB5":890205,
      "pixel_regressions_vs_existing_clean_source":0,
      "pixel_improvements_vs_existing_clean_source":0,
      "source_exact_full_frames_against_2014_Snes9x":132,
      "unresolved_INIDISP_CGRAM_medal_phase_still_present":True,
      "original_vs_native_CPU_instruction_clock_proven":False,
      "premath_trial_renderer_installed":False,
      "real_4K_7to6_HD_artist_approval_or_release_accepted":False
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    r=verify(a.source)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("QA08_CLEAN_FULL263",r["all_263_images_byte_equal_independent_clean_RF017_PPU"],
          r["current_clean_source_wrong_RGB5"],"art_release=0")
if __name__=="__main__":main()
