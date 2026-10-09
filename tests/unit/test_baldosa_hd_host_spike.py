"""Unit contracts for the isolated Baldosa moving-racer host experiment."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


patch = load("baldosa_hd_host_spike", "tools/baldosa_hd_host_spike.py")
report = load("baldosa_hd_presentation_report", "tools/baldosa_hd_presentation_report.py")


class NativeRacerHostTest(unittest.TestCase):
    def test_fail_closed_and_idempotent(self):
        with self.assertRaises(ValueError):
            patch.patch_main("static const SnesDesktopHostGame kGameHost = {};")
        source = (
            "static const SnesDesktopHostGame kGameHost = {\n"
            "    .after_run_frame     = &ur_baldosa_guest_snapshot_after_run_frame,\n"
            "};\n"
        )
        candidate = patch.patch_main(source)
        self.assertEqual(patch.patch_main(candidate), candidate)
        self.assertIn(".begin_sim_frame", candidate)
        self.assertIn(".draw_frame", candidate)

    def test_only_first_party_presenter_is_linked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for filename in (
                "tools/baldosa_native_racer_presentation.cpp",
                "native/presentation/racer_hd_presenter.cpp",
                "native/presentation/racer_oam_placement.cpp",
            ):
                path = root / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("// test")
            with self.assertRaises(ValueError):
                patch.patch_cmake("add_executable(UniracersSNESRecomp)", root)
            candidate = patch.patch_cmake(
                "# UR_BALDOSA_GUEST_SNAPSHOT_BRIDGE\n", root)
            self.assertEqual(patch.patch_cmake(candidate, root), candidate)
            self.assertIn("racer_hd_presenter.cpp", candidate)

    def test_requires_distinct_presented_rasters_and_same_guest_crc(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base, candidate, log = [root / n for n in ("before", "after", "log")]
            frames = ("0xAAAA0000\n" * 2473).encode()
            base.write_bytes(frames)
            candidate.write_bytes(frames)
            log.write_text("".join(
                f"UR_BALDOSA_NATIVE_COMPOSE frame={f} racer_present=1 "
                f"logical=256x224 source_art=ur hd_capture=1\n"
                for f in (1800, 1860)))
            captures = root / "captures"
            captures.mkdir()
            header = (b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
                      b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
            for f, pixel in ((1800, b"\x10"), (1860, b"\x20")):
                (captures / f"ur-baldosa-frame-{f:06d}.pam").write_bytes(
                    header + pixel * (256 * 224 * 4))
            self.assertEqual(report.assess(base, candidate, log, captures)["status"], "passed")
            candidate.write_bytes(frames.replace(b"0xAAAA0000", b"0xBBBB0000", 1))
            self.assertEqual(report.assess(base, candidate, log, captures)["status"], "unproven")


if __name__ == "__main__":
    unittest.main()
