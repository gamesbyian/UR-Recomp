#!/usr/bin/env python3
"""Independent two-pilot native 2P recording verification and visual contacts."""
import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
from pathlib import Path


NAMES = ("p1-leads", "p2-leads")
SAMPLES = (30, 120, 210, 300, 390, 480, 570, 660, 750, 840)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def read_world_snapshot(path: Path) -> dict:
    """4 original 7E WRAM player-position words; no false path-distance claim."""
    data = path.read_bytes()
    if len(data) != 0x20000:
        raise ValueError("Invalid 128KiB guest WRAM scene dump")
    p1x, p2x, p1y, p2y = (struct.unpack_from("<H", data, off)[0]
                          for off in (0x0411, 0x0413, 0x0415, 0x0417))
    return {
        "p1_world_x_u16": p1x,
        "p2_world_x_u16": p2x,
        "p1_world_y_u16": p1y,
        "p2_world_y_u16": p2y,
        "raw_abs_x_difference": abs(p1x - p2x),
        "raw_abs_y_difference": abs(p1y - p2y),
        "distance_status": "raw_coordinate_difference_not_course_arc_distance",
    }


def read_guest_dump_witnesses(work_root: Path, name: str) -> list[dict]:
    """Compare exact semantic dump tags with no-video control run."""
    cases = ("cinematic-lead", "cinematic-middle", "cinematic-late")
    ctrl = work_root / f"{name}-control"
    rec = work_root / f"{name}-recorded"
    ctrl_log = (ctrl / "log.txt").read_text(errors="replace")
    rec_log = (rec / "log.txt").read_text(errors="replace")
    out = []
    for tag in cases:
        pattern = r"script f=(\d+) dump " + re.escape(tag) + r" ok"
        a = re.findall(pattern, ctrl_log)
        b = re.findall(pattern, rec_log)
        if len(a) != 1 or len(b) != 1 or a[0] != b[0]:
            raise ValueError(f"Guest semantic dump tag missing/nonidentical: {name}/{tag}")
        path_control = ctrl / "dump" / f"{tag}.wram.bin"
        path_recorded = rec / "dump" / f"{tag}.wram.bin"
        if sha(path_control) != sha(path_recorded):
            raise ValueError(f"Source WRAM changed with recording: {name}/{tag}")
        out.append({
            "tag": tag,
            "guest_frame": int(a[0]),
            "control_vs_recorded_wram_sha256": sha(path_control),
            **read_world_snapshot(path_recorded),
        })
    return out


