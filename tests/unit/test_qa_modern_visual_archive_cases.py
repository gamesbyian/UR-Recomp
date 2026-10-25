#!/usr/bin/env python3
"""Archive consumer: injected verified report + synthetic retained ZIP."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from tests.unit.test_qa_modern_visual_case_checks import busy
from tests.unit.test_qa_modern_visual_diagnostics import (
    BAR, png, put, render_fit)
from tools import qa_modern_visual_archive_cases as ac


def frame_png(lw, out_w, out_h, focus=True):
    grid, h = busy(lw)
    if focus:
        put(grid, lw, 12, 60, 3, 16, BAR)
    f = render_fit(grid, lw, h, out_w, out_h)
    return png(f.width, f.height, [f.rgb(x, y) for y in range(f.height)
                                   for x in range(f.width)], ctype=6)


def capture(cid, route, pixels, data, witnessed):
    return {"id": cid, "pixels": pixels, "png_sha256": hashlib.sha256(data).hexdigest(),
            "native_semantic_route": route,
            "native_source_canvas_at_capture": [witnessed, 224],
            "exe_sha256": "a" * 64, "source_sha": "b" * 40}


class ArchiveCasesTest(unittest.TestCase):
    def make(self, tmp, items):
        zp = Path(tmp) / "native-ui.zip"
        with zipfile.ZipFile(zp, "w") as z:
            for cid, data in items.items():
                z.writestr(f"{cid}/actual-sdl-drawable.png", data)
        return zp

    def test_mapped_and_unmapped_captures(self):
        wide = frame_png(256, 1280, 720)
        compact = frame_png(256, 1024, 768)
        other = frame_png(342, 1280, 720, focus=False)
        with tempfile.TemporaryDirectory() as tmp:
            zp = self.make(tmp, {"visual-1280x720": wide, "visual-1024x768": compact,
                                 "records": other})
            verified = {"captures": [
                capture("visual-1280x720", "root-quit", [1280, 720], wide, 256),
                capture("visual-1024x768", "root-quit", [1024, 768], compact, 256),
                capture("records", "records-keyboard", [1280, 720], other, 342)]}
            rep = ac.analyse(zp, verified)
            self.assertTrue(rep["pass"], rep)
            byid = {c["capture"]: c for c in rep["captures"]}
            self.assertEqual(byid["visual-1280x720"]["case"], "root-wide-720")
            self.assertEqual(byid["visual-1024x768"]["case"], "root-43-768")
            self.assertIsNone(byid["records"]["case"])
            self.assertEqual([c["check"] for c in byid["records"]["checks"]],
                             ["witnessed-source-width"])
            self.assertEqual(rep["release_gate_credit"], 0)
            md = ac.markdown(rep)
            self.assertIn("root-wide-720", md)
            self.assertIn("witnessed-source-width=ok", md)

    def test_host_witnessed_width_disagreeing_with_pixels_fails(self):
        wide = frame_png(342, 1280, 720)
        with tempfile.TemporaryDirectory() as tmp:
            zp = self.make(tmp, {"v": wide})
            # the host claims a compact 256 source but the pixels are 342-wide
            verified = {"captures": [capture("v", "records-keyboard", [1280, 720],
                                             wide, 256)]}
            rep = ac.analyse(zp, verified)
            self.assertFalse(rep["pass"])

    def test_directory_mode_uses_receipt_and_detects_width(self):
        import json
        wide = frame_png(256, 1280, 720)
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "ur-modern-win32-visual-1280x720"
            good.mkdir()
            (good / "actual-sdl-drawable.png").write_bytes(wide)
            receipt = {"png_sha256": hashlib.sha256(wide).hexdigest(),
                       "actual_sdl_renderer_output": [1280, 720],
                       "native_semantic_route": "root-quit"}
            (good / "readback-receipt.json").write_text(json.dumps(receipt))
            rep = ac.analyse_dirs([good])
            self.assertTrue(rep["pass"], rep)
            # A legacy bar without the shared ring is advisory by default and
            # a failure when the ring is required.
            self.assertFalse(ac.analyse_dirs([good], require_ring=True)["pass"])
            self.assertEqual(rep["captures"][0]["case"], "root-wide-720")
            self.assertEqual(rep["release_gate_credit"], 0)
            self.assertIn("one-logical-width=ok(256)", ac.markdown(rep))
            receipt["png_sha256"] = "0" * 64
            (good / "readback-receipt.json").write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                ac.analyse_dirs([good])
            receipt.update(png_sha256=hashlib.sha256(wide).hexdigest(),
                           actual_sdl_renderer_output=[1024, 768])
            (good / "readback-receipt.json").write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                ac.analyse_dirs([good])
            self.assertEqual(ac.main(["--dir", str(good), "--artifact", "x.zip"]), 1)

    def test_other_matrix_root_sizes_map_to_their_cases(self):
        for pixels, case in (((1920, 1080), "root-wide-1080"),
                             ((3840, 2160), "root-wide-4k-virtual"),
                             ((640, 480), "root-43-480"),
                             ((1280, 720), "root-wide-720")):
            self.assertEqual(ac.ROUTE_CASE[("root-quit", pixels)], case)
        matrix = ac.cases.load_cases()
        for case in ("root-wide-1080", "root-wide-4k-virtual", "root-43-480"):
            self.assertIn(case, matrix)

    def test_hash_mismatch_and_missing_png_are_refused(self):
        wide = frame_png(256, 1280, 720)
        with tempfile.TemporaryDirectory() as tmp:
            zp = self.make(tmp, {"v": wide})
            bad = capture("v", "root-quit", [1280, 720], wide, 256)
            bad["png_sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                ac.analyse(zp, {"captures": [bad]})
            with self.assertRaises(ValueError):
                ac.analyse(zp, {"captures": [capture("missing", "root-quit",
                                                     [1280, 720], wide, 256)]})


    def test_verified_zip_binds_source_qualified_root_case(self):
        from unittest.mock import patch
        wide = frame_png(342, 1280, 720)
        with tempfile.TemporaryDirectory() as tmp:
            zp = self.make(tmp, {"native-title": wide})
            witness = capture("native-title", "root-quit", [1280, 720], wide, 342)
            source_sha = witness["source_sha"]
            candidate = dict(ac.cases.load_cases()["root-wide-720"],
                             id="source-qualified-native-title-root",
                             source_scene="native-title-root", source_sha=source_sha)
            route = ("root-quit", (1280, 720))
            with patch.dict(ac.ROUTE_CASE, {route: candidate["id"]}):
                passed = ac.analyse(zp, {"captures": [witness]},
                                    matrix={candidate["id"]: candidate})
                self.assertTrue(passed["pass"], passed)
                self.assertEqual(passed["release_gate_credit"], 0)
                identity = [c for c in passed["captures"][0]["checks"]
                            if c["check"] == "source-identity"]
                self.assertEqual(len(identity), 1)
                self.assertTrue(identity[0]["pass"])
                altered = dict(witness, source_sha="c" * 40)
                refused = ac.analyse(zp, {"captures": [altered]},
                                     matrix={candidate["id"]: candidate})
                self.assertFalse(refused["pass"])
                self.assertFalse(next(c for c in refused["captures"][0]["checks"]
                                      if c["check"] == "source-identity")["pass"])


if __name__ == "__main__":
    unittest.main()
