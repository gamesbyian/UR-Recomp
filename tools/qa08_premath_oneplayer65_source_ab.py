#!/usr/bin/env python3
"""Genuine RF017 Windows pre-math 65 consecutive moving 1P vs Snes9x 2014."""
from __future__ import annotations
import argparse,hashlib,json,os,re,zipfile
from pathlib import Path
try:
    from tools.baldosa_windows_native_pause_route import run_route
except ImportError:
    from baldosa_windows_native_pause_route import run_route
ROM="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SCRIPT="65567dd5629bc71d544d58a4ac31b51de6c0b382d070aaf06ec1a2be952a5cd1"
ORIG_ZIP="9b6f32bd00b89e5fda72bb82ea9d535ebd90baf62a4600a2fb0fd598b4ee648d"
NATIVE_GUEST_CRC="45d7675858ebf3e3a051a58d2af104b6d2d9a66e7700da8248ad571713662c41"
FRAMES=tuple(range(2177,2242))
HEADER=b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
PIXELS=256*224
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def census(original:bytes,trial:bytes)->int:
    if len(original)!=PIXELS*4 or len(trial)!=len(HEADER)+PIXELS*4 or not trial.startswith(HEADER):
        raise ValueError("actual complete 256x224 2014/native original source absent")
    trial=trial[len(HEADER):]
    wrong=0
    for i in range(0,len(original),4):
        ref=(original[i+2]>>3,original[i+1]>>3,original[i]>>3)
        got=(trial[i]>>3,trial[i+1]>>3,trial[i+2]>>3)
        wrong+=ref!=got
    return wrong
def compare(folder:Path,originalzip:zipfile.ZipFile,crcs:list[str])->dict:
    if len(crcs)!=5447 or any(re.fullmatch(r"0x[0-9a-fA-F]{8}",x) is None for x in crcs):
        raise ValueError("exact 5447 native guest frames not completed")
    digest=sha(("\n".join(x.lower() for x in crcs)+"\n").encode())
    # Source provenance must be retained, never waived. This old native CRC
    # was measured before RF017. It is NOT an equivalence claim for the
    # current RF017 guest; a mismatch leaves the 65 raster pixel counts
    # observational only, pending a separately measured clean RF017 route.
    same_old_guest = digest==NATIVE_GUEST_CRC
    expected={f"ur-baldosa-original-source-{f:06}.pam" for f in FRAMES}
    actual={x.name for x in folder.iterdir() if x.is_file()}
    if actual!=expected:
        raise ValueError("actual 65 consecutive 1P native original PPU callbacks absent or extra")
    source_info=json.loads(originalzip.read("qa08-original-1p-source.json"))
    hist={x["original_callback_frame_zero_based"]:x["unmodified_BGRX8888_sha256"]
          for x in source_info["actual_source_frames"]}
    if sorted(hist)!=list(range(2176,2241)):
        raise ValueError("original 2014 Snes9x source callback manifest changed")
    frames=[]
    for f in FRAMES:
        s=originalzip.read(f"frames/frame_{f-1:06}_256x224.raw")
        if sha(s)!=hist[f-1]:
            raise ValueError("2014 Snes9x original callback source hashes changed")
        b=(folder/f"ur-baldosa-original-source-{f:06}.pam").read_bytes()
        frames.append({"original_callback":f-1,"native_guest":f,
                       "original_sha256":sha(s),"native_P7_sha256":sha(b),
                       "wrong_RGB5":census(s,b)})
    return {
      "schema":"qa08-current-premath-authenticated-Windows-vs-2014-oneplayer-65/1",
      "source_2014_Snes9x_artifact_sha256":ORIG_ZIP,
      "native_USA_guest_CRC_sha256":digest,
      "archived_pre_RF017_1P_guest_CRC_sha256":NATIVE_GUEST_CRC,
      "current_matches_archived_pre_RF017_guest_CRC":same_old_guest,
      "current_RF017_clean_same_route_guest_CRC_comparison_completed":False,
      "image_comparison_source_frame_parity_qualified":False,
      "native_script_sha256":SCRIPT,
      "original_fminus1_vs_native_guest_f":True,
      "actual_65_contiguous_full_256x224_frames":len(frames),
      "source_pixels_evaluated":len(frames)*PIXELS,
      "full_original_native_pixel_exact_frames":sum(x["wrong_RGB5"]==0 for x in frames),
      "wrong_pixels":sum(x["wrong_RGB5"] for x in frames),
      "per_frame":frames,
      "current_unpatched_same_PE_1P_65_frame_baseline_captured":False,
      "CPU_APU_NMI_instruction_equivalence_proven":False,
      "hardware_SNES_physical_4K_HD_art_release_accepted":False
    }
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ("exe","rom","script","original-artifact","out"):
        p.add_argument("--"+flag,type=Path,required=True)
    p.add_argument("--timeout",type=int,default=720)
    a=p.parse_args()
    if sha(a.rom.read_bytes())!=ROM or sha(a.script.read_bytes())!=SCRIPT:
        p.error("actual original USA ROM or authenticated 1P controller route changed")
    raw=a.original_artifact.read_bytes()
    if sha(raw)!=ORIG_ZIP:p.error("2014 true Snes9x ZIP source changed")
    if a.out.exists():p.error("refuse overwrite of real source 1P campaign")
    a.out.mkdir(parents=True)
    folder=a.out/"source";folder.mkdir()
    env={"UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR":str(folder.resolve()),
         "UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE":"oneplayer-exact65"}
    was={k:os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        crc,log=run_route(a.exe.resolve(),a.rom.resolve(),a.script.resolve(),
                          a.out,pause=False,video="windows",timeout=a.timeout)
    finally:
        for k,v in was.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
    if "UR_QA08_WINDOWS_SOURCE_REJECT" in log:
        raise ValueError("source producer rejected a frame or duplicated callback")
    with zipfile.ZipFile(a.original_artifact) as original:
        report=compare(folder,original,crc)
    report["actual_Win32_PE_sha256"]=sha(a.exe.read_bytes())
    report_path=a.out/"qa08-premath-oneplayer65.json"
    report_path.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    with zipfile.ZipFile(a.out/"qa08-premath-oneplayer65-images.zip","w",
                         zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        out.write(report_path,arcname=report_path.name)
        for f in FRAMES:
            v=f"ur-baldosa-original-source-{f:06}.pam"
            out.write(folder/v,arcname="source/"+v)
    print("QA08_REAL_1P_SOURCE",report["actual_65_contiguous_full_256x224_frames"],
          "exact",report["full_original_native_pixel_exact_frames"],
          "wrong",report["wrong_pixels"],
          "old_guest_match="+str(int(report["current_matches_archived_pre_RF017_guest_CRC"])),
          "source_parity_qualified=0 release=0")
if __name__=="__main__":main()
