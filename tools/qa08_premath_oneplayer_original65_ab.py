#!/usr/bin/env python3
"""Compare real 2014 1P 65 consecutive BGRX callbacks to native P7 f+1."""
from __future__ import annotations
import argparse,hashlib,json,os,re,zipfile
from pathlib import Path
try:
    from tools.baldosa_windows_native_pause_route import run_route
    from tools.qa08_premath_full263_native_source_ab import census,PIXELS,sha
except ImportError:
    from baldosa_windows_native_pause_route import run_route
    from qa08_premath_full263_native_source_ab import census,PIXELS,sha

ARCHIVE="9b6f32bd00b89e5fda72bb82ea9d535ebd90baf62a4600a2fb0fd598b4ee648d"
MANIFEST="4c2cb772d8102de6f0c8d04bf076313329ce1b99b26eb60261a9bf8c40e29fd7"
SCRIPT="74527132f85e136985edfe5de9b84172a4d1a3ecd8814af7c6e481fd0603d56b"
ROM="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
FIRST,LAST=2176,2240
LOG=re.compile(r"^UR_QA08_WINDOWS_ORIGINAL_SOURCE frame=(\d+) logical=256x224 saved=(\d) source=post-original-ppu-before-present$",re.M)
def reference(path:Path):
    if sha(path.read_bytes())!=ARCHIVE:
        raise ValueError("2014 authentic 1P original artifact SHA changed")
    z=zipfile.ZipFile(path)
    raw=z.read("qa08-original-1p-source.json")
    if sha(raw)!=MANIFEST:raise ValueError("original 1P manifest SHA changed")
    md=json.loads(raw)
    script=z.read("qa08-original-1p.script")
    if sha(script)!=SCRIPT or md["unchanged_original_route_no_turbo_SHA256"]!=SCRIPT:
        raise ValueError("actual no-turbo original input script changed")
    if (md["original_USA_ROM_sha256"]!=ROM or md["callback_count"]!=65 or
        md["actual_original_callback_range"]!=[FIRST,LAST]):
        raise ValueError("authentic Snes9x 1P source identity changed")
    wanted={f"frames/frame_{f:06}_256x224.raw" for f in range(FIRST,LAST+1)}
    if set(z.namelist())!=wanted|{"qa08-original-1p-source.json","qa08-original-1p.script","original.log"}:
        raise ValueError("original 1P source inventory altered")
    for f,m in zip(range(FIRST,LAST+1),md["actual_source_frames"]):
        image=z.read(f"frames/frame_{f:06}_256x224.raw")
        if (len(image)!=PIXELS*4 or m["original_callback_frame_zero_based"]!=f or
            m["original_retro_run_one_based"]!=f+1 or
            sha(image)!=m["unmodified_BGRX8888_sha256"]):
            raise ValueError("original source frame SHA or geometry changed")
    return script,z

def compare(z,folder:Path,log:str,crcs:list[str]):
    if len(crcs)!=5447 or any(not re.fullmatch(r"0x[0-9a-fA-F]{8}",x) for x in crcs):
        raise ValueError("real 5447 native 1P guest CRC transcript missing")
    captured=LOG.findall(log)
    selected=set(range(FIRST+1,LAST+2))
    if len(captured)!=65 or {(int(frame)) for frame,ok in captured if ok=="1"}!=selected:
        raise ValueError("real 65 consecutive native callbacks missing or duplicated")
    if "UR_QA08_WINDOWS_SOURCE_REJECT" in log:
        raise ValueError("native 1P source capture was rejected")
    names={f"ur-baldosa-original-source-{f:06}.pam" for f in selected}
    if not folder.is_dir() or {p.name for p in folder.iterdir()}!=names:
        raise ValueError("native 1P consecutive PPU images missing/extra")
    frames=[]
    for f in range(FIRST,LAST+1):
        original=z.read(f"frames/frame_{f:06}_256x224.raw")
        native=(folder/f"ur-baldosa-original-source-{f+1:06}.pam").read_bytes()
        comparison=census(original,native,native)
        if comparison["original_baseline_wrong"]!=comparison["experimental_wrong"]:
            raise ValueError("native self-control against source inconsistent")
        frames.append({"original_callback":f,"native_guest":f+1,
                       "original_BGRX_SHA256":sha(original),"native_P7_SHA256":sha(native),
                       "wrong_RGB5":comparison["experimental_wrong"]})
    return {"schema":"qa08-current-RF017-original-1P-65-consecutive-source/1",
      "authentic_2014_original_source_zip_SHA256":ARCHIVE,
      "original_unmodified_no_turbo_route_SHA256":SCRIPT,
      "native_guest_CRC_sha256":sha(("\n".join(x.lower() for x in crcs)+"\n").encode()),
      "native_1P_guest_frames_simulated":len(crcs),
      "registered_callback_rule":"original_f => native_guest_f+1 (no search)",
      "all_65_source_frames":65,"all_uncropped_RGB5_pixel_positions":65*PIXELS,
      "wrong_original_native_RGB5":sum(x["wrong_RGB5"] for x in frames),
      "exact_full_frames":sum(x["wrong_RGB5"]==0 for x in frames),
      "per_frame":frames,"native_unmodified_1P_baseline_65_frames_available":False,
      "CPU_instruction_or_event_clock_parity_proven":False,
      "hardware_HD_art_QA08_QA10_release_approved":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for s in ("exe","rom","original-archive","out"):
        p.add_argument("--"+s,type=Path,required=True)
    p.add_argument("--timeout",type=int,default=720)
    a=p.parse_args()
    if sha(a.rom.read_bytes())!=ROM:p.error("real USA ROM source fingerprint changed")
    if a.out.exists():p.error("refuse to overwrite source campaign")
    script,z=reference(a.original_archive)
    a.out.mkdir(parents=True)
    script_path=a.out/"qa08-authentic-2014-original-1p.script"
    script_path.write_bytes(script)
    folder=a.out/"source";folder.mkdir()
    env={"UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE":"oneplayer-original65",
         "UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR":str(folder.resolve())}
    prior={k:os.environ.get(k) for k in env}
    os.environ.update(env)
    try:crcs,log=run_route(a.exe.resolve(),a.rom.resolve(),script_path.resolve(),
                           a.out,pause=False,video="windows",timeout=a.timeout)
    finally:
        for k,v in prior.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
    result=compare(z,folder,log,crcs)
    result["Win32_trial_PE_SHA256"]=sha(a.exe.read_bytes())
    outfile=a.out/"qa08-real-1p-65-source.json"
    outfile.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    with zipfile.ZipFile(a.out/"qa08-real-1p-65-images.zip","w",
                         zipfile.ZIP_DEFLATED,compresslevel=6) as bundle:
        bundle.write(outfile,arcname=outfile.name)
        for frame in range(FIRST+1,LAST+2):
            name=f"ur-baldosa-original-source-{frame:06}.pam"
            bundle.write(folder/name,arcname="source/"+name)
    print("QA08_REAL_1P_65",result["wrong_original_native_RGB5"],
          "wrong RGB5",result["exact_full_frames"],"exact frames release=0")
if __name__=="__main__":main()
