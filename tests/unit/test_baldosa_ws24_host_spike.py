"""Fail-closed contracts for disposable +24 world-shadow Baldosa presenter."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    p = ROOT / "tools" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


adapter = load("baldosa_ws24_host_spike")
split_patch = load("baldosa_ws24_framework_split_patch")
oracle = load("baldosa_ws24_presentation_report")


class WorldMarginProbeTests(unittest.TestCase):
    def test_host_patch_is_fail_closed_and_idempotent(self):
        with self.assertRaises(ValueError):
            adapter.patch_main("static const SnesDesktopHostGame kGameHost = {};")
        s = (
            "static const SnesDesktopHostGame kGameHost = {\n"
            "    .after_run_frame     = &ur_baldosa_guest_snapshot_after_run_frame,\n"
            "    .begin_sim_frame    = &ur_baldosa_hd_begin_sim_frame,\n"
            "    .draw_frame         = &ur_baldosa_hd_draw_frame,\n"
            "    .presentation_scale = &ur_baldosa_hd_presentation_scale,\n"
            "};\n"
        )
        p = adapter.patch_main(s)
        self.assertEqual(adapter.patch_main(p), p)
        self.assertIn(".native_widescreen = 1", p)
        self.assertIn("&ur_baldosa_ws24_prepare_frame", p)
        self.assertIn("&ur_baldosa_ws24_draw_frame", p)
        self.assertIn(".compute_viewport  = &ur_baldosa_ws24_compute_viewport", p)
        self.assertIn("ur_baldosa_ws24_original_viewport(", p)

    def test_pinned_split_band_framework_patch_is_required(self):
        import hashlib
        import json
        manifest = json.loads(
            (ROOT / "tools/toolchain-entries/snesrecomp.json").read_text())
        pin = [row for row in manifest["patches"]
               if row["path"] == split_patch.PATCH]
        self.assertEqual(len(pin), 1)
        self.assertEqual(hashlib.sha256(
            (ROOT / split_patch.PATCH).read_bytes()).hexdigest(), pin[0]["sha256"])
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "missing required"):
                split_patch.apply(ROOT, Path(td))

    def test_cmake_reuses_existing_materializer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("tools/baldosa_native_ws24_presentation.cpp",
                         "native/title/uniracers_ws_margins.c",
                         "native/product/widescreen_output_composition.cpp"):
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("/* fixture */\n")
            with self.assertRaises(ValueError):
                adapter.patch_cmake("# No original bridge\n", root)
            out = adapter.patch_cmake("# UR_BALDOSA_NATIVE_RACER_PRESENTATION\n", root)
            self.assertEqual(adapter.patch_cmake(out, root), out)
            self.assertIn("uniracers_ws_margins.c", out)
            self.assertIn("widescreen_output_composition.cpp", out)
            self.assertIn('target_include_directories(UniracersSNESRecomp PRIVATE', out)

    def test_two_split_views_require_real_24_pixel_world_margins(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            before, after, log = (root / n for n in ("before", "after", "log"))
            crcs = ("abcd1234\n" * 2473).encode()
            before.write_bytes(crcs)
            after.write_bytes(crcs)
            log.write_text("".join(
                f"UR_BALDOSA_WS24_PREP frame={f} calibrated=1 "
                f"logical=304x224 margin=24\n"
                f"UR_BALDOSA_WS24_PRESENT frame={f} width=304 height=224 "
                f"pitch=1216 calibrated=1 saved=1\n"
                for f in (1810, 1870)))
            captures = root / "frames"
            captures.mkdir()
            for frame, value in ((1810, 80), (1870, 160)):
                raster = bytearray(304 * 224 * 4)
                for y in range(224):
                    for x in tuple(range(24)) + tuple(range(280, 304)):
                        offset = (y * 304 + x) * 4
                        raster[offset:offset + 4] = bytes((value, 20, 40, 255))
                (captures / f"ur-baldosa-ws24-{frame:06d}.pam").write_bytes(
                    oracle.HEADER + raster)
            result = oracle.assess(before, after, log, captures)
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["four_margin_image_frames"], 2)
            self.assertTrue(result["identical_guest_crc_sequence"])
            # A black 256-wide stock frame simply bordered to 304 fails.
            bad = captures / "ur-baldosa-ws24-001870.pam"
            bad.write_bytes(oracle.HEADER + bytes(304 * 224 * 4))
            self.assertEqual(oracle.assess(before, after, log, captures)["status"], "unproven")
            # A believable rendered image never excuses a guest CRC change.
            after.write_bytes(crcs.replace(b"abcd1234", b"abcd5678", 1))
            self.assertEqual(oracle.assess(before, after, log, captures)["status"], "unproven")


if __name__ == "__main__":
    unittest.main()
