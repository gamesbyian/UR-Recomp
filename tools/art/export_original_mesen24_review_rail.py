#!/usr/bin/env python3
"""Export exact original Mesen24 sprites for the existing experimental 3D viewer.

Source-only, not an original 3D pose or GLB joint mapping.
"""
from __future__ import annotations
import argparse, hashlib, io, json, struct, tempfile, zipfile, zlib
from pathlib import Path
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.recover_original_mesen24_rom_pose_ids import (
    ROM_SHA, SOURCE_SHA, ROLES, TICKS, source_frame_tiles,
    render_original_primary_sprite64,
)

POSE_SHA = "6286aedcda6080acf832ecece9fcdb879354db008e870bc00ada02db3ff3aa20"
SCHEMA = "UR-ART4K-ORIGINAL-MESEN24-VIEWER-REFERENCE/1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def png_rgba64(rgba):
    """Deterministic 64x64 RGBA, index-zero remains transparent."""
    if type(rgba) is not bytes or len(rgba) != 64 * 64 * 4:
        raise ValueError("64x64 RGBA required")
    def chunk(tag, value):
        return (struct.pack(">I", len(value)) + tag + value +
                struct.pack(">I", zlib.crc32(tag + value) & 0xffffffff))
    scanlines = b"".join(b"\x00" + rgba[y*256:(y+1)*256] for y in range(64))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(scanlines, 9)) + chunk(b"IEND", b""))


def export(rom, original_zip, pose_raw):
    if len(rom) != 2097152 or sha(rom) != ROM_SHA:
        raise ValueError("incorrect original USA ROM")
    if sha(original_zip) != SOURCE_SHA or sha(pose_raw) != POSE_SHA:
        raise ValueError("incorrect authenticated original capture or pose IDs")
    pose = json.loads(pose_raw)
    if (pose.get("all_48_original_64x64_source_index_images_pixel_exact_from_ROM") is not True
            or pose.get("original_usa_ROM_sha256") != ROM_SHA
            or pose.get("original_Mesen24_source_archive_sha256") != SOURCE_SHA):
        raise ValueError("original source pose evidence unverified")
    candidates = source_frame_tiles(rom)
    files, records = {}, []
    with zipfile.ZipFile(io.BytesIO(original_zip)) as z:
        for role, (slot, tile, palette) in ROLES.items():
            rows = pose["per_original_source_racer"][role]["source_24_unique_per_tick_ROM_primary_frame_IDs"]
            if [row["authentic_original_bridge_tick"] for row in rows] != list(TICKS):
                raise ValueError("source tick ordering changed")
            for tick, row in zip(TICKS, rows):
                identifier = row["source_primary_frame_id"]
                if (type(identifier) is not int or not 0 <= identifier < 1536
                        or row["source_primary_phase_index"] != identifier // 64
                        or row["source_primary_angle_index"] != identifier % 64):
                    raise ValueError("invalid original ROM frame ID or axes")
                oam = decode_oam(z.read(f"frame-{tick:06d}-oam.bin"))[slot]
                obj = decode_source_obj(
                    oam, z.read(f"frame-{tick:06d}-vram.bin"),
                    z.read(f"frame-{tick:06d}-cgram.bin"),
                    oam_mode=4, obj_base=0x6000, second_table_offset=0x1000)
                original = render_original_primary_sprite64(candidates[identifier])
                if (original != obj["plane"]
                        or sha(original) != row["source_held_OAM_local_index_plane_sha256"]
                        or obj["slot"] != slot or obj["size"] != 64
                        or obj["source_palette_id"] != palette
                        or oam["source_oam_tile_word9"] != tile):
                    raise ValueError("ROM source and held Mesen pixel oracle disagree")
                name = f"{role}-{tick:04d}.png"
                image = png_rgba64(obj["rgba"])
                files[name] = image
                records.append({
                    "role": role, "tick": tick, "original_OAM_slot": slot,
                    "original_ROM_frame_ID": identifier,
                    "source_phase_index": identifier // 64,
                    "source_orientation_index": identifier % 64,
                    "source_4bpp_plane_sha256": sha(original),
                    "source_RGBA_sha256": sha(obj["rgba"]),
                    "png": name, "png_sha256": sha(image)})
    if len(files) != 48 or len(records) != 48:
        raise ValueError("missing original two-racer source evidence")
    packet = {
        "schema": SCHEMA, "source_USA_ROM_sha256": ROM_SHA,
        "original_Mesen24_source_sha256": SOURCE_SHA,
        "exact_original_ROM_pose_receipt_sha256": POSE_SHA,
        "source_pixel_size": [64, 64], "display_pixel_aspect": [7, 6],
        "original_1994_3D_mesh_camera_pose_recovered": False,
        "original_source_to_2026_GLB_joint_pose_verified": False,
        "source_sprite_index_zero_transparent": True, "frames": records}
    return packet, files


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom", required=True, type=Path)
    p.add_argument("--source-zip", required=True, type=Path)
    p.add_argument("--pose-ids", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    a = p.parse_args()
    if a.out_dir.exists():
        raise FileExistsError("refusing to overwrite original source rail")
    packet, files = export(a.rom.read_bytes(), a.source_zip.read_bytes(),
                           a.pose_ids.read_bytes())
    a.out_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".original-mesen24-", dir=a.out_dir.parent) as tmp:
        folder = Path(tmp)
        for name, image in files.items():
            (folder / name).write_bytes(image)
        (folder / "source-poses.json").write_text(
            json.dumps(packet, indent=2, sort_keys=True) + "\n")
        folder.rename(a.out_dir)
    print("ART4K_ORIGINAL_MESEN24_REVIEW_RAIL", len(packet["frames"]), POSE_SHA)


if __name__ == "__main__":
    main()
