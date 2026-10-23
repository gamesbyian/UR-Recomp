"""ROM-free negative and positive transport tests for incidental atlas intake."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import windows_visual_atlas as atlas
from tools import windows_visual_atlas_intake as intake
from tools.qa_modern_visual_pam_png import convert


class WindowsAtlasIntakeTests(unittest.TestCase):
    SOURCE = "a" * 40
    EXE = "b" * 64

    def sample(self, root: Path, *, include_witness: bool = True) -> Path:
        case = root / "producer-artifact" / "ur-modern-win32-visual-baseline"
        case.mkdir(parents=True)
        header = (b"P7\nWIDTH 1280\nHEIGHT 720\nDEPTH 4\n"
                  b"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")
        p7 = header + b"\x34\x51\x62\xff" * (1280 * 720)
        png = case / "actual-sdl-drawable.png"
        scratch = case / "synthetic-p7.tmp"
        scratch.write_bytes(p7)
        convert(scratch, png, (1280, 720))
        if include_witness:
            stage = case / "probe_first"
            stage.mkdir()
            (stage / "actual-sdl-drawable.pam").write_bytes(p7)
            log = ("UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 guest_frame=40 "
                   "output=1280x720 source=SDL_RenderReadPixels backend=sdl3\n")
            (stage / "native-process.log").write_text(log)
        else:
            log = "no source readback witness"
        receipt = {
            "schema_version": 1, "native_process_exit": 0,
            "source_sha": self.SOURCE, "exe_sha256": self.EXE,
            "native_semantic_route": "root-quit",
            "requested_window_size": [1280, 720],
            "actual_sdl_renderer_output": [1280, 720],
            "SDL_driver": "windows", "visual_approved": False,
            "hardware_approved": False, "authentic_isolation_approved": False,
            "release_gate_credit": 0,
            "png_sha256": atlas.sha256(png),
            "p7_sha256": hashlib.sha256(p7).hexdigest(),
            "native_process_log_sha256": hashlib.sha256(log.encode()).hexdigest(),
        }
        scratch.unlink()
        (case / "readback-receipt.json").write_text(json.dumps(receipt))
        return case

    def scan(self, root: Path, workflow="Modern visual QA native SDL baseline",
             run_head=SOURCE):
        return intake.discover(root / "artifact-root", root / "scan",
                               repo=root, main="f" * 40, workflow=workflow,
                               run_id=123, run_head=run_head)

    def test_reusable_image_requires_real_source_witness_and_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.sample(root / "artifact-root")
            with patch.object(intake, "code_state", return_value="integrated-current-visual"):
                result = self.scan(root)
            self.assertEqual(result["counts"]["eligible"], 1)
            record = root / "scan/approved/captures/URV-MD-001"
            self.assertTrue((record / "actual-sdl-drawable.png").is_file())
            approval = json.loads((record / "intake-approval.json").read_text())
            self.assertFalse(approval["independent_visual_approval"])
            self.assertEqual(approval["png_sha256"], atlas.sha256(record / "actual-sdl-drawable.png"))

    def test_no_p7_log_cannot_be_automatically_admitted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.sample(root / "artifact-root", include_witness=False)
            with patch.object(intake, "code_state", return_value="integrated-current-visual"):
                result = self.scan(root)
            self.assertEqual(result["counts"], {"eligible": 0, "review": 1})
            self.assertIn("P7", result["candidates"][0]["reason"])

    def test_unmerged_visual_source_is_review_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.sample(root / "artifact-root")
            with patch.object(intake, "code_state", return_value="integrated-changed-visual"):
                result = self.scan(root)
            self.assertEqual(result["counts"]["eligible"], 0)
            self.assertIn("not current", result["candidates"][0]["reason"])

    def test_unknown_producer_and_different_source_are_review_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.sample(root / "artifact-root")
            with patch.object(intake, "code_state", return_value="integrated-current-visual"):
                result = self.scan(root, workflow="third-party experiment")
            self.assertEqual(result["counts"]["eligible"], 0)
            self.assertIn("unrecognized", result["candidates"][0]["reason"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.sample(root / "artifact-root")
            with patch.object(intake, "code_state", return_value="integrated-current-visual"):
                result = self.scan(root, run_head="c" * 40)
            self.assertEqual(result["counts"]["eligible"], 0)
            self.assertIn("differs", result["candidates"][0]["reason"])

    def test_original_genuine_capture_validator_refuses_route_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            case = self.sample(root / "artifact-root")
            receipt = case / "readback-receipt.json"
            data = json.loads(receipt.read_text())
            data["native_semantic_route"] = "authentic-stock"
            receipt.write_text(json.dumps(data))
            with patch.object(intake, "code_state", return_value="integrated-current-visual"):
                result = self.scan(root)
            self.assertEqual(result["counts"]["eligible"], 0)
            self.assertIn("mapping", result["candidates"][0]["reason"])

    def test_code_state_fail_closed_without_git_objects(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(intake.code_state(self.SOURCE, Path(temp), "f"*40), "unknown")


if __name__ == "__main__":
    unittest.main()
