#!/usr/bin/env python3
"""Real current clean RF017 vs premath Win32 original 1P guest CRC equality."""
from __future__ import annotations
import argparse,hashlib,io,json,re,zipfile
from pathlib import Path
try:
    from tools.baldosa_windows_native_pause_route import run_route
except ImportError:
    from baldosa_windows_native_pause_route import run_route
ROM="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SCRIPT="65567dd5629bc71d544d58a4ac31b51de6c0b382d070aaf06ec1a2be952a5cd1"
OUTER="a4e3365c8fd4c80a33479bef3c8f4cc97598ef3edbd7ab7f2bde8563bdc51c98"
INNER="03d250901a78192a0a7ac0d788c471986a7e3abacb370943e6e8542d97eac52f"
CLEAN_PE="157180a26a78dd34f96ff3ad353a9676a7e5811dbd1ed537bb15ddfdbfadb93b"
OLD_GUEST="45d7675858ebf3e3a051a58d2af104b6d2d9a66e7700da8248ad571713662c41"
FOLDER="UR-Recomp-Baldosa-Windows-x64/"
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def extract(path:Path,out:Path)->Path:
    raw=path.read_bytes()
    if sha(raw)!=OUTER:raise ValueError("unqualified clean original RF017 outer ZIP SHA")
    with zipfile.ZipFile(io.BytesIO(raw)) as z: nested=z.read("UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip")
    if sha(nested)!=INNER:raise ValueError("unqualified clean RF017 nested package")
    with zipfile.ZipFile(io.BytesIO(nested)) as z:
        pe=z.read(FOLDER+"UniracersSNESRecomp.exe")
        meta=json.loads(z.read(FOLDER+"BALDOSA-CANDIDATE-MANIFEST.json"))
    files={x["path"]:x["sha256"] for x in meta["immutable_files"]}
    if sha(pe)!=CLEAN_PE or files["UniracersSNESRecomp.exe"]!=CLEAN_PE:
        raise ValueError("unqualified clean original Win32 real PE identity")
    out.mkdir(parents=True,exist_ok=True)
    exe=out/"UniracersSNESRecomp.exe";exe.write_bytes(pe)
    return exe
def full_crc(lines:list[str])->str:
    if len(lines)!=5447 or any(re.fullmatch("0x[0-9a-fA-F]{8}",x) is None for x in lines):
        raise ValueError("real 5447 1P full native guest CRC not recorded")
    return sha(("\n".join(x.lower() for x in lines)+"\n").encode())
def compare(report:dict,clean:str)->dict:
    if report["schema"]!="qa08-current-premath-authenticated-Windows-vs-2014-oneplayer-65/1":
        raise ValueError("different experiment source receipt")
    candidate=report["native_USA_guest_CRC_sha256"]
    if re.fullmatch("[0-9a-f]{64}",candidate) is None:raise ValueError("no experiment guest CRC SHA")
    return {
      "schema":"qa08-real-current-clean-vs-premath-oneplayer-5447-guestCRC/1",
      "actual_clean_RF017_PE_sha256":CLEAN_PE,
      "actual_clean_RF017_package_sha256":INNER,
      "actual_candidate_premath_PE_sha256":report["actual_Win32_PE_sha256"],
      "exact_USA_source_input_rom_sha256":ROM,
      "exact_same_native_1P_input_script_sha256":SCRIPT,
      "actual_full_guest_count_per_run":5447,
      "current_clean_original_Windows_guest_crc_sha256":clean,
      "experimental_premath_original_Windows_guest_crc_sha256":candidate,
      "two_independent_Windows_pe_current_guest_CRC_equal":candidate==clean,
      "old_preRF017_guest_crc_sha256":OLD_GUEST,
      "2014_Snes9x_guest_CPU_equivalence_proven":False,
      "full_1P_original_course_event_or_release_accepted":False
    }
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for flag in ("rom","script","clean-artifact","trial-report","out"):
        ap.add_argument("--"+flag,required=True,type=Path)
    ap.add_argument("--timeout",type=int,default=720)
    a=ap.parse_args()
    if sha(a.rom.read_bytes())!=ROM or sha(a.script.read_bytes())!=SCRIPT:
        ap.error("incorrect real USA 1P source ROM/script")
    if a.out.exists():ap.error("cannot overwrite independent Windows guest A/B")
    a.out.mkdir(parents=True)
    exe=extract(a.clean_artifact,a.out/"exe")
    x=a.out/"clean-guest";x.mkdir()
    values,log=run_route(exe,a.rom.resolve(),a.script.resolve(),x,
                         pause=False,video="windows",timeout=a.timeout)
    current=full_crc(values)
    report=compare(json.loads(a.trial_report.read_text()),current)
    (a.out/"qa08-1p-clean-vs-premath-crc.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    if not report["two_independent_Windows_pe_current_guest_CRC_equal"]:
        raise ValueError("current clean and experiment RF017 1P guest CRCs differ")
    print("QA08_REAL_CURRENT_1P_GUEST_CRC_EQUAL",current,"release=0")
if __name__=="__main__":main()
