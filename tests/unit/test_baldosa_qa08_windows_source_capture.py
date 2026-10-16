"""QA-08 read-only Windows PPU capture: source guards and adversarial receipts."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_qa08_windows_source_capture_patch as stage  # noqa: E402
import check_qa08_windows_source_raster as check  # noqa: E402

MAIN = (
    "/* UR_BALDOSA_NATIVE_PRODUCT_PAUSE */\n"
    "static const SnesDesktopHostGame kGameHost = {\n"
    "    .after_run_frame     = &ur_baldosa_product_after_run_frame,\n"
    "};\n"
)
CMAKE = (
    "# UR_BALDOSA_NATIVE_PRODUCT_PAUSE\n"
    "target_sources(UniracersSNESRecomp PRIVATE \"pause.cpp\")\n"
)


class SourceHookTest(unittest.TestCase):
    def test_observer_only_uses_existing_end_sim_frame_and_is_idempotent(self):
        out = stage.patch_game_main(MAIN)
        self.assertEqual(stage.patch_game_main(out), out)
        self.assertIn("    .end_sim_frame      = &ur_qa08_windows_capture_original_source,\n", out)
        self.assertIn(stage.STATS_ANCHOR, out)
        self.assertNotIn(".draw_frame", out)
        self.assertNotIn(".before_run_frame", out)
        self.assertEqual(out.count(stage.MARK), 1)

    def test_no_guest_or_modern_abi_drift_is_accepted(self):
        for bad in (
            "", MAIN.replace("UR_BALDOSA_NATIVE_PRODUCT_PAUSE", "unrelated"),
            MAIN.replace(stage.STATS_ANCHOR, ""), MAIN + MAIN,
            MAIN.replace("kGameHost", "other"),
            MAIN.replace(stage.STATS_ANCHOR, stage.STATS_ANCHOR +
                         "    .end_sim_frame = &other_compositor;\n"),
        ):
            with self.subTest(bad=bad[:60]), self.assertRaises(ValueError):
                stage.patch_game_main(bad)
        broken = stage.patch_game_main(MAIN).replace(
            ".end_sim_frame      =", ".draw_frame         =")
        with self.assertRaises(ValueError):
            stage.patch_game_main(broken)

    def test_cmake_wires_only_read_only_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / stage.SOURCE
            path.parent.mkdir(parents=True)
            path.write_text("// real source exists", encoding="utf-8")
            out = stage.patch_game_cmake(CMAKE, root)
            self.assertEqual(stage.patch_game_cmake(out, root), out)
            self.assertIn("target_sources(UniracersSNESRecomp PRIVATE", out)
            self.assertEqual(out.count(stage.MARK), 1)
            with self.assertRaises(ValueError):
                stage.patch_game_cmake(CMAKE.replace(
                    "UR_BALDOSA_NATIVE_PRODUCT_PAUSE", "OTHER"), root)

    def test_atomic_plan_does_not_write_if_cmake_is_wrong(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game"
            (game / "src").mkdir(parents=True)
            (root / stage.SOURCE).parent.mkdir(parents=True, exist_ok=True)
            (root / stage.SOURCE).write_text("x", encoding="utf-8")
            (game / "src/main.c").write_text(MAIN, encoding="utf-8")
            (game / "CMakeLists.txt").write_text("wrong", encoding="utf-8")
            with self.assertRaises(ValueError):
                stage.plan(game, root)
            self.assertEqual((game / "src/main.c").read_text(), MAIN)


class SourcePixelTest(unittest.TestCase):
    def setUp(self):
        self.crcs = ["0x00000000"] * 2473
        self.blob = check.HEADER + b"\x00\x00\x00\xff" * (256 * 224)
        self.digest = hashlib.sha256(self.blob).hexdigest()
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def save(self, frame=2208, blob=None):
        (self.folder / f"ur-baldosa-original-source-{frame:06d}.pam").write_bytes(
            self.blob if blob is None else blob)

    def log(self, frame=2208):
        return (f"UR_QA08_WINDOWS_ORIGINAL_SOURCE frame={frame} "
                "logical=256x224 saved=1 "
                "source=post-original-ppu-before-present\n")

    def test_exact_actual_source_passes_when_independent_digest_matches(self):
        self.save()
        with patch.dict(check.EXPECTED, {2208: self.digest}):
            result = check.inspect(self.folder, self.log(), self.crcs)
        self.assertEqual(result["actual_frames_observed"], [2208])
        self.assertTrue(result["source_callback_2208_match_to_independent_original"])
        self.assertFalse(result["observed_moving_postGO_frames_all_exact"])
        self.assertFalse(result["all_four_countdown_and_moving_2P_original_source_exact"])
        self.assertFalse(result["release_graphics_gate_approved"])

    def test_full_source_guard_demands_all_four_real_original_windows_scene_hashes(self):
        self.assertEqual(check.FRAMES, (1856, 2192, 2208, 2224))
        self.assertEqual(set(check.EXPECTED), set(check.FRAMES))
        self.assertEqual(set(check.STOCK), set(check.FRAMES))
        for f in check.FRAMES:
            self.save(frame=f)
        log = "".join(self.log(frame=f) for f in check.FRAMES)
        # Synthetic same-byte inputs exercise strict coverage; these are not
        # presented as actual original source pixel approvals.
        with patch.dict(check.EXPECTED, {f: self.digest for f in check.FRAMES}):
            good = check.inspect(self.folder, log, self.crcs)
            self.assertTrue(good["all_four_countdown_and_moving_2P_original_source_exact"])
            self.assertTrue(good["observed_moving_postGO_frames_all_exact"])
            self.assertFalse(good["release_graphics_gate_approved"])
            # A missing countdown may not borrow the existing 2208 witness.
            (self.folder / "ur-baldosa-original-source-001856.pam").unlink()
            missing = check.inspect(self.folder, log.replace(self.log(1856), ""), self.crcs)
            self.assertFalse(missing["all_four_countdown_and_moving_2P_original_source_exact"])
            self.save(frame=1856)
            # No tolerance for a single altered pixel anywhere in 57,344.
            changed = bytearray(self.blob)
            changed[-4] ^= 1
            self.save(frame=2224, blob=bytes(changed))
            changed_result = check.inspect(self.folder, log, self.crcs)
            self.assertFalse(changed_result["all_four_countdown_and_moving_2P_original_source_exact"])

    def test_wrong_or_missing_raster_not_accepted(self):
        for b in [self.blob[:-1], self.blob.replace(b"WIDTH 256", b"WIDTH 216", 1)]:
            self.save(blob=b)
            with self.assertRaises(ValueError):
                check.inspect(self.folder, self.log(), self.crcs)
        (self.folder / "ur-baldosa-original-source-002208.pam").unlink()
        no_frame = check.inspect(self.folder, "", self.crcs)
        self.assertFalse(no_frame["source_callback_2208_observed"])
        self.assertFalse(no_frame["source_callback_2208_match_to_independent_original"])

    def test_negative_duplicates_source_drift_guest_crc_and_unsolicited_frame(self):
        self.save()
        for log, crc in [
            (self.log() * 2, self.crcs),
            (self.log() + "UR_QA08_WINDOWS_SOURCE_REJECT frame=2208\n", self.crcs),
            (self.log(), self.crcs[:-1]),
            (self.log(), ["broken"] * 2473),
        ]:
            with self.assertRaises(ValueError):
                check.inspect(self.folder, log, crc)
        self.save(700)
        with self.assertRaises(ValueError):
            check.inspect(self.folder, self.log(), self.crcs)

    def test_unchanged_legacy_stock_is_diagnostic_not_parity(self):
        self.save()
        with patch.dict(check.STOCK, {2208: self.digest}):
            result = check.inspect(self.folder, self.log(), self.crcs)
        self.assertFalse(result["source_callback_2208_match_to_independent_original"])
        self.assertTrue(result["source_sha_controls"][0][
            "matches_old_wrong_pinned_native_raster"])

    def test_windows_bridge_wires_observer_only_for_disposable_guest(self):
        wf = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertEqual(wf.count(
            "python tools/baldosa_qa08_windows_source_capture_patch.py --game baldosa "
            '--ur-root "$GITHUB_WORKSPACE" --apply-candidate'), 1)
        self.assertEqual(wf.count(
            "python tests/unit/test_baldosa_qa08_windows_source_capture.py"), 1)
        self.assertLess(wf.index("python tools/baldosa_product_pause_spike.py"),
                        wf.index("python tools/baldosa_qa08_windows_source_capture_patch.py"))
        self.assertLess(wf.index("python tools/baldosa_qa08_windows_source_capture_patch.py"),
                        wf.index("cmake -S baldosa -B baldosa/build-ur-win"))


if __name__ == "__main__":
    unittest.main()
