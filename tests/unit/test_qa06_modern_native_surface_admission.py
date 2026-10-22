"""ROM-free H26 Modern root geometry regression, distinct from gameplay PAR."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

HAS_PIL = importlib.util.find_spec("PIL") is not None
if HAS_PIL:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
    from qa06_modern_native_surface_admission import (
        _roi, _sample_index, verify_capture, SOURCE_SHA, PE_SHA256)


@unittest.skipUnless(HAS_PIL, "Pillow unavailable for Modern capture audit")
class ModernNativeSurfaceAdmissionTests(unittest.TestCase):
    def test_observed_compact_4by3_uses_entire_drawable(self):
        self.assertEqual(_roi(1024, 768), (0, 0, 1024, 768))

    def test_observed_wide_16by9_keeps_side_mattes(self):
        self.assertEqual(_roi(1280, 720), (160, 0, 960, 720))

    def test_unobserved_resolution_is_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError, "unqualified"):
            _roi(1920, 1080)

    def test_source_epoch_and_process_receipts_fail_before_image_read(self):
        base={"actual_sdl_renderer_output":[1024,768],
              "source_sha":SOURCE_SHA,"exe_sha256":PE_SHA256,
              "native_process_exit":0,"observed_in_draw":40,
              "native_semantic_route":"root-quit","execution_mode":"modern"}
        for key,bad,expected in (("source_sha","0"*40,"source/PE"),
                                 ("native_process_exit",1,"native process/draw"),
                                 ("native_semantic_route","practice","wrong Modern")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                receipt=dict(base);receipt[key]=bad
                (Path(tmp)/"readback-receipt.json").write_text(json.dumps(receipt))
                with self.assertRaisesRegex(ValueError,expected):
                    verify_capture(tmp)

    def test_nearest_neighbour_output_mapping_is_bounded(self):
        self.assertEqual(_sample_index(0,256,1024),0)
        self.assertEqual(_sample_index(1023,256,1024),255)
        self.assertEqual(_sample_index(767,224,768),223)

if __name__=="__main__":
    unittest.main()
