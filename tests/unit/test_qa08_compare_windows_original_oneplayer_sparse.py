"""Read-only QA-08 original/native 1P whole-route sparse-frame comparator contracts."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_compare_windows_original_oneplayer_sparse as sparse  # noqa: E402


class SparseSourceRasterTest(unittest.TestCase):
    def test_only_256x224_source_p7_with_exact_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"pixel.pam"
            original=sparse.HEADER+b"\x00\x00\x00\xff"*(256*224)
            path.write_bytes(original)
            result=sparse.source_rgb_from_pam(path,hashlib.sha256(original).hexdigest())
            self.assertEqual(len(result),256*224*4)
            self.assertEqual(result[:4],b"\x00\x00\x00\xff")
            for bad in (original[:-1],original.replace(b"HEIGHT 224",b"HEIGHT 216",1)):
                path.write_bytes(bad)
                with self.assertRaises(ValueError):
                    sparse.source_rgb_from_pam(path,hashlib.sha256(original).hexdigest())
                with self.assertRaises(ValueError):
                    sparse.source_rgb_from_pam(path,hashlib.sha256(bad).hexdigest())

    def test_original_manifest_must_be_exact_authenticated_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            orig=root/"original"
            win=root/"windows"
            orig.mkdir()
            win.mkdir()
            (orig/"qa08-original-1p-sparse.json").write_text(json.dumps({
                "schema":"fabricated", "USA_ROM_sha256":sparse.ROM_SHA}))
            (win/"qa08-windows-original-oneplayer-coverage.json").write_text("{}")
            route=root/"script.txt"
            route.write_text("turbo on\n")
            with self.assertRaisesRegex(ValueError,"unqualified original"):
                sparse.analyze(orig,win,route)

    def test_frame_contract_never_uses_cropped_or_nearest_frame(self):
        self.assertEqual((sparse.FIRST,sparse.LAST,sparse.STEP),(1280,5440,16))
        self.assertEqual(sparse.PX,57344)
        contents=(ROOT/"tools/qa08_compare_windows_original_oneplayer_sparse.py").read_text()
        self.assertIn("source_refs[frame-1]",contents)
        self.assertIn("compare(original_source,native)",contents)
        self.assertNotIn("resize(",contents)
        self.assertNotIn("nearest(",contents)
        self.assertNotIn("shifted",contents.lower().split("def analyze",1)[1])


if __name__=="__main__":
    unittest.main()
