#!/usr/bin/env python3
"""Reproduce original Mesen PPU/held-screen cross-run disagreement.

Independent ROM execution is not performed here: both existing original-emulator
artifacts must match immutable source ZIP and manifest hashes. Exact original
OAM/VRAM/CGRAM identity with different screens disproves repeatability of the
held display as a uniquely registered PPU raster, not the original 3D anatomy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from tools.art.no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-ORIGINAL-MESEN-PPU-SCREEN-REPEATABILITY/1"
SOURCE_SCHEMA = "UR-ART4K-MESENCE-LIVE-RAW-SNES-PPU-STATES/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
REPLAY_SHA = "28f2842fd262030e434b3aef88eb360f74de94fbf558f0eb0ba8edce645fb490"
EMULATOR_SHA = "8d501dcdea86837387df1c1bca1e7660d2a5b1adbe822beff4f82935a50fe94b"
SOURCE_REV = "a60e79feb4d6dcced5922d636f9211837d01e381"
RUNS = {
    "first": {
        "id": 41565384581,
        "zip_sha": "b72a1c805423f14847b257fe807be84559aa2a9e8914314ce1b8d24532f95964",
        "manifest_sha": "e63c9e51d82befcd9720439aaf5e37a822837690c0b64f52759466999700c38d",
    },
    "second": {
        "id": 41566836578,
        "zip_sha": "24b70f3a3468d628d57c1bc1a43915e8abaecb6a66dc6156fcb4b685a73610e2",
        "manifest_sha": "acd5c844e243d50c421892f53aba5d128dc5561e71759281e9e12d9767421185",
    },
}
W, H = 256, 239
N = W * H
HEADER = f"P6\n{W} {H}\n255\n".encode("ascii")
REGIONS = {"oam": 544, "vram": 65536, "cgram": 512}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def changed_rgb_pixels(a: bytes, b: bytes) -> int:
    if not isinstance(a, bytes) or not isinstance(b, bytes) or len(a) != 3 * N or len(b) != 3 * N:
        raise ValueError("exact 256x239 RGB original screen pixel arrays required")
    return sum(a[i:i+3] != b[i:i+3] for i in range(0, 3*N, 3))


def read_original_run(path: Path, run: str) -> dict:
    evidence = RUNS[run]
    raw = path.read_bytes()
    if digest(raw) != evidence["zip_sha"]:
        raise ValueError("original Mesen executable-run artifact ZIP SHA differs")
    with ZipFile(path) as archive:
        names = archive.namelist()
        expected = {"manifest.json"}
        for tick in (1219, 1220):
            expected.update(f"frame-{tick:06d}-{region}.bin" for region in REGIONS)
            expected.add(f"frame-{tick:06d}-held-display.ppm")
        if len(names) != len(expected) or set(names) != expected:
            raise ValueError("original Mesen PPU/archive inventory changed")
        manifest_bytes = archive.read("manifest.json")
        if digest(manifest_bytes) != evidence["manifest_sha"]:
            raise ValueError("actual original held screen manifest SHA differs")
        manifest = json.loads(manifest_bytes)
        if (manifest.get("schema") != SOURCE_SCHEMA or
                manifest.get("original_USA_ROM_sha256") != ROM_SHA or
                manifest.get("original_input_replay_sha256") != REPLAY_SHA or
                manifest.get("actual_emulator_executable_sha256") != EMULATOR_SHA or
                manifest.get("emulator_source_revision") != SOURCE_REV or
                manifest.get("original_held_framebuffer_P6_exported") is not True or
                manifest.get("original_PPU_RGB_to_source_OBJ_pixel_ownership_verified") is not False or
                manifest.get("source_held_display_to_current_PPU_scanout_phase_independently_aligned") is not False):
            raise ValueError("original source ROM/replay/scanout provenance changed")
        rows = manifest.get("frames")
        if not isinstance(rows, list) or [x.get("emulator_bridge_frame") for x in rows] != [1219, 1220]:
            raise ValueError("actual original held emulator frame identities changed")
        frames = {}
        for row in rows:
            tick = row["emulator_bridge_frame"]
            region_records = row["raw_original_snes_ppu_memory"]
            if set(region_records) != set(REGIONS):
                raise ValueError("incomplete original SNES source memory regions")
            hashes = {}
            for region, length in REGIONS.items():
                metadata = region_records[region]
                filename = f"frame-{tick:06d}-{region}.bin"
                bytes_ = archive.read(filename)
                if (metadata["relative_file"] != filename or
                        metadata["byte_size"] != length or
                        len(bytes_) != length or digest(bytes_) != metadata["sha256"]):
                    raise ValueError("actual original source PPU region contents differ")
                hashes[region] = digest(bytes_)
            screen = row["original_emulator_held_display_P6"]
            filename = f"frame-{tick:06d}-held-display.ppm"
            ppm = archive.read(filename)
            if (screen["relative_file"] != filename or
                    screen["source_display_width"] != W or
                    screen["source_display_height"] != H or
                    screen["source_format"] != "P6" or
                    screen["byte_size"] != len(ppm) or
                    screen["sha256"] != digest(ppm) or
                    len(ppm) != len(HEADER) + 3*N or not ppm.startswith(HEADER) or
                    screen["source_framebuffer_RGB_sha256"] != digest(ppm[len(HEADER):])):
                raise ValueError("original Mesen held P6 framebuffer bytes differ")
            frames[tick] = {"screen_rgb": ppm[len(HEADER):],
                            "screen_sha": digest(ppm),
                            "source_ppu_sha": hashes}
    return {"run_id": evidence["id"], "frames": frames}


def compare_sources(a: dict, b: dict) -> dict:
    if set(a["frames"]) != {1219, 1220} or set(b["frames"]) != {1219, 1220}:
        raise ValueError("different original held frame identifiers")
    compared = {}
    for tick in (1219, 1220):
        l, r = a["frames"][tick], b["frames"][tick]
        if l["source_ppu_sha"] != r["source_ppu_sha"]:
            raise ValueError("not the same original OAM/VRAM/CGRAM state across executions")
        compared[str(tick)] = {
            "first_held_screen_sha256": l["screen_sha"],
            "second_held_screen_sha256": r["screen_sha"],
            "same_original_raw_PPU_region_hashes": True,
            "RGB_pixels_different_across_executions":
                changed_rgb_pixels(l["screen_rgb"], r["screen_rgb"]),
        }
    within = {
        str(source["run_id"]): changed_rgb_pixels(
            source["frames"][1219]["screen_rgb"],
            source["frames"][1220]["screen_rgb"],
        ) for source in (a, b)
    }
    all_equal = all(x["RGB_pixels_different_across_executions"] == 0
                    for x in compared.values())
    return {
        "schema": SCHEMA,
        "source_original_emulator_runs": [a["run_id"], b["run_id"]],
        "original_USA_ROM_sha256": ROM_SHA,
        "original_replay_sha256": REPLAY_SHA,
        "pinned_mesen_executable_sha256": EMULATOR_SHA,
        "source_visible_rgb_dimensions": [W, H],
        "source_total_visible_RGB_pixels_per_frame": N,
        "source_emulated_ticks": [1219, 1220],
        "across_executions_same_tick": compared,
        "within_execution_changed_RGB_pixels_by_run": within,
        "source_original_OAM_VRAM_CGRAM_sha_identical_across_executions": True,
        "screen_RGB_repeatable_across_executions": all_equal,
        "source_screen_to_current_PPU_scanout_phase_independently_aligned": False,
        "original_source_OAM_to_racer_pixel_ownership_verified": False,
        "1994_original_3D_rig_or_camera_verified": False,
        "owner_likeness_approved": False,
        "interpretation": (
            "Original ROM, replay, executable and all three raw PPU memory "
            "region hashes are identical at these held ticks, but exported "
            "RGB screen differs. Distinguish unobserved PPU state or screen "
            "buffer phase from the original emulator memory; neither original "
            "visible sprite-to-part registration nor deterministic screenshot "
            "replay is established by the held tick alone."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--first-original-source-zip", type=Path, required=True)
    p.add_argument("--second-original-source-zip", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    opts = p.parse_args()
    report = compare_sources(
        read_original_run(opts.first_original_source_zip, "first"),
        read_original_run(opts.second_original_source_zip, "second"),
    )
    publish_text_once(opts.out, json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "source_held_RGB_repeatable": report["screen_RGB_repeatable_across_executions"],
        "per_tick_changed_pixels": {x: y["RGB_pixels_different_across_executions"]
                                    for x, y in report["across_executions_same_tick"].items()},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
