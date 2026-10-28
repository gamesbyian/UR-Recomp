"""ROM-free three-real-file byte contract for MENU-10 final SDL captures.

Synthetic P7 data here proves only verifier integrity, not original gameplay.
"""
from pathlib import Path
import json
import tempfile
import unittest

from tools import qa_modern_attract_final_sdl_pair as witness

SOURCE = "a" * 40
PE = "b" * 64
HEADER = (b"P7\nWIDTH 1280\nHEIGHT 720\nDEPTH 4\n"
          b"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")


class StockAttractSDLPairTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.records = {}
        self.write_all()

    def write_all(self):
        # Alpha zero is intentional: compare *observed RGB* rather than
        # guess Windows renderer/display alpha semantics.
        pixels = [
            ("stock-attract-before", bytes([30, 60, 90, 0])),
            ("stock-attract-after", bytes([35, 60, 90, 0])),
            ("stock-attract-woken", bytes([60, 90, 30, 0])),
        ]
        for i, (name, sample) in enumerate(pixels):
            case = self.root / name
            if not case.exists():
                (case / "probe_first").mkdir(parents=True)
            frame = witness.FRAMES[name]
            event = ("UR_MODERN_VISUAL_SDL_CAPTURE status=saved "
                     f"draw={1500+i} guest_frame={frame} output=1280x720 "
                     "source=SDL_RenderReadPixels backend=sdl3")
            log = ("UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=943\n"
                   "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=main_menu frame=440 menu=d7 race=00 overlay_title=1\n"
                   "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=attract_title frame=943 menu=84 race=00 overlay_title=1\n"
                   "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=demo_race frame=1532 menu=84 race=01 overlay_title=0\n"
                   "UR_MODERN_TITLE_STOCK_ATTRACT p1_wake_consumed=1 frame=1600\n"
                   "UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600\n"
                   + event + "\n").encode()
            p7 = HEADER + sample * (1280 * 720)
            (case / "probe_first" / "native-process.log").write_bytes(log)
            (case / "probe_first" / "actual-sdl-drawable.pam").write_bytes(p7)
            receipt = {
                "source_sha": SOURCE, "native_semantic_route": name,
                "observed_guest_frame": frame, "observed_in_draw": 1500+i,
                "native_process_exit": 0, "execution_mode": "modern",
                "release_gate_credit": 0, "visual_approved": False,
                "hardware_approved": False, "actual_sdl_renderer_output": [1280, 720],
                "exe_sha256": PE, "SDL_driver": "windows",
                "native_process_log_sha256": witness.digest(log),
                "p7_sha256": witness.digest(p7),
            }
            self.records[name] = receipt
            (case / "readback-receipt.json").write_text(json.dumps(receipt))

    def test_synthetic_complete_triplet_is_only_diagnostic(self):
        result = witness.score(self.root, SOURCE)
        self.assertEqual(result["actual_sdl_guest_frames"], witness.FRAMES)
        self.assertEqual(result["source_sha"], SOURCE)
        self.assertEqual(result["exe_sha256"], PE)
        self.assertEqual(result["actual_sdl_original_demo_rgb_differing_pixels"], 1280*720)
        self.assertEqual(result["actual_sdl_wake_rgb_differing_pixels"], 1280*720)
        self.assertFalse(result["menu10_independent_criterion_admitted"])
        self.assertFalse(result["physical_hardware_verified"])
        self.assertEqual(result["first_usa_event_credit"], 0)
        self.assertEqual(result["release_gate_credit"], 0)

    def test_exact_windows_crlf_logs_preserve_hashes_and_parse_markers(self):
        # Actual Windows artifacts had CRLF, while synthetic POSIX logs
        # used LF. Parse normalized text only AFTER hashing original bytes.
        for name in witness.FRAMES:
            path = self.root / name / "probe_first" / "native-process.log"
            raw = path.read_bytes().replace(b"\n", b"\r\n")
            path.write_bytes(raw)
            receipt = dict(self.records[name],
                           native_process_log_sha256=witness.digest(raw))
            (self.root / name / "readback-receipt.json").write_text(
                json.dumps(receipt))
        accepted = witness.score(self.root, SOURCE)
        self.assertGreater(accepted["actual_sdl_original_demo_rgb_differing_pixels"], 0)
        self.assertFalse(accepted["menu10_independent_criterion_admitted"])

    def test_tampered_raw_pixel_bytes_and_mixed_pe_fail(self):
        p = self.root / "stock-attract-after" / "probe_first" / "actual-sdl-drawable.pam"
        p.write_bytes(p.read_bytes() + b"X")
        with self.assertRaisesRegex(ValueError, "SHA"):
            witness.score(self.root, SOURCE)
        self.write_all()
        d = dict(self.records["stock-attract-woken"], exe_sha256="c"*64)
        (self.root / "stock-attract-woken" / "readback-receipt.json").write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, "same|exact"):
            witness.score(self.root, SOURCE)

    def test_false_guest_frame_and_missing_readback_rejected(self):
        p = self.root / "stock-attract-before" / "readback-receipt.json"
        d = dict(self.records["stock-attract-before"], observed_guest_frame=1584)
        p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, "scope"):
            witness.score(self.root, SOURCE)
        self.write_all()
        p = self.root / "stock-attract-before" / "probe_first" / "actual-sdl-drawable.pam"
        p.unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            witness.score(self.root, SOURCE)

    def test_source_lifecycle_must_be_real_and_ordered(self):
        # A frame-labelled SDL screenshot does not prove original state.
        log_path = (self.root / "stock-attract-before" / "probe_first" /
                    "native-process.log")
        raw = log_path.read_bytes()
        changed = raw.replace(b"phase=attract_title frame=943",
                              b"phase=attract_title frame=942")
        log_path.write_bytes(changed)
        receipt = dict(self.records["stock-attract-before"],
                       native_process_log_sha256=witness.digest(changed))
        (self.root / "stock-attract-before" / "readback-receipt.json").write_text(
            json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            witness.score(self.root, SOURCE)

    def test_two_matching_sdl_demonstrations_fail_no_motion(self):
        p = self.root / "stock-attract-after" / "probe_first" / "actual-sdl-drawable.pam"
        before = self.root / "stock-attract-before" / "probe_first" / "actual-sdl-drawable.pam"
        p.write_bytes(before.read_bytes())
        d = dict(self.records["stock-attract-after"], p7_sha256=witness.digest(p.read_bytes()))
        (self.root / "stock-attract-after" / "readback-receipt.json").write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, "did not move"):
            witness.score(self.root, SOURCE)


if __name__ == "__main__":
    unittest.main()
