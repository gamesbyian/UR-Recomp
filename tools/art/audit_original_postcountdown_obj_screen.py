#!/usr/bin/env python3
"""Reassess held original post-countdown 2D OBJ placement using existing bytes.

This diagnostic reuses the one-pass authentic MesenCE capture, no emulator
replay. A 2D opaque-colour overlap is not per-scanline sprite ownership and
cannot validate any original 3D geometry, camera or shipping likeness.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import tempfile
import zipfile

from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import (
    best_opaque_matches, decode_source_obj, p6_screen, sha,
)
from tools.art.capture_original_mesen_ppu_raw import (
    REGIONS, ROM_SHA, MESEN_REVISION, validate_snapshot_files,
)
from tools.art.no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-POSTCOUNTDOWN-BOUNDED-OBJ-X-SEARCH/1"
SOURCE_ZIP_SHA = "d7d3e312528563bae0940ed97258024103085576c385334253458af501744ab7"
TICKS = tuple(range(1601, 1606))
LEGACY_X_BOUNDS = (76, 170)
WIDE_X_BOUNDS = (0, 192)


def source_archive_frames(raw_zip: bytes, *, expected_zip_sha: str = SOURCE_ZIP_SHA):
    """Verify source bytes, then return the original held screen/PPU snapshots.

    Alternate expected hashes are allowed only for explicit synthetic tests.
    The CLI always uses the fixed independently authenticated ZIP SHA.
    """
    if not isinstance(raw_zip, bytes) or not raw_zip or len(raw_zip) > 16_000_000:
        raise ValueError("original source ZIP absent or exceeds diagnostic cap")
    if sha(raw_zip) != expected_zip_sha:
        raise ValueError("not the authenticated original post-countdown source ZIP")
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as z:
        infos = z.infolist()
        if len(infos) > 200 or sum(i.file_size for i in infos) > 16_000_000:
            raise ValueError("original source ZIP member budget exceeded")
        manifest_names = [
            i.filename for i in infos
            if i.filename.rsplit("/", 1)[-1] ==
            "original-raw-ppu-and-video-manifest.json"
        ]
        if len(manifest_names) != 1:
            raise ValueError("one original combined PPU/video manifest required")
        prefix = manifest_names[0].rsplit("/", 1)[0] + "/" if "/" in manifest_names[0] else ""
        manifest = json.loads(z.read(manifest_names[0]))
        frames = manifest.get("frames", [])
        if ([f.get("emulator_bridge_frame") for f in frames] != list(TICKS) or
                manifest.get("original_USA_ROM_sha256") != ROM_SHA or
                manifest.get("emulator_source_revision") != MESEN_REVISION or
                manifest.get("original_held_framebuffer_P6_exported") is not True or
                manifest.get("source_original_snes_frame_skipping_disabled_requested") is not True):
            raise ValueError("original live source manifest provenance/ticks changed")
        with tempfile.TemporaryDirectory(prefix="original-art4k-obj-") as temporary:
            root = Path(temporary)
            for frame in frames:
                tick = frame["emulator_bridge_frame"]
                for region, (_, size) in REGIONS.items():
                    name = f"frame-{tick:06d}-{region}.bin"
                    info = z.getinfo(prefix + name)
                    if info.file_size != size:
                        raise ValueError("source original PPU region has wrong size")
                    (root / name).write_bytes(z.read(info))
                name = f"frame-{tick:06d}-held-display.ppm"
                info = z.getinfo(prefix + name)
                if info.file_size != len(b"P6\n256 239\n255\n") + 256*239*3:
                    raise ValueError("source original P6 screen has wrong size")
                (root / name).write_bytes(z.read(info))
            validate_snapshot_files(root, manifest)
            result = []
            for frame in frames:
                tick = frame["emulator_bridge_frame"]
                read = lambda region: (root / f"frame-{tick:06d}-{region}.bin").read_bytes()
                result.append({
                    "tick": tick,
                    "oam": read("oam"), "vram": read("vram"),
                    "cgram": read("cgram"),
                    "rgb": p6_screen((root / f"frame-{tick:06d}-held-display.ppm").read_bytes()),
                })
            return result


def measure_same_frame(frames: list[dict]) -> dict:
    if [frame.get("tick") for frame in frames] != list(TICKS):
        raise ValueError("source original frame sequence invalid")
    rows = []
    for frame in frames:
        oam = decode_oam(frame["oam"])
        for slot, upper, colour in ((96, False, "blue"), (97, True, "red")):
            obj = decode_source_obj(
                oam[slot], frame["vram"], frame["cgram"],
                oam_mode=4, obj_base=0x6000, second_table_offset=0x1000,
            )
            if obj["size"] != 64 or not 0 < obj["opaque_count"] <= 4096:
                raise ValueError("source original racer OBJ size/alpha invalid")
            original = best_opaque_matches(
                obj, frame["rgb"], upper=upper,
                horizontal_origin_bounds=LEGACY_X_BOUNDS,
            )
            wider = best_opaque_matches(
                obj, frame["rgb"], upper=upper,
                horizontal_origin_bounds=WIDE_X_BOUNDS,
            )
            before = original["exact_opaque_RGB_pixel_matches"]
            after = wider["exact_opaque_RGB_pixel_matches"]
            if after < before:
                raise ValueError("expanded original search illegally reduced optimum")
            rows.append({
                "tick": frame["tick"],
                "original_held_OBJ_slot": slot,
                "original_2D_colourway": colour,
                "original_opaque_source_OBJ_pixels": obj["opaque_count"],
                "countdown_horizontal_origin_bounds": list(LEGACY_X_BOUNDS),
                "extended_horizontal_origin_bounds": list(WIDE_X_BOUNDS),
                "historical_window": original,
                "extended_window": wider,
                "additional_exact_matches_by_x_expansion": after-before,
                "full_opaque_source_colour_match_in_extended_window":
                    wider["complete_pixel_match"],
            })
    return {
        "schema": SCHEMA,
        "authenticated_source_artifact_ZIP_sha256": SOURCE_ZIP_SHA,
        "source_original_ROM_sha256": ROM_SHA,
        "source_mesen_revision": MESEN_REVISION,
        "source_original_frames": list(TICKS),
        "source_2D_extended_horizontal_search": rows,
        "source_per_scanline_OBJ_ownership_proved": False,
        "original_source_3D_mesh_rig_camera_recovered": False,
        "source_to_experimental_GLB_pose_alignment_verified": False,
        "owner_likeness_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-postcountdown-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    frames = source_archive_frames(args.original_postcountdown_zip.read_bytes())
    result = measure_same_frame(frames)
    publish_text_once(args.out, json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "original_2D_frame_count": len(TICKS),
        "countdown_search_X_exclusion_tested": True,
        "source_2D_colour_matches": [
            {"tick": r["tick"], "slot": r["original_held_OBJ_slot"],
             "legacy": r["historical_window"]["exact_opaque_RGB_pixel_matches"],
             "wide": r["extended_window"]["exact_opaque_RGB_pixel_matches"],
             "position": [r["extended_window"]["source_screen_x"],
                          r["extended_window"]["source_screen_y"]]}
            for r in result["source_2D_extended_horizontal_search"]
        ],
        "original_3D_accepted": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
