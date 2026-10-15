"""Accept only one authentic Snes9x 1P 16-frame sparse source census."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_original_oneplayer_sparse_fullroute_manifest as source  # noqa: E402


class OnePlayerSparseSourceTest(unittest.TestCase):
    def test_fixed_261_frames_cover_entry_race_and_return(self):
        self.assertEqual(len(range(source.FIRST,source.LAST+1,source.STEP)),261)
        self.assertEqual((source.FIRST,source.LAST,source.STEP),(1279,5439,16))
        self.assertEqual(source.SIZE,229376)

    def test_wrong_rom_script_log_and_missing_source_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            folder=root/"original"
            folder.mkdir()
            script=root/"script.txt"
            script.write_text("until16 0053 == 8610\npress right 1200\nquit\n")
            log=root/"log.txt"
            log.write_text("script f=5447 quit\n")
            core=root/"core.so"
            core.write_bytes(b"test")
            rom=root/"USA.sfc"
            rom.write_bytes(b"dummy")
            with self.assertRaisesRegex(ValueError,"original USA"):
                source.observe(folder,script,log,rom,core)
            with patch.object(source,"ROM_SHA",hashlib.sha256(rom.read_bytes()).hexdigest()):
                with self.assertRaisesRegex(ValueError,"missing"):
                    source.observe(folder,script,log,rom,core)
                with self.assertRaises(ValueError):
                    script.write_text("turbo on\nuntil16 0053 == 8610\npress right 1200\n")
                    source.observe(folder,script,log,rom,core)
                script.write_text("until16 0053 == 8610\npress right 1200\n")
                log.write_text("script f=5439 quit\n")
                with self.assertRaisesRegex(ValueError,"finish"):
                    source.observe(folder,script,log,rom,core)

    def test_real_source_manifest_rejects_one_cropped_full_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            folder=root/"frames"
            folder.mkdir()
            script=root/"script.txt"
            script.write_text("until16 0053 == 8610\npress right 1200\nquit\n")
            log=root/"log.txt"
            log.write_text("script f=5447 quit\n")
            core=root/"core.so"
            core.write_bytes(b"test core")
            rom=root/"USA.sfc"
            rom.write_bytes(b"authentic-source-test-standin")
            raw=bytes([0,0,0,0])*256*224
            for i in range(source.FIRST,source.LAST+1,source.STEP):
                (folder/f"frame_{i:06d}_256x224.raw").write_bytes(
                    raw if i!=source.LAST else raw[:-1])
            with patch.object(source,"ROM_SHA",hashlib.sha256(rom.read_bytes()).hexdigest()):
                with self.assertRaisesRegex(ValueError,"cropped"):
                    source.observe(folder,script,log,rom,core)


if __name__=="__main__":
    unittest.main()
