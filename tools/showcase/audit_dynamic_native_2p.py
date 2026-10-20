#!/usr/bin/env python3
"""Independent two-pilot native 2P recording verification and visual contacts."""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

NAMES = ("p1-leads", "p2-leads")
SAMPLES = (30, 120, 210, 300, 390, 480, 570, 660, 750, 840)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def inspect(folder, route_manifest, binary_file, rom_sha, source_sha, names=NAMES):
    route_data = json.loads(Path(route_manifest).read_text())
    routes = route_data.get("routes", route_data.get("cases"))
    if not isinstance(routes, dict) or not names or len(names) != len(set(names)):
        raise ValueError("Missing/duplicate proposed routes")
    out = {
        "schema": "UR-GENUINE-ASYNCHRONOUS-NATIVE-2P/1",
        "source_head": source_sha,
        "rom_sha256": rom_sha,
        "native_binary_sha256": Path(binary_file).read_text().split()[0],
        "source_game_commit": "10b864b9d14a7b7416dd909eb7b054c88faef101",
        "source_framework_commit": "075fbe4c8e0d97b0013be541795c39cb644a9709",
        "recorded_capture_guest_frame_ids": [2100, 2999],
        "two_player_gameplay_confirmed": False,
        "visible_airborne_or_completed_trick_confirmed": False,
        "source_is_genuine_continuous_native_frames": True,
        "motion_interpolation": False,
        "source_logic_or_physics_modified": False,
        "review_status": "awaiting visual inspection, inputs alone are not trick proof",
        "routes": {}
    }
    for name in names:
        if name not in routes:
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
        if (verified["control_guest_crc_sha256"] != verified["recorded_guest_crc_sha256"]
                or verified["dropped_or_skipped_host_frame_ids"] != 0
                or verified["guest_frame_start"] != 2100
                or verified["guest_frame_end"] != 2999):
            raise ValueError(f"Failed no-video / recording non-interference: {name}")
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
            d.text((x + 10, y + 7), f"{name}  guest frame {2100+ordinal}", fill="white")
            hashes[q.name] = sha(q)
        sheet_path = folder / f"{name}-contact-sheet.png"
        sheet.save(sheet_path)
        out["routes"][name] = {
            **routes[name],
            "movie": movie.name,
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
    p.add_argument("--native-sha", type=Path, required=True)
    p.add_argument("--rom-sha", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--names", nargs="+", default=list(NAMES))
    a = p.parse_args()
    a.publish.mkdir(parents=True, exist_ok=True)
    doc = inspect(a.publish, a.route_manifest, a.native_sha, a.rom_sha,
                  a.source_sha, names=a.names)
    (a.publish / "dynamic-racing-provenance.json").write_text(
        json.dumps(doc, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"movies": {k: v["sha256"] for k, v in doc["routes"].items()},
                      "status": doc["review_status"]}, indent=2))


if __name__ == "__main__":
    main()
