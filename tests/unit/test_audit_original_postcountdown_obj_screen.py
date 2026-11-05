"""ROM-free adversarial controls for original post-countdown OBJ X-window test."""
from __future__ import annotations

import io
import json
from unittest import mock
import unittest
import zipfile

from tools.art.audit_original_postcountdown_obj_screen import (
    LEGACY_X_BOUNDS, SOURCE_ZIP_SHA, TICKS, WIDE_X_BOUNDS,
    measure_same_frame, source_archive_frames,
)
from tools.art.audit_original_mesen_obj_screen_pixels import sha
from tools.art.capture_original_mesen_ppu_raw import (
    REGIONS, ROM_SHA, MESEN_REVISION, SCHEMA as SNAP_SCHEMA, inspect_held_ppm,
)


def fabricated_archive(*, mutate=None):
    """Synthetics only. Never used by the CLI as authenticated original bytes."""
    manifest = {
        "schema": SNAP_SCHEMA,
        "original_USA_ROM_sha256": ROM_SHA,
        "emulator_source_revision": MESEN_REVISION,
        "source_original_snes_frame_skipping_disabled_requested": True,
        "original_held_framebuffer_P6_exported": True,
        "source_original_live_OAM_sprite_to_racer_identity_verified": False,
        "original_PPU_RGB_to_source_OBJ_pixel_ownership_verified": False,
        "source_held_display_to_current_PPU_scanout_phase_independently_aligned": False,
        "source_held_display_RGB_reproducibility_across_runs_independently_verified": False,
        "actual_raw_SNES_sprite_RAM_VRAM_CGRAM_snapshots": len(TICKS),
        "frames": [],
    }
    members = {}
    for tick in TICKS:
        rows = {}
        for region, (memtype, size) in REGIONS.items():
            filename = f"frame-{tick:06d}-{region}.bin"
            raw = bytes([tick % 256]) * size
            members["data/" + filename] = raw
            rows[region] = {
                "relative_file": filename,
                "sha256": sha(raw),
                "byte_size": size,
                "mesen_memory_type": memtype,
            }
        filename = f"frame-{tick:06d}-held-display.ppm"
        image = b"P6\n256 239\n255\n" + bytes(256 * 239 * 3)
        members["data/" + filename] = image
        screen = inspect_held_ppm(
            image, {"path": "/synthetic/frame.ppm", "format": "P6",
                    "width": 256, "height": 239, "pixels": 256*239},
            "/synthetic/frame.ppm",
        )
        screen["relative_file"] = filename
        manifest["frames"].append({
            "emulator_bridge_frame": tick,
            "replayed_controller_step_index": tick - 1,
            "raw_original_snes_ppu_memory": rows,
            "original_emulator_held_display_P6": screen,
        })
    if mutate == "wrong_tick":
        manifest["frames"][2]["emulator_bridge_frame"] = 1703
    elif mutate == "wrong_mode":
        manifest["source_original_snes_frame_skipping_disabled_requested"] = False
    elif mutate == "wrong_hash":
        members["data/frame-001601-oam.bin"] = b"\xFF" + members[
            "data/frame-001601-oam.bin"][1:]
    if mutate == "missing_screen":
        del members["data/frame-001602-held-display.ppm"]
    members["data/original-raw-ppu-and-video-manifest.json"] = json.dumps(
        manifest, sort_keys=True).encode()
    if mutate == "duplicate_manifest":
        members["another/original-raw-ppu-and-video-manifest.json"] = members[
            "data/original-raw-ppu-and-video-manifest.json"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename, data in sorted(members.items()):
            archive.writestr(filename, data)
    return buffer.getvalue()


class OriginalObjXBoundsTests(unittest.TestCase):
    def test_synthetic_archive_and_all_five_held_sources_are_sha_verified(self):
        raw = fabricated_archive()
        rows = source_archive_frames(raw, expected_zip_sha=sha(raw))
        self.assertEqual([r["tick"] for r in rows], list(TICKS))
        self.assertEqual([len(r["oam"]) for r in rows], [544]*5)
        self.assertEqual([len(r["vram"]) for r in rows], [65536]*5)
        self.assertEqual([len(r["cgram"]) for r in rows], [512]*5)
        self.assertEqual([len(r["rgb"]) for r in rows], [256*239*3]*5)
        with self.assertRaisesRegex(ValueError, "authenticated"):
            source_archive_frames(raw)  # CLI defaults to immutable real SHA

    def test_invalid_source_archives_never_enter_matching(self):
        for kind in ("wrong_tick", "wrong_mode", "wrong_hash",
                     "missing_screen", "duplicate_manifest"):
            with self.subTest(kind=kind):
                raw = fabricated_archive(mutate=kind)
                with self.assertRaises((ValueError, KeyError)):
                    source_archive_frames(raw, expected_zip_sha=sha(raw))
        with self.assertRaisesRegex(ValueError, "ZIP absent"):
            source_archive_frames(b"", expected_zip_sha=sha(b""))

    def test_diagnostic_keeps_historical_bounds_and_uses_wide_only_opt_in(self):
        frames = [{"tick": tick, "oam": bytes(544),
                   "vram": bytes(65536), "cgram": bytes(512),
                   "rgb": bytes(256*239*3)} for tick in TICKS]
        def fake_match(obj, rgb, *, upper, horizontal_origin_bounds):
            return {
                "exact_opaque_RGB_pixel_matches":
                    2 if horizontal_origin_bounds == WIDE_X_BOUNDS else 1,
                "total_source_OBJ_opaque_pixels": 3,
                "source_screen_x": 48 if upper else 82,
                "source_screen_y": 47 if upper else 160,
                "source_screen_region": "upper" if upper else "lower",
                "complete_pixel_match": False,
            }
        with (mock.patch("tools.art.audit_original_postcountdown_obj_screen.decode_oam",
                         return_value=[{}]*128),
              mock.patch("tools.art.audit_original_postcountdown_obj_screen.decode_source_obj",
                         return_value={"size": 64, "opaque_count": 3}),
              mock.patch("tools.art.audit_original_postcountdown_obj_screen.best_opaque_matches",
                         side_effect=fake_match) as matcher):
            result = measure_same_frame(frames)
        rows = result["source_2D_extended_horizontal_search"]
        self.assertEqual(len(rows), 10)
        self.assertEqual([r["original_held_OBJ_slot"] for r in rows], [96,97]*5)
        self.assertEqual([r["additional_exact_matches_by_x_expansion"] for r in rows], [1]*10)
        self.assertEqual({tuple(c.kwargs["horizontal_origin_bounds"])
                          for c in matcher.call_args_list}, {LEGACY_X_BOUNDS, WIDE_X_BOUNDS})
        self.assertFalse(result["source_per_scanline_OBJ_ownership_proved"])
        self.assertFalse(result["original_source_3D_mesh_rig_camera_recovered"])
        self.assertFalse(result["owner_likeness_approved"])
        self.assertEqual(result["authenticated_source_artifact_ZIP_sha256"], SOURCE_ZIP_SHA)

    def test_authentic_five_frame_numeric_receipt_preserves_negative_gates(self):
        from pathlib import Path
        from tools.art.audit_original_postcountdown_obj_screen import SOURCE_ZIP_SHA
        path = (Path(__file__).resolve().parents[2] /
                "analysis/data/racer-original-postcountdown-horizontal-window-real-20261103.json")
        receipt = json.loads(path.read_text())
        self.assertEqual(receipt["source_original_artifact_zip_sha256"], SOURCE_ZIP_SHA)
        self.assertTrue(receipt["original_source_ppu_memory_and_P6_per_file_shas_checked"])
        rows = receipt["source_2d_experiment_rows"]
        self.assertEqual(len(rows), 10)
        self.assertEqual([(r["tick"], r["original_oam_slot"]) for r in rows],
                         [(tick, slot) for tick in TICKS for slot in (96, 97)])
        self.assertEqual([r["historical_x_76_to_170_exact_matches"]
                          for r in rows if r["original_oam_slot"] == 97], [0]*5)
        self.assertEqual([r["wide_x_0_to_192_exact_matches"]
                          for r in rows if r["original_oam_slot"] == 97],
                         [132, 134, 134, 128, 132])
        self.assertEqual([r["wide_x_0_to_192_exact_matches"]
                          for r in rows if r["original_oam_slot"] == 96],
                         [281, 277, 281, 282, 281])
        for row in rows:
            self.assertEqual(
                row["additional_matches_due_only_to_horizontal_search"],
                row["wide_x_0_to_192_exact_matches"] -
                row["historical_x_76_to_170_exact_matches"])
        for gate in ("source_per_scanline_sprite_ownership_verified",
                     "original_sprite_priority_and_overlay_occlusion_classification_verified",
                     "source_to_2026_experimental_GLB_pose_alignment_verified",
                     "owner_likeness_approved"):
            self.assertFalse(receipt[gate])

    def test_refuses_nonconsecutive_held_frame_input(self):
        frames = [{"tick": tick} for tick in TICKS]
        frames[1]["tick"] += 1
        with self.assertRaisesRegex(ValueError, "frame sequence"):
            measure_same_frame(frames)


if __name__ == "__main__":
    unittest.main()
