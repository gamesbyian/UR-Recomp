"""ROM-free regression: nine actual sourced GLB SHA pins, legacy default preserved."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.art import study_original_racer_eighth_ride_motion as eighth
from tools.art.study_original_racer_continuous_ride_motion import (
    TIMES as LEGACY_TIMES, PINNED_GRID_GLB_SHA, validate_sample_receipt,
)


class EighthRideSourceTests(unittest.TestCase):
    def test_eighth_phases_and_source_pins_not_legacy_five(self):
        self.assertEqual(len(eighth.TIMES), 9)
        self.assertEqual(tuple(float(t) for t in eighth.TIMES),
                         tuple(i/8 for i in range(9)))
        self.assertEqual(set(eighth.TIMES), set(eighth.SHA))
        self.assertEqual(len(set(eighth.SHA.values())), 9)
        self.assertTrue(all(len(sha) == 64 for sha in eighth.SHA.values()))
        self.assertEqual(LEGACY_TIMES, ("0.0", "0.25", "0.5", "0.75", "1.0"))
        self.assertNotEqual(PINNED_GRID_GLB_SHA["0.0"], eighth.SHA["0.0"])

    def test_exact_eighth_time_receipt_is_allowed_only_by_pinned_grid(self):
        sha = eighth.SHA["0.125"]
        q = {
            "schema": "UR-ART4K-REAL-CONTINUOUS-SOURCE-GLB-RECEIPT/1",
            "rig_pose": "ride", "rig_time": 0.125,
            "model_source_sha256": "e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984",
            "GLB_sha256": sha, "part_parent_count": 5, "part_material_mesh_count": 16,
            "source_owned_pivots_validated_against_real_GLB": True,
            "authored_continuous_source_kinematics_recomputed": True,
            "1994_source_cadence_or_pose_paired": False,
            "1994_source_camera_or_rig_recovered": False,
            "owner_character_likeness_approved": False, "shipping_art_approved": False,
        }
        c = {
            "attempt_id": "abc", "source_sha256": q["model_source_sha256"],
            "rig_pose": "ride", "glb_sha256": sha,
            "glb_path": "attempts/abc/unicycle_articulated_blockout.glb",
        }
        last = {
            "attempt_id": "abc", "source_sha256": q["model_source_sha256"],
            "status": "succeeded", "current_output_usable": True,
            "glb_sha256": sha,
        }
        with self.assertRaises(ValueError):
            validate_sample_receipt(q, c, last, "0.125")  # old fixed-five mode
        self.assertEqual(validate_sample_receipt(q, c, last, "0.125", eighth.SHA),
                         c["glb_path"])
        q["GLB_sha256"] = PINNED_GRID_GLB_SHA["0.25"]
        with self.assertRaises(ValueError):
            validate_sample_receipt(q, c, last, "0.125", eighth.SHA)

    def test_verified_rom_sprite_source_is_explicitly_not_live_ppu_timing(self):
        document = {
            "source_kind": "deterministic_canonical_USA_ROM_registered_composition",
            "source_rom_verified_and_used_for_composition": True,
            "native_live_original_PPU_or_1994_3d_camera_independently_verified": False,
            "source_temporal_frame_observations": [{"window": "authored", "guest_frame": 1}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"authentic-source-corpus.json"
            payload = (json.dumps(document, sort_keys=True)+"\n").encode()
            path.write_bytes(payload)
            actual_sha = hashlib.sha256(payload).hexdigest()
            result = eighth.registered_source_time_evidence(path, actual_sha)
            self.assertTrue(result["original_64px_rasters_composed_from_sha_authenticated_original_rom"])
            self.assertTrue(result["source_frame_order_is_registry_authored"])
            self.assertFalse(result["original_live_emulator_ppu_frame_timing_independently_verified"])
            self.assertFalse(result["original_live_gameplay_hold_cadence_proven"])
            with self.assertRaises(ValueError):
                eighth.registered_source_time_evidence(path, "0"*64)
            for key, bad in (
                ("source_kind", "live_original_PP_U_verified"),
                ("source_rom_verified_and_used_for_composition", False),
                ("native_live_original_PPU_or_1994_3d_camera_independently_verified", True),
                ("source_temporal_frame_observations", None),
            ):
                altered = dict(document)
                altered[key] = bad
                raw = (json.dumps(altered, sort_keys=True)+"\n").encode()
                path.write_bytes(raw)
                with self.subTest(key=key), self.assertRaises(ValueError):
                    eighth.registered_source_time_evidence(
                        path, hashlib.sha256(raw).hexdigest())

    def test_wrapper_rejects_incomplete_grid_without_model_loading(self):
        with self.assertRaises(ValueError):
            eighth.compute(Path("not-used"), Path("not-used"),
                           {"0.125": Path("not-used")})

    def test_wrapper_rechecks_old_five_remains_stored_as_original(self):
        roots = {t: Path("untouched") for t in eighth.TIMES}
        source = {
            "source_original_corpus_sha256": "f"*64,
            "exact_ride_grid": list(eighth.TIMES),
            "first_last_authored_cycle_4x_pixel_xor": 0,
            "uniform_2026_phase_transition_diagnostics": [{} for _ in range(8)],
            "all_transition_pairs_predeclared_without_frame_matching": True,
            "original_1994_camera_or_pose_or_cadence_recovered": False,
            "shipping_art_approved": False,
        }
        with (patch.object(eighth, "evaluate", return_value=source) as fake,
              patch.object(eighth, "registered_source_time_evidence",
                           return_value={"source_frame_order_is_registry_authored": True})):
            out = eighth.compute(Path("original"), Path("camera"), roots)
        self.assertEqual(out["schema"], eighth.SCHEMA)
        self.assertEqual(out["actual_GLBS_from_existing_draft_exporter_run_id"], 41385793054)
        self.assertEqual(out["actual_distinct_3d_mesh_states_previously_independently_measured"], 7)
        fake.assert_called_once_with(Path("original"), roots, Path("camera"),
                                     sample_times=eighth.TIMES, pinned_glbs=eighth.SHA)
        self.assertEqual(LEGACY_TIMES, ("0.0", "0.25", "0.5", "0.75", "1.0"))

    def test_bad_cycle_closure_and_1994_acceptance_refused(self):
        roots = {t: Path("unused") for t in eighth.TIMES}
        for field, invalid in (("first_last_authored_cycle_4x_pixel_xor", 1),
                               ("original_1994_camera_or_pose_or_cadence_recovered", True),
                               ("shipping_art_approved", True)):
            payload = {
                "source_original_corpus_sha256": "f"*64,
            "exact_ride_grid": list(eighth.TIMES),
                "first_last_authored_cycle_4x_pixel_xor": 0,
                "uniform_2026_phase_transition_diagnostics": [{} for _ in range(8)],
                "all_transition_pairs_predeclared_without_frame_matching": True,
                "original_1994_camera_or_pose_or_cadence_recovered": False,
                "shipping_art_approved": False,
            }
            payload[field] = invalid
            with (self.subTest(field=field),
                  patch.object(eighth, "evaluate", return_value=payload),
                  patch.object(eighth, "registered_source_time_evidence",
                               return_value={"source_frame_order_is_registry_authored": True})):
                with self.assertRaises(ValueError):
                    eighth.compute(Path("unused"), Path("unused"), roots)


if __name__ == "__main__":
    unittest.main()
