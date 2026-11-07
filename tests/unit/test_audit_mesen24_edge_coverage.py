"""Stdlib guards for independent original PPU 24-tick motion coverage auditor."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.art.audit_mesen24_edge_coverage import (
    analyze_witness, analyze_historical_artifact, iou,
    IDENTITIES, WITNESS_SHA256, WITNESS_GLB_SHA256, WITNESS_MEMBER,
    SHAPES, TICKS,
)
from tools.art.audit_mesen24_reconstruction_tradeoffs import (
    ARMS, HISTORICAL_SOURCE, ROLES,
)


def example():
    witness = {
        "schema": "UR-ART4K-ORIGINAL-24TICK-REAL-2026-SADDLE-LEAN-GENERALIZATION/1",
        "source_original_timeline_ticks": [1601, 1624],
        "source_each_player_has_all_24_consecutive_original_PPU_images": True,
        "original_1994_3D_mesh_camera_joint_or_source_materials_recovered": False,
        "owner_2026_character_art_likeness_approved": False,
        "current_successful_2026_16_material_GLB_sha256": WITNESS_GLB_SHA256,
    }
    for field, key in IDENTITIES.items():
        witness[field] = HISTORICAL_SOURCE[key]
    witness["original_source_per_role"] = {}
    for role in ROLES:
        frames = {}
        groups = {}
        for i, tick in enumerate(TICKS):
            # Same exact alpha source shape can repeat. 19 distinct P1,
            # 23 distinct P2; never count a duplicate as a new original shape.
            digest = hashlib.sha256(
                ("synthetic source " + role + " " +
                 str(i % SHAPES[role])).encode("utf-8")).hexdigest()
            frames[str(tick)] = {"source_2D_alpha_sha256": digest}
            groups.setdefault(digest, []).append(tick)
        arms = {}
        active_edge_index = 1 if role == "blue" else 4
        for arm in ARMS:
            edges = []
            for i, tick in enumerate(TICKS[:-1]):
                tp, fp, fn = (1, 1, 1) if i == active_edge_index else (0, 0, 2)
                edges.append({
                    "source_ticks": [tick, tick + 1],
                    "tp": tp, "fp": fp, "fn": fn,
                    "iou": iou(tp, fp, fn),
                })
            arms[arm] = {
                "original_chronological_source_frame_count": 24,
                "original_unique_64px_binary_shape_count": SHAPES[role],
                "source_actual_timeline_edge_count": 23,
                "per_original_chronological_edge": edges,
                "source_actual_23_consecutive_edge_change_tp_fp_fn":
                    {"tp": 1, "fp": 1, "fn": 45},
                "source_actual_23_consecutive_edge_change_pooled_iou":
                    iou(1, 1, 45),
            }
        witness["original_source_per_role"][role] = {
            "original_24_tick_samples": frames,
            "original_unique_binary_source_alpha_shape_sha256_to_ticks": groups,
            "arms": arms,
        }
    return witness


class OriginalEdgeCoverageTests(unittest.TestCase):
    def test_complete_48_source_samples_and_sparse_2026_predictions(self):
        report = analyze_witness(example())
        self.assertEqual(report["schema"], "UR-ART4K-AUTHENTIC-MESEN24-EDGE-COVERAGE/1")
        self.assertEqual(report["original_frames_per_player"], 24)
        self.assertEqual(report["original_edges_per_player"], 23)
        self.assertEqual(report["original_distinct_shapes"], {"blue": 19, "red": 23})
        self.assertFalse(report["orientation_only_controls_cover_all_source_edges"])
        self.assertFalse(report["previous_owner_selected_wider_pedal_model_tested"])
        self.assertFalse(report["original_1994_mechanics_recovered"])
        self.assertFalse(report["shipping_art_approved"])
        for role in ROLES:
            for arm in ARMS:
                e = report["roles_and_fixed_control_arms"][role][arm]
                self.assertEqual(e["original_nonempty_edges"], 23)
                self.assertEqual(e["predicted_nonempty_edges"], 1)
                self.assertEqual(e["original_changed_alpha_pixels"], 46)
                self.assertEqual(e["predicted_changed_alpha_pixels"], 2)
                self.assertEqual(e["matched_changed_alpha_pixels"], 1)
                self.assertEqual(e["false_positive_changed_alpha_pixels"], 1)
                self.assertEqual(e["unexplained_original_changed_alpha_pixels"], 45)
                self.assertEqual(e["pooled_changed_alpha_iou"], iou(1, 1, 45))
                self.assertEqual(
                    e["predicted_change_edge_ticks"],
                    [[1602, 1603]] if role == "blue" else [[1605, 1606]])

    def test_reject_missing_or_mutated_original_source_and_prediction_evidence(self):
        edits = (
            ("wrong source", lambda d: d.update(source_exact_original_USA_ROM_sha256="a"*64)),
            ("wrong model", lambda d: d.update(current_successful_2026_16_material_GLB_sha256="b"*64)),
            ("false approval", lambda d: d.update(owner_2026_character_art_likeness_approved=True)),
            ("missing player", lambda d: d["original_source_per_role"].pop("red")),
            ("missing tick", lambda d: d["original_source_per_role"]["red"]["original_24_tick_samples"].pop("1604")),
            ("wrong shape grouping", lambda d: d["original_source_per_role"]["blue"]["original_unique_binary_source_alpha_shape_sha256_to_ticks"].pop(next(iter(d["original_source_per_role"]["blue"]["original_unique_binary_source_alpha_shape_sha256_to_ticks"])))),
            ("missing arm", lambda d: d["original_source_per_role"]["blue"]["arms"].pop("axle_root_saddle_minus15")),
            ("missing edge", lambda d: d["original_source_per_role"]["red"]["arms"]["axle_root_saddle_plus15"]["per_original_chronological_edge"].pop()),
            ("bad sequence", lambda d: d["original_source_per_role"]["blue"]["arms"]["axle_root_saddle_neutral"]["per_original_chronological_edge"][0].update(source_ticks=[1602, 1604])),
            ("non-numeric pixel", lambda d: d["original_source_per_role"]["blue"]["arms"]["axle_root_saddle_plus15"]["per_original_chronological_edge"][0].update(tp=True)),
            ("invalid IoU", lambda d: d["original_source_per_role"]["red"]["arms"]["axle_root_saddle_plus15"]["per_original_chronological_edge"][4].update(iou=0.9)),
            ("wrong aggregate", lambda d: d["original_source_per_role"]["red"]["arms"]["axle_root_saddle_plus15"]["source_actual_23_consecutive_edge_change_tp_fp_fn"].update(fn=48)),
            ("tuned source", lambda d: d["original_source_per_role"]["blue"]["arms"]["axle_root_saddle_minus15"]["per_original_chronological_edge"][0].update(fn=1)),
        )
        for label, mutate in edits:
            data = example()
            mutate(data)
            with self.subTest(label=label), self.assertRaises(ValueError):
                analyze_witness(data)

    def test_actual_artifact_pin_blocks_arbitrary_zip_substitution(self):
        self.assertEqual(len(WITNESS_SHA256), 64)
        data = example()
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "fake.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr(WITNESS_MEMBER, json.dumps(data))
            with self.assertRaisesRegex(ValueError, "SHA differs"):
                analyze_historical_artifact(archive)


if __name__ == "__main__":
    unittest.main()
