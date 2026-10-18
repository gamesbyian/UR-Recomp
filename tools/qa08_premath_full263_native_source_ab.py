#!/usr/bin/env python3
"""Exactly source-registered clean current PE versus historical native baseline and Snes9x 2014."""
from __future__ import annotations
import argparse,hashlib,io,json,os,re,zipfile
from pathlib import Path
try:
    from tools.baldosa_windows_native_pause_route import run_route
except ImportError:
    from baldosa_windows_native_pause_route import run_route
ROM="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SCRIPT="ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194"
ORIG_OUTER="3475ee87b5b20768f9377d8d1c787927955c33ee6d4388dae008f5486a81370e"
ORIG_INNER="72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
BASE_OUTER="4cb67a3ea8e5952c1757b4db8dadcbc3005a79f2609a7068a074171b2f8b28ea"
BASE_INNER="91e0bf8f5d7b86b188526740d825af890a99b02ecc05093f9a2143fa56ce49cd"
GUEST="b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
FRAMES=tuple(range(1280,5473,16))
HEADER=(b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
        b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
PIXELS=256*224
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def load_archive(path:Path,outer:str,key:str,inner:str)->zipfile.ZipFile:
    raw=path.read_bytes()
    if sha(raw)!=outer:raise ValueError("outer immutable full-source ZIP identity changed")
    with zipfile.ZipFile(io.BytesIO(raw)) as z: data=z.read(key)
    if sha(data)!=inner:raise ValueError("nested full-source ZIP changed")
    return zipfile.ZipFile(io.BytesIO(data))
def load_current_native_source(path:Path)->zipfile.ZipFile:
    """Artifact 12090308473 is the already-raw source ZIP, not a wrapper.

    Archive-only research bundle wrapped it as native-source.zip; never
    conflate two different ZIP-layer digests or silently unwrap arbitrary
    submitted data. The current real GitHub artifact digest is BASE_INNER.
    """
    raw=path.read_bytes()
    if sha(raw)!=BASE_INNER:
        raise ValueError("actual source GitHub artifact 12090308473 SHA changed")
    return zipfile.ZipFile(io.BytesIO(raw))

def pixels(raw:bytes)->bytes:
    if len(raw)!=len(HEADER)+PIXELS*4 or not raw.startswith(HEADER):
        raise ValueError("missing real uncropped 256x224 RGBA source")
    return raw[len(HEADER):]
def census(original:bytes,old:bytes,new:bytes)->dict:
    if len(original)!=PIXELS*4:raise ValueError("cropped original callback")
    old=pixels(old);new=pixels(new)
    bad_old=bad_new=fixed=regressed=0
    for j in range(0,PIXELS*4,4):
        ref=(original[j+2]>>3,original[j+1]>>3,original[j]>>3)
        a=(old[j]>>3,old[j+1]>>3,old[j+2]>>3)
        b=(new[j]>>3,new[j+1]>>3,new[j+2]>>3)
        wa=a!=ref;wb=b!=ref
        bad_old+=wa;bad_new+=wb
        fixed+=wa and not wb
        regressed+=wb and not wa
    return {"original_baseline_wrong":bad_old,"experimental_wrong":bad_new,
            "corrected":fixed,"newly_wrong":regressed}
def compare(orig:zipfile.ZipFile,base:zipfile.ZipFile,folder:Path,
            crcs:list[str])->dict:
    if len(crcs)!=5484 or any(re.fullmatch(r"0x[0-9a-fA-F]{8}",v) is None for v in crcs):
        raise ValueError("real native full 5484 guest CRC absent")
    digest=sha(("\n".join(v.lower() for v in crcs)+"\n").encode())
    if digest!=GUEST:raise ValueError("RF017 native CPU/guest input source changed")
    expected={f"ur-baldosa-original-source-{f:06}.pam" for f in FRAMES}
    if {x.name for x in folder.iterdir() if x.is_file()}!=expected:
        raise ValueError("actual original PPU source callback inventory changed")
    rows=[]
    for f in FRAMES:
        raw=orig.read(f"frames/frame_{f-1:06}_256x224.raw")
        baseline=base.read(f"source/ur-baldosa-original-source-{f:06}.pam")
        image=(folder/f"ur-baldosa-original-source-{f:06}.pam").read_bytes()
        # QA08 clean extraction: every byte of the new real PPU P7 image
        # must equal the independently source-pinned prior clean RF017 P7.
        # No selected-coordinate masks, drift search or brightness changes.
        if baseline != image:
            raise ValueError("clean current PE changed true 263-frame PPU source baseline")
        rows.append({"guest":f,"original_callback":f-1,
                     "experimental_P7_sha256":sha(image),
                     **census(raw,baseline,image)})
    old_total=sum(row["original_baseline_wrong"] for row in rows)
    if old_total!=890205:raise ValueError("real RF017 full-original baseline pixel census drift")
    return {
      "schema":"qa08-real-RF017-two-player-full263-premath-AB/1",
      "original_2014_Snes9x_source_sha256":ORIG_INNER,
      "current_unmodified_Windows_native_source_sha256":BASE_INNER,
      "native_actual_5484_guest_CRC_SHA256":digest,
      "actual_2014_original_callback_f_minus_1_to_guest_f":True,
      "all_263_full_logical_256x224_source_frames":len(rows),
      "all_pixels_source_bound":len(rows)*PIXELS,
      "baseline_wrong_RGB5":old_total,
      "experimental_wrong_RGB5":sum(row["experimental_wrong"] for row in rows),
      "corrected_real_pixels":sum(row["corrected"] for row in rows),
      "newly_wrong_real_pixels":sum(row["newly_wrong"] for row in rows),
      "baseline_exact_frames":sum(row["original_baseline_wrong"]==0 for row in rows),
      "experimental_exact_frames":sum(row["experimental_wrong"]==0 for row in rows),
      "clean_263_native_P7_all_bytes_equal_prior_RF017_source":True,
      "source_frames_better":sum(row["experimental_wrong"]<row["original_baseline_wrong"] for row in rows),
      "source_frames_worse":sum(row["experimental_wrong"]>row["original_baseline_wrong"] for row in rows),
      "per_frame":rows,
      "actual_hardware_SNESC_DAC_or_source_CPU_equivalence_proven":False,
      "QA08_QA10_4K_art_release_accepted":False
    }
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for x in ("exe","rom","script","original-outer","current-outer","out"):
        p.add_argument("--"+x,type=Path,required=True)
    p.add_argument("--timeout",type=int,default=720)
    a=p.parse_args()
    if sha(a.rom.read_bytes())!=ROM or sha(a.script.read_bytes())!=SCRIPT:
        p.error("retail USA ROM/controller bytes changed")
    if a.out.exists():p.error("refuse overwrite of original source campaign")
    a.out.mkdir(parents=True)
    original=load_archive(a.original_outer,ORIG_OUTER,"original.zip",ORIG_INNER)
    current=load_current_native_source(a.current_outer)
    folder=a.out/"source";folder.mkdir()
    env={"UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR":str(folder.resolve()),
         "UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE":"twoplayer-fullroute"}
    previous={k:os.environ.get(k) for k in env}
    os.environ.update(env)
    try: crc,log=run_route(a.exe.resolve(),a.rom.resolve(),a.script.resolve(),
                          a.out,pause=False,video="windows",timeout=a.timeout)
    finally:
        for k,v in previous.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
    report=compare(original,current,folder,crc)
    report["actual_Windows_PE_sha256"]=sha(a.exe.read_bytes())
    report_path=a.out/"qa08-premath-full263-ab.json"
    report_path.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    with zipfile.ZipFile(a.out/"qa08-premath-source-images.zip","w",
                         zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(report_path,arcname=report_path.name)
        for f in FRAMES:
            name=f"ur-baldosa-original-source-{f:06}.pam"
            z.write(folder/name,arcname="source/"+name)
    print("QA08_PREMATH_FULL263",report["baseline_wrong_RGB5"],
          report["experimental_wrong_RGB5"],"newly_wrong",
          report["newly_wrong_real_pixels"],"release=0")
if __name__=="__main__":main()
