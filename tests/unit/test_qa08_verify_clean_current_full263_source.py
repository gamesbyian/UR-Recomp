"""Full original source archive identity and fail-closed no-release receipt."""
import sys,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools import qa08_verify_clean_current_full263_source as q
class CleanRealWin32Receipt(unittest.TestCase):
    def test_fail_closed_missing_bad_source(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as t:
            p=Path(t)/"wrong.zip";p.write_bytes(b"wrong")
            with self.assertRaisesRegex(ValueError,"identity drift"):q.verify(p)
    def test_current_evidence_holds_original_pixel_baseline_and_no_QA(self):
        r=json.loads((ROOT/"analysis/data/qa08-current-clean-compiled-win32-full263-source-20261018.json").read_text())
        self.assertEqual(r["current_compiled_original_PPU_Win32_PE_SHA256"],q.PE)
        self.assertEqual(r["source_outer_zip_sha256"],q.ZIP_SHA)
        self.assertEqual(r["full_256x224_source_RGB5_pixel_positions"],15081472)
        self.assertEqual(r["pixel_regressions_vs_existing_clean_source"],0)
        self.assertEqual(r["current_clean_source_wrong_RGB5"],890205)
        self.assertFalse(r["real_4K_7to6_HD_artist_approval_or_release_accepted"])
if __name__=="__main__":unittest.main()
