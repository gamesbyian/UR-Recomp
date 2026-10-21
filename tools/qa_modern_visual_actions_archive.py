#!/usr/bin/env python3
"""Independently qualify retained Windows SDL3 P7/PNG evidence ZIP artifacts.

A valid PNG and receipt cannot substitute for the exact successful process
log or original P7, especially when Options changes display mode and the
first probe fails before the second fresh process produces the PNG.

Transport evidence only; never grants source, artistic, hardware or release QA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import PurePosixPath, Path
import re
import struct
import zipfile
import zlib

MAX_IMAGE = 3840 * 2160 * 4
MAX_LOG = 2 * 1024 * 1024
P7 = re.compile(rb"\AP7\nWIDTH ([1-9][0-9]*)\nHEIGHT ([1-9][0-9]*)\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")
PNG_SIG = b"\x89PNG\r\n\x1a\n"
HEX = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_HEX = re.compile(r"[0-9a-f]{40}\Z")
# Native host stage values are emitted by the real source painter and ordered
# before the SDL EndDraw readback. An unrelated screenshot with correct
# geometry/P7/log transport must NOT satisfy a route-specific visual case.
ROUTE_STAGES = {
    "root-quit": "root",
    "records-keyboard": "records-1p",
    "options-p1": "options",
    "options-open-p1": "options",
    "profile-first-p1": "profile-first-saved",
    "practice-picker-p1": "practice-picker",
    "multiplayer-unbound": "multiplayer-unrecorded-warning",
}



class AuditError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(z: zipfile.ZipFile, name: str, limit: int) -> bytes:
    if name not in z.namelist():
        raise AuditError("missing retained member: " + name)
    info = z.getinfo(name)
    if info.is_dir() or not 0 < info.file_size <= limit:
        raise AuditError("unsafe retained member size: " + name)
    return z.read(info)


def png_rgba(png: bytes, expected: tuple[int, int]) -> bytes:
    if not png.startswith(PNG_SIG):
        raise AuditError("not a PNG")
    pos = len(PNG_SIG)
    compressed = bytearray()
    dims = None
    seen_end = False
    while pos < len(png):
        if len(png) - pos < 12:
            raise AuditError("truncated PNG chunk")
        n = struct.unpack_from(">I", png, pos)[0]
        tag = png[pos + 4:pos + 8]
        if n > MAX_IMAGE or pos + 12 + n > len(png):
            raise AuditError("oversized PNG chunk")
        payload = png[pos + 8:pos + 8 + n]
        if zlib.crc32(tag + payload) & 0xffffffff != struct.unpack_from(">I", png, pos+8+n)[0]:
            raise AuditError("invalid PNG chunk CRC")
        if tag == b"IHDR":
            if dims is not None or n != 13:
                raise AuditError("ambiguous PNG header")
            w, h, depth, color, comp, filt, inter = struct.unpack(">IIBBBBB", payload)
            if (w, h) != expected or (depth, color, comp, filt, inter) != (8, 6, 0, 0, 0):
                raise AuditError("PNG output geometry/pixel type changed")
            dims = (w, h)
        elif tag == b"IDAT":
            compressed.extend(payload)
        elif tag == b"IEND":
            if n or pos+12+n != len(png):
                raise AuditError("bad PNG trailer")
            seen_end = True
        pos += 12+n
    if not seen_end or dims is None:
        raise AuditError("incomplete PNG")
    w,h = expected
    expected_size = (w*4+1)*h
    try:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(bytes(compressed), expected_size+1)
    except zlib.error as exc:
        raise AuditError("undecodable PNG") from exc
    if len(raw) != expected_size or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise AuditError("partial or oversized PNG decoded raster")
    stride = w*4
    if any(raw[y*(stride+1)] != 0 for y in range(h)):
        raise AuditError("expected exact filter-zero PNG rows")
    return b"".join(raw[y*(stride+1)+1:(y+1)*(stride+1)] for y in range(h))


def check_one(z: zipfile.ZipFile, folder: str) -> dict:
    receipt = json.loads(read(z, folder+"/readback-receipt.json", 64*1024))
    if (not isinstance(receipt,dict) or
            receipt.get("visual_approved") is not False or
            receipt.get("hardware_approved") is not False or
            receipt.get("release_gate_credit") != 0):
        raise AuditError("receipt overclaims native visual approval: "+folder)
    w,h = receipt["actual_sdl_renderer_output"]
    if not (isinstance(w,int) and isinstance(h,int) and
            320 <= w <= 3840 and 224 <= h <= 2160):
        raise AuditError("unsafe output geometry")
    expected = (w,h)
    png = read(z,folder+"/actual-sdl-drawable.png",MAX_IMAGE)
    if digest(png) != receipt.get("png_sha256"):
        raise AuditError("PNG SHA differs from native receipt: "+folder)
    rgba = png_rgba(png,expected)
    raw_p7 = [n for n in z.namelist()
              if n.startswith(folder+"/") and n.endswith("/actual-sdl-drawable.pam")]
    expected_p7 = receipt.get("p7_sha256")
    if not isinstance(expected_p7,str) or not HEX.fullmatch(expected_p7):
        raise AuditError("missing valid original P7 hash")
    selected = [n for n in raw_p7 if digest(read(z,n,MAX_IMAGE+512)) == expected_p7]
    if len(selected) != 1:
        raise AuditError(f"missing exact successful P7 for {folder}: retained={raw_p7}")
    p7 = read(z,selected[0],MAX_IMAGE+512)
    m = P7.match(p7)
    if not m or tuple(map(int,m.groups())) != expected or p7[m.end():] != rgba:
        raise AuditError("native P7 differs from actual PNG RGBA: "+folder)
    logs = [n for n in z.namelist()
            if n.startswith(folder+"/") and n.endswith("/native-process.log")]
    selected_logs = [n for n in logs if digest(read(z,n,MAX_LOG)) ==
                     receipt.get("native_process_log_sha256")]
    if len(selected_logs) != 1:
        raise AuditError(f"missing exact successful native route log for {folder}: retained={logs}")
    log = read(z,selected_logs[0],MAX_LOG).decode("utf8","replace")
    # A paused guest can have a frozen guest_frame while SDL PRESENT keeps
    # advancing. Pin the *drawable* ordinal and parse the recorded guest
    # frame as an independently witnessed nonnegative value.
    evidence = re.findall(
        r"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=(\d+) "
        r"guest_frame=(\d+) output=(\d+)x(\d+) "
        r"source=SDL_RenderReadPixels backend=sdl3", log)
    if (len(evidence) != 1 or
            tuple(map(int, (evidence[0][0], evidence[0][2], evidence[0][3]))) !=
            (receipt["observed_in_draw"], w, h)):
        raise AuditError("retained log does not witness successful SDL3 capture: "+folder)
    route = receipt.get("native_semantic_route")
    if route == "authentic-stock":
        before = log.split("UR_MODERN_VISUAL_SDL_CAPTURE status=saved",1)[0]
        if ("[snes_load]" not in before or
                "UR_BALDOSA_MODERN_DESTINATION stage=" in before or
                "UR_BALDOSA_MODERN_ROOT opened=1" in before or
                "UR_BALDOSA_MODERN_ROOT painted=1" in before):
            raise AuditError("Authentic capture contains Modern destination/paint")
        last_stage = "authentic-original"
    elif route == "play-stock-handoff":
        before = log.split("UR_MODERN_VISUAL_SDL_CAPTURE status=saved",1)[0]
        handoff = "UR_BALDOSA_MODERN_ROOT stock_entered players=1"
        if handoff not in before:
            raise AuditError("Play native stock handoff was not witnessed before SDL screenshot")
        prior, after_handoff = before.split(handoff, 1)
        if "UR_BALDOSA_MODERN_DESTINATION stage=root " not in prior:
            raise AuditError("Play stock handoff never started from native root")
        if ("UR_BALDOSA_MODERN_DESTINATION stage=" in after_handoff or
                "UR_BALDOSA_MODERN_ROOT reopened_painted=1" in after_handoff or
                "UR_BALDOSA_MODERN_ROOT painted=1" in after_handoff):
            raise AuditError("Modern frontend painted again after guest stock handoff")
        last_stage = "original-stock-1p-after-handoff"
    elif route in ROUTE_STAGES:
        before = log.split("UR_MODERN_VISUAL_SDL_CAPTURE status=saved",1)[0]
        painted = re.findall(
            r"UR_BALDOSA_MODERN_DESTINATION stage=([^\s]+) "
            r"raster=(\d+)x(\d+) root=(\d+),(\d+),(\d+),(\d+) "
            r"source=modern_product_view", before)
        expected_stage = ROUTE_STAGES[route]
        if not painted or painted[-1][0] != expected_stage:
            raise AuditError(
                "native semantic destination at capture is wrong for "+
                str(route)+": saw "+str([p[0] for p in painted[-1:]] or "none"))
        # The source selection contract is explicit: compact 4:3 (and 3:2)
        # allocates 256x224 with 240px root; wide allocates 342x224 with
        # 320px root. This prevents a 342-wide letterboxed root from being
        # mistaken for actual 4:3 layout simply because SDL output is 4:3.
        wide = w * 2 > h * 3
        expected_source = (342, 224, 11, 10, 320, 204) if wide else (
            256, 224, 8, 10, 240, 204)
        actual_source = tuple(map(int, painted[-1][1:]))
        if actual_source != expected_source:
            raise AuditError("native source canvas/root geometry mismatch: "
                             +str(actual_source)+" != "+str(expected_source))
        last_stage = painted[-1][0]
    else:
        raise AuditError("unknown semantic capture route: "+str(route))
    if (not isinstance(receipt.get("exe_sha256"),str) or
            not HEX.fullmatch(receipt["exe_sha256"])):
        raise AuditError("no executable SHA")
    if (not isinstance(receipt.get("source_sha"),str) or
            not SOURCE_HEX.fullmatch(receipt["source_sha"])):
        raise AuditError("no exact source SHA")
    return {
        "id":folder.rsplit("/",1)[-1], "pixels":[w,h],
        "original_p7":selected[0],
        "successful_process_log":selected_logs[0],
        "png_sha256":digest(png), "p7_sha256":digest(p7),
        "exe_sha256":receipt["exe_sha256"],
        "source_sha":receipt["source_sha"], "exact_rgba_bytes":w*h*4,
        "guest_frame_witness":int(evidence[0][1]),
        "native_painted_stage_at_capture":last_stage,
        # Once Play hands focus to guest stock, no current Modern root
        # geometry is authoritative. Only active Modern destination routes
        # advertise their native 342/256 source and panel dimensions.
        "native_source_canvas_at_capture":list(actual_source[:2]) if route in ROUTE_STAGES else [256,224],
        "native_root_geometry_at_capture":list(actual_source[2:]) if route in ROUTE_STAGES else None,
        "human_approved":False, "release_gate_credit":0,
    }


def verify(path: Path, expected_source_sha: str | None = None,
           expected_exe_sha: str | None = None) -> dict:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or any(
                n.startswith("/") or "\\" in n or ".." in PurePosixPath(n).parts
                for n in names):
            raise AuditError("duplicate, traversing or nonportable evidence paths")
        folders = sorted({name.rsplit("/",1)[0] for name in names
                          if name.endswith("/readback-receipt.json")})
        if not folders:
            raise AuditError("artifact contains no capture receipts")
        report = {
            "schema_version":1,
            "kind":"independent archived real native SDL P7/PNG/route transport",
            "artifact":path.name,
            "captures":[check_one(z,folder) for folder in folders],
            "visual_approved":False, "hardware_approved":False,
            "release_gate_credit":0,
        }
        if len({r["exe_sha256"] for r in report["captures"]}) != 1:
            raise AuditError("different native PE hashes in same capture artifact")
        if len({r["source_sha"] for r in report["captures"]}) != 1:
            raise AuditError("different native source epochs in same capture artifact")
        if expected_source_sha is not None and (
                not SOURCE_HEX.fullmatch(expected_source_sha) or
                report["captures"][0]["source_sha"] != expected_source_sha):
            raise AuditError("capture archive does not belong to required source SHA")
        if expected_exe_sha is not None and (
                not HEX.fullmatch(expected_exe_sha) or
                report["captures"][0]["exe_sha256"] != expected_exe_sha):
            raise AuditError("capture archive does not belong to required Windows PE")
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact",type=Path,required=True)
    parser.add_argument("--out",type=Path)
    parser.add_argument("--expected-source-sha")
    parser.add_argument("--expected-exe-sha")
    args = parser.parse_args()
    try:
        result = verify(args.artifact,args.expected_source_sha,args.expected_exe_sha)
        if args.out:
            if args.out.exists() or args.out.is_symlink():
                raise AuditError("report destination exists")
            args.out.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
        return 0
    except (AuditError,ValueError,OSError,KeyError,zipfile.BadZipFile) as exc:
        print("MODERN_NATIVE_ARCHIVE_REJECTED:",exc)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