def inspect(folder, route_manifest, binary_file, rom_sha, source_sha, names=NAMES, work_root=None):
    # Unit-level guest-position tests must work without optional media dependencies.
    from PIL import Image, ImageDraw, ImageOps
    route_data = json.loads(Path(route_manifest).read_text())
    routes = route_data.get("routes", route_data.get("cases"))
    if not isinstance(routes, dict) or not names or len(names) != len(set(names)):
        raise ValueError("Missing/duplicate proposed routes")
    out = {
        "schema": "UR-GENUINE-ASYNCHRONOUS-NATIVE-2P/1",
        "source_head": source_sha,
        "rom_sha256": rom_sha,
        "native_binary_sha256": (Path(binary_file).read_text().split()[0] if binary_file else None),
        "native_binary_sha256_unavailable_reason": ("original artifact excluded its binary checksum text file; native source commits and signed CI provenance retained" if binary_file is None else None),
        "source_game_commit": "10b864b9d14a7b7416dd909eb7b054c88faef101",
        "source_framework_commit": "075fbe4c8e0d97b0013be541795c39cb644a9709",
        "recording_origin": "111 guest frames after observed stock race GO, bounded below by absolute source frame 1990",
        "two_player_gameplay_confirmed": False,
        "visible_airborne_or_completed_trick_confirmed": False,
        "source_is_genuine_continuous_native_frames": True,
        "motion_interpolation": False,
        "source_logic_or_physics_modified": False,
        "review_status": "awaiting visual inspection, inputs alone are not trick proof",
        "routes": {}
    }
    for name in names:
        if work_root is None:
            raise ValueError("Real original guest world-position witness directory required")
        route_key = name if name in routes else f"{name}.txt"
        if route_key not in routes:
            raise ValueError("Missing variant in controller manifest")
        movie = folder / f"native-{name}-900f.mp4"
        verified = json.loads((folder / f"verified-{name}.json").read_text())
        stream = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-count_frames",
            "-select_streams", "v:0", "-show_entries",
            "stream=width,height,r_frame_rate,nb_read_frames", "-of", "json", str(movie)
        ]))["streams"][0]
        if (stream["width"], stream["height"], stream["r_frame_rate"],
                int(stream["nb_read_frames"])) != (1920, 1080, "60/1", 900):
            raise ValueError(f"Unexpected movie duration and geometry {name}: {stream}")
        clock_path = folder / f"capture-clock-{name}.json"
        clock = json.loads(clock_path.read_text())
        expected_start = max(1990, clock["source_go_guest_frame"] + 111)
        if (not clock["source_control_equals_recorded_go"]
                or clock["capture_start_guest_frame"] != expected_start
                or clock["capture_end_guest_frame"] != expected_start + 899
                or verified["guest_frame_start"] != expected_start
                or verified["guest_frame_end"] != expected_start + 899
                or verified["control_guest_crc_sha256"] != verified["recorded_guest_crc_sha256"]
                or verified["dropped_or_skipped_host_frame_ids"] != 0):
            raise ValueError(f"Failed GO-relative/guest non-interference: {name}")
        expr = "+".join(f"eq(n\\,{n})" for n in SAMPLES)
        target = folder / f"{name}-sample-%02d.png"
        subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                        "-y", "-i", str(movie), "-vf", f"select={expr}",
                        "-fps_mode", "vfr", "-frames:v", str(len(SAMPLES)),
                        "-start_number", "0", str(target)], check=True)
        sheet = Image.new("RGB", (1920, 900), "#061120")
        d = ImageDraw.Draw(sheet)
        hashes = {}
        for idx, ordinal in enumerate(SAMPLES):
            p = folder / f"{name}-sample-{idx:02d}.png"
            q = folder / f"{name}-frame-{ordinal:04d}.png"
            if not p.exists():
                raise ValueError(f"No sample: {idx}")
            p.rename(q)
            with Image.open(q) as img:
                if img.size != (1920, 1080):
                    raise ValueError(f"Unexpected PNG: {q}")
                img.load()
                thumb = ImageOps.contain(img, (470, 263))
            with Image.open(q) as img:
                img.verify()
            x = (idx % 4) * 480
            y = (idx // 4) * 300
            sheet.paste(thumb, (x, y + 28))
            d.text((x + 10, y + 7), f"{name}  guest frame {expected_start+ordinal}", fill="white")
            hashes[q.name] = sha(q)
        sheet_path = folder / f"{name}-contact-sheet.png"
        sheet.save(sheet_path)
        witnesses = read_guest_dump_witnesses(work_root, name)
        out["routes"][name] = {
            "real_guest_world_position_witnesses": witnesses,
            "world_position_measurement_caveat": "raw original 7E:0411/0413 and 0415/0417 words; do not assert track-arc distance",
            **routes[route_key],
            "movie": movie.name,
            "capture_go_frame": clock["source_go_guest_frame"],
            "capture_frame_start_end": [expected_start, expected_start + 899],
            "capture_clock_sha256": sha(clock_path),
            "sha256": sha(movie),
            "recording_input_versus_control_crc_sha256": verified["recorded_guest_crc_sha256"],
            "source_lossless_sha256": verified["master"]["sha256"],
            "frame_index_sha256": verified["index_sha256"],
            "frame_sample_sha256": hashes,
            "contact_sheet_sha256": sha(sheet_path),
            "presented_gameplay": "source-frame-authentic native 342-column Original renderer",
            "delivery_drawable": [1920, 1080],
            "captured_physical_drawable": verified["dimensions"]["actual_sdl_drawable"],
        }
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--publish", type=Path, required=True)
    p.add_argument("--route-manifest", type=Path, required=True)
    p.add_argument("--native-sha", type=Path)
    p.add_argument("--salvage-artifact-without-native-binary-hash", action="store_true")
    p.add_argument("--rom-sha", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--names", nargs="+", default=list(NAMES))
    a = p.parse_args()
    a.publish.mkdir(parents=True, exist_ok=True)
    if (a.native_sha is None) == (not a.salvage_artifact_without_native_binary_hash):
        p.error("Supply exactly one of --native-sha or --salvage-artifact-without-native-binary-hash")
    doc = inspect(a.publish, a.route_manifest, a.native_sha, a.rom_sha,
                  a.source_sha, names=a.names, work_root=a.work_root)
    (a.publish / "dynamic-racing-provenance.json").write_text(
        json.dumps(doc, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"movies": {k: v["sha256"] for k, v in doc["routes"].items()},
                      "status": doc["review_status"]}, indent=2))


if __name__ == "__main__":
    main()
