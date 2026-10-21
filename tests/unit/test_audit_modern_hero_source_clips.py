"""Fail-closed original-guest hero-clip inventory; no ROM or sprite assets needed."""
import copy
import json
import unittest

from tools.audit_modern_hero_source_clips import (
    CANONICAL_USA_SHA256, CANDIDATES, ClipAdmissionError, REGISTRY, SOURCE,
    build_report, inspect_clip,
)


class ModernHeroClipInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.source = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_actual_source_registration_has_three_distinct_bounded_clips(self):
        report = build_report(self.registry, self.source)
        self.assertEqual(report["canonical_rom_sha256"], CANONICAL_USA_SHA256)
        self.assertEqual([c["ticks_at_source_60hz"] for c in report["clips"]],
                         [8, 10, 9])
        self.assertEqual([c["clip_id"] for c in report["clips"]],
                         ["root-entry-reaction", "settle-and-recover",
                          "long-hold-recovery"])
        for clip in report["clips"]:
            start, stop = clip["source_guest_frames"]
            self.assertEqual(
                [r["original_guest_frame"] for r in clip["source_observed_original_p1"]],
                list(range(start, stop + 1)))
            self.assertEqual(
                [r["presentation_tick"] for r in clip["source_observed_original_p1"]],
                list(range(stop - start + 1)))
            self.assertEqual(sum(r["host_frames"] for r in
                                 clip["registered_composition_holds"]),
                             stop - start + 1)
            self.assertGreaterEqual(clip["distinct_registered_compositions"], 2)
            self.assertFalse(clip["may_reverse_or_loop"])
            self.assertFalse(clip["raster_bytes_verified_here"])
            self.assertFalse(clip["source_sprite_cadence_certified_in_native"])
            self.assertEqual(clip["native_visual_approval"], "pending")

    def test_source_sha_and_sequence_status_fail_closed(self):
        wrong_source = {**self.source, "rom_sha256": "0" * 64}
        with self.assertRaisesRegex(ClipAdmissionError, "canonical USA"):
            build_report(self.registry, wrong_source)
        changed = copy.deepcopy(self.registry)
        changed["motion_review_sequences"][
            "ordinary-race-1230-1239-entry-hold-exit"]["status"] = (
                "candidate awaiting independent original source review")
        with self.assertRaisesRegex(ClipAdmissionError, "not an accepted"):
            build_report(changed, self.source)

    def test_missing_duplicate_and_out_of_order_frames_rejected(self):
        for mutation in ("missing", "duplicate", "reverse"):
            changed = copy.deepcopy(self.registry)
            timeline = changed["motion_review_sequences"][
                "ordinary-race-1230-1239-entry-hold-exit"]["frames"]
            if mutation == "missing":
                del timeline[4]
            elif mutation == "duplicate":
                timeline[3]["frame"] = timeline[2]["frame"]
            else:
                timeline[4], timeline[5] = timeline[5], timeline[4]
            with self.subTest(mutation=mutation), self.assertRaisesRegex(
                    ClipAdmissionError, "missing, duplicated or reordered"):
                inspect_clip(changed, self.source, CANDIDATES[1])

    def test_original_p1_palette_and_semantic_composition_guards(self):
        rid = self.registry["motion_review_sequence"]["frames"][8][
            "p1_representation_id"]
        for mutation in ("wrong_player", "palette", "semantic", "duplicate_id"):
            changed = copy.deepcopy(self.registry)
            entry = next(x for x in changed["entries"]
                         if x["representation_id"] == rid)
            if mutation == "wrong_player":
                entry["player"] = "p2"
            elif mutation == "palette":
                entry["palette_asset_id"] = "0x07"
            elif mutation == "semantic":
                entry["composition_guards"]["p1_primary"] = "0x0001"
            else:
                changed["entries"].append(copy.deepcopy(entry))
            with self.subTest(mutation=mutation), self.assertRaises(ClipAdmissionError):
                inspect_clip(changed, self.source, CANDIDATES[0])

    def test_reject_unregistered_range_and_false_source_semantics(self):
        with self.assertRaisesRegex(ClipAdmissionError, "exceeds observed"):
            inspect_clip(self.registry, self.source,
                         ("invented", "motion_review_sequence", None, 1204, 1213))
        with self.assertRaisesRegex(ClipAdmissionError, "missing"):
            inspect_clip(self.registry, self.source,
                         ("future", "motion_review_sequences",
                          "not-a-real-source-clip", 1410, 1415))
        # The P1 primary code may stay constant while companion composition
        # changes. Source fidelity must preserve exact representation ID.
        clip = inspect_clip(self.registry, self.source, CANDIDATES[1])
        self.assertGreater(clip["distinct_registered_compositions"], 1)
        self.assertTrue(all("representation_id" in x for x in
                            clip["source_observed_original_p1"]))


if __name__ == "__main__":
    unittest.main()
