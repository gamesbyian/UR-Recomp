"""ROM-free controls for the archived Windows title-plate cross-aspect witness.

Synthetic 4:3 and 16:9 captures exercise the *whole* receipt/P7/PNG/log
path. A genuine Windows artifact may optionally be replayed by setting
UR_TITLE_WINDOWS_ARTIFACT; it is never included in the repository or test ZIP.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

try:
    import numpy as np
    from PIL import Image
except ImportError:
    np = None
    Image = None

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
if np is not None and Image is not None:
    import verify_title_plate_artifact as witness


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


@unittest.skipUnless(np is not None and Image is not None,
                     "optional NumPy/Pillow graphics research dependencies")
class TitlePlatePortableTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "title.zip"
        self.members = self.synthetic_members()
        self.write_archive()

    @staticmethod
    def synthetic_members():
        members = {"synthetic-metadata.json": b"{}", "synthetic-readme.txt": b"ROM-free fixture"}
        # The plate is the same source artwork across 256 and 342 logical
        # widths. Every other pixel is invented fixture data, never game art.
        yy, xx = np.indices((81, 238), dtype=np.uint16)
        plate = np.stack(((xx * 19 + yy * 11) % 256,
                          (xx * 37 + yy * 13) % 256,
                          (xx * 7 + yy * 29) % 256,
                          np.full_like(xx, 255)), axis=-1).astype(np.uint8)
        for res, (width, height, source_width, art_x) in witness.SIZES.items():
            for case in witness.CASES:
                root = case.endswith("entered-root")
                reduced = case.startswith("title-reduced-")
                src = np.zeros((224, source_width, 4), dtype=np.uint8)
                src[:, :, 3] = 255
                if root:
                    src[12:202, 8:-8, :3] = (19, 83, 177)
                else:
                    src[27:108, art_x:art_x + 238] = plate
                    src[200:205, 20:80, :3] = (211, 0, 0) if reduced else (0, 211, 0)
                x_index = np.minimum(source_width - 1,
                    np.floor((np.arange(width) + .5) * source_width / width).astype(int))
                y_index = np.minimum(223,
                    np.floor((np.arange(height) + .5) * 224 / height).astype(int))
                rgba = src[y_index[:, None], x_index[None, :]]
                p7 = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\nMAXVAL 255\n"
                      "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode() + rgba.tobytes()
                out = io.BytesIO()
                Image.fromarray(rgba, "RGBA").save(out, format="PNG")
                png = out.getvalue()
                draw = 100 if root else 40
                log = (f"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw={draw} "
                       f"guest_frame={draw} output={width}x{height} "
                       "source=SDL_RenderReadPixels backend=sdl3\n")
                if root:
                    log += ("UR_BALDOSA_MODERN_TITLE entered_root=1 "
                            f"frame={'60' if reduced else '74'} input_owned=1\n"
                            "UR_BALDOSA_MODERN_DESTINATION stage=root "
                            f"raster={source_width}x224\n")
                else:
                    log += ("UR_BALDOSA_MODERN_TITLE painted=1 "
                            f"raster={source_width}x224 host=modern\n")
                log = log.encode()
                receipt = {
                    "source_sha": witness.SOURCE,
                    "exe_sha256": witness.EXE,
                    "native_semantic_route": case,
                    "native_process_exit": 0,
                    "execution_mode": "modern",
                    "SDL_driver": "windows",
                    "actual_sdl_renderer_output": [width, height],
                    "requested_window_size": [width, height],
                    "visual_approved": False,
                    "release_gate_credit": 0,
                    "observed_in_draw": draw,
                    "p7_sha256": sha(p7),
                    "png_sha256": sha(png),
                    "native_process_log_sha256": sha(log),
                }
                prefix = f"ur-modern-title-final-sdl-{res}/{case}/"
                members[prefix + "readback-receipt.json"] = json.dumps(receipt).encode()
                members[prefix + "probe_first/actual-sdl-drawable.pam"] = p7
                members[prefix + "actual-sdl-drawable.png"] = png
                members[prefix + "probe_first/native-process.log"] = log
        assert len(members) == 34
        return members

    def write_archive(self):
        with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, payload in self.members.items():
                z.writestr(name, payload)
        self.addCleanup(lambda: None)
        self.original_hash = witness.ARTIFACT_SHA256
        witness.ARTIFACT_SHA256 = sha(self.path.read_bytes())
        self.addCleanup(setattr, witness, "ARTIFACT_SHA256", self.original_hash)

    def mutate(self, res, case, member, edit):
        prefix = f"ur-modern-title-final-sdl-{res}/{case}/"
        path = prefix + member
        self.members[path] = edit(self.members[path])
        if member.endswith(".pam"):
            key = "p7_sha256"
        elif member.endswith(".png"):
            key = "png_sha256"
        else:
            key = "native_process_log_sha256"
        receipt_path = prefix + "readback-receipt.json"
        receipt = json.loads(self.members[receipt_path])
        receipt[key] = sha(self.members[path])
        self.members[receipt_path] = json.dumps(receipt).encode()
        self.write_archive()

    def test_synthetic_positive_exact_cross_aspect(self):
        result = witness.verify(self.path)
        self.assertEqual(result["actual_windows_cases_checked"], 8)
        self.assertEqual(result["native_P7_png_exact_cases"], 8)
        self.assertEqual(result["cross_aspect_title_plate"]["title-still"]["exact_rgba_pixels"], 19278)
        self.assertEqual(len(set(v["plate_sha256"] for v in result["cross_aspect_title_plate"].values())), 1)

    def test_rehashed_native_p7_disagrees_with_png(self):
        self.mutate("1280x720", "title-still", "probe_first/actual-sdl-drawable.pam",
                    lambda b: b[:-4] + bytes([b[-4] ^ 1]) + b[-3:])
        with self.assertRaisesRegex(ValueError, "PNG differs from actual native SDL P7"):
            witness.verify(self.path)

    def test_rehashed_fake_native_event(self):
        self.mutate("1024x768", "title-still", "probe_first/native-process.log",
                    lambda b: b.replace(b"UR_BALDOSA_MODERN_TITLE painted=1",
                                        b"FAKE_UR_BALDOSA_MODERN_TITLE painted=1"))
        with self.assertRaisesRegex(ValueError, "missing/ambiguous native event"):
            witness.verify(self.path)

    def test_rehashed_cross_aspect_plate_difference(self):
        prefix = "ur-modern-title-final-sdl-1280x720/title-still/"
        pn = prefix + "probe_first/actual-sdl-drawable.pam"
        gn = prefix + "actual-sdl-drawable.png"
        p7 = bytearray(self.members[pn])
        offset = p7.index(b"ENDHDR\n") + len(b"ENDHDR\n")
        x = int((52 + 3 + .5) * 1280 / 342)
        y = int((27 + 5 + .5) * 720 / 224)
        pos = offset + (y * 1280 + x) * 4
        p7[pos] ^= 1
        self.members[pn] = bytes(p7)
        with Image.open(io.BytesIO(self.members[gn])) as im:
            image = im.copy()
            image.putpixel((x, y), tuple(p7[pos:pos + 4]))
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            self.members[gn] = buf.getvalue()
        rn = prefix + "readback-receipt.json"
        receipt = json.loads(self.members[rn])
        receipt["p7_sha256"] = sha(self.members[pn])
        receipt["png_sha256"] = sha(self.members[gn])
        self.members[rn] = json.dumps(receipt).encode()
        self.write_archive()
        with self.assertRaisesRegex(ValueError, "actual 4:3/16:9 retail plate pixels differ"):
            witness.verify(self.path)

    def test_wrong_executable_refused(self):
        prefix = "ur-modern-title-final-sdl-1280x720/title-still/"
        rn = prefix + "readback-receipt.json"
        receipt = json.loads(self.members[rn])
        receipt["exe_sha256"] = "0" * 64
        self.members[rn] = json.dumps(receipt).encode()
        self.write_archive()
        with self.assertRaisesRegex(ValueError, "receipt source/stage/approval mismatch"):
            witness.verify(self.path)

    def test_duplicate_native_field_refused(self):
        self.mutate("1024x768", "title-still", "probe_first/native-process.log",
                    lambda b: b.replace(b"painted=1", b"painted=1 painted=1"))
        with self.assertRaisesRegex(ValueError, "malformed/duplicate native event field"):
            witness.verify(self.path)


@unittest.skipUnless(np is not None and Image is not None,
                     "optional NumPy/Pillow graphics research dependencies")
class TitlePlateOriginalOptionalTests(unittest.TestCase):
    def test_original_windows_artifact_if_available(self):
        artifact = os.environ.get("UR_TITLE_WINDOWS_ARTIFACT")
        if not artifact:
            self.skipTest("original Windows artifact not supplied; no release evidence inferred")
        result = witness.verify(Path(artifact))
        self.assertEqual(result["actual_windows_cases_checked"], 8)


if __name__ == "__main__":
    unittest.main()
