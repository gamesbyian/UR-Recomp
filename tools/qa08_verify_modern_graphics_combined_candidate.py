#!/usr/bin/env python3
"""Strict offline replay of genuine compiled combined Modern+QA08 graphics PE.

Consume TWO previously archived source-pinned GitHub Actions ZIP artifacts.
No ROM, profile data, GitHub connection, emulator, rendering or product edits.
Explicitly does not award player-operated physical QA or original RGB5 parity.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile

BINDING_OUTER = "e3eb5b38118a236deb1fd33c90300e2d945b911d511f821b82d66f22a25c1384"
PACKAGE_OUTER = "5e30ecef730d90b14390edba0cb0ff3b17b7d0ea34fadbbe52978dd00268f98f"
BINDING_INNER = "6550c7f73e15bebd0c23dc8135c08f144130ff86da0ffb38e39abf55869cf01a"
PACKAGE_INNER = "fdd53e041772459e2df3b78275a959d81ca379c1cec48ffc41fa5c2991a122eb"
SOURCE = "5c5c992ecdc156f638c13a0d6d6c20a3331c52d6"
PE_SHA = "1786c474399b245305ba6ab22ff816653ad762ea36d4ac6a4667ec6a74e7ef53"
LAUNCHER = "b61d6b3836e21da6dd91dc4bcbf5cff19a85df6f73f07ee2bcd29a377fc678c3"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
BASE = "UR-Recomp-Baldosa-Windows-x64/"
PACKAGE = "UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip"
ALLOWED = {"BALDOSA-CANDIDATE-MANIFEST.json","README-BALDOSA-CANDIDATE.txt",
           "UniracersSNESRecomp.exe","run-baldosa-modern.cmd"}

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def exact_zip(blob:bytes,expected:set[str])->dict[str,bytes]:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if set(z.namelist()) != expected or len(z.namelist()) != len(expected):
            raise ValueError("artifact members differ or are duplicated")
        if any(x.is_dir() or x.file_size<=0 for x in z.infolist()):
            raise ValueError("truncated or unexpected archive member")
        return {name:z.read(name) for name in expected}

def verify(binding_archive:Path,package_archive:Path)->dict:
    a=binding_archive.read_bytes()
    b=package_archive.read_bytes()
    if digest(a)!=BINDING_OUTER or digest(b)!=PACKAGE_OUTER:
        raise ValueError("authenticated GitHub artifact ZIP SHA mismatch")
    binding_files=exact_zip(a,{"candidate-binding.json"})
    payload=binding_files["candidate-binding.json"]
    if digest(payload)!=BINDING_INNER:
        raise ValueError("exact combined source binding changed")
    identity=json.loads(payload)
    outer=exact_zip(b,{PACKAGE,PACKAGE+".sha256"})
    bundle=outer[PACKAGE]
    if digest(bundle)!=PACKAGE_INNER or digest(bundle)!=identity.get("zip_sha256"):
        raise ValueError("packaged executable source ZIP identity changed")
    if outer[PACKAGE+".sha256"]!=(
        PACKAGE_INNER+" *"+PACKAGE+"\n").encode("ascii"):
        raise ValueError("portable package sidecar hash differs")
    members=exact_zip(bundle,{BASE+name for name in ALLOWED})
    manifest=json.loads(members[BASE+"BALDOSA-CANDIDATE-MANIFEST.json"])
    exe=members[BASE+"UniracersSNESRecomp.exe"]
    if len(exe)<0x100 or exe[:2]!=b"MZ":
        raise ValueError("not a real Windows portable executable")
    offset=struct.unpack_from("<I",exe,0x3c)[0]
    if offset<=0 or offset+26>len(exe) or exe[offset:offset+4]!=b"PE\x00\x00":
        raise ValueError("not a complete real Windows native PE image")
    machine,sections,timestamp=struct.unpack_from("<HHI",exe,offset+4)
    if machine!=0x8664 or sections<1 or struct.unpack_from("<H",exe,offset+24)[0]!=0x20b:
        raise ValueError("not a compiled Windows PE32+ AMD64 executable")
    if (identity.get("source_revision")!=SOURCE or
        identity.get("executable_bytes")!=len(exe) or
        identity.get("zip_bytes")!=len(bundle) or
        identity.get("journey_and_packaged_executable_sha256")!=PE_SHA or
        digest(exe)!=PE_SHA or
        identity.get("claims")!="hash identity only; not physical-pad, release-gate or independent acceptance"):
        raise ValueError("actual Windows PE source binding is different")
    claims=identity.get("manifest_immutable_files")
    if not isinstance(claims,dict) or set(claims)!={"README-BALDOSA-CANDIDATE.txt","UniracersSNESRecomp.exe","run-baldosa-modern.cmd"}:
        raise ValueError("original native package manifest population changed")
    if any(digest(members[BASE+key])!=value for key,value in claims.items()) or (
        claims["run-baldosa-modern.cmd"]!=LAUNCHER):
        raise ValueError("launcher or immutable product bytes drift")
    if (manifest.get("project_revision")!=SOURCE or
        manifest.get("rom_sha256_required")!=ROM_SHA or
        manifest.get("rom_bundled") is not False or
        manifest.get("profile_data_bundled") is not False or
        manifest.get("status")!="native-modern-root-stock-1p-2p-candidate-only"):
        raise ValueError("embedded manifest altered or a ROM/save was bundled")
    rows=manifest.get("immutable_files",[])
    if not isinstance(rows,list) or len(rows)!=3 or {
        row["path"]:row["sha256"] for row in rows if isinstance(row,dict)}!=claims:
        raise ValueError("embedded manifest does not match original native files")
    if any(row["bytes"]!=len(members[BASE+row["path"]]) for row in rows):
        raise ValueError("embedded manifest byte sizes mismatch")
    if timestamp<=0:
        raise ValueError("compiled source timestamp absent")
    return {
        "schema":"QA08-exact-combined-clean-HDMA-V0-and-Modern-SRAM-Windows-candidate/1",
        "actual_compiled_Windows_PE_SHA256":PE_SHA,
        "actual_windows_PE32_plus_amd64":True,
        "source_merge_sha":SOURCE,
        "binding_outer_zip_sha256":BINDING_OUTER,
        "binding_json_sha256":BINDING_INNER,
        "package_outer_zip_sha256":PACKAGE_OUTER,
        "portable_inner_zip_sha256":PACKAGE_INNER,
        "package_launcher_sha256":LAUNCHER,
        "required_authentic_USA_ROM_SHA256":ROM_SHA,
        "portable_zip_bytes":len(bundle),
        "windows_PE_bytes":len(exe),
        "observed_PE_COFF_timestamp":timestamp,
        "package_rom_free":True,
        "package_profile_data_free":True,
        "release_QA_accepted":False,
        "original_2014_RGB5_result_parity_proven":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binding-archive",type=Path,required=True)
    p.add_argument("--package-archive",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=verify(a.binding_archive,a.package_archive)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA08_MODERN_GRAPHICS_ACTUAL_PE",result["actual_compiled_Windows_PE_SHA256"],
          "no_release_credit=1")

if __name__=="__main__":main()
