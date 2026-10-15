"""Independent original 2P one-shot full-route raster authority gates."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_original_twoplayer_fullroute_manifest as source  # noqa: E402


class Original2PSourceTest(unittest.TestCase):
    def test_bounded_authentic_callback_schedule_and_quit_time(self):
        self.assertEqual(source.FIRST,1279)
        self.assertEqual(source.STEP,16)
        self.assertEqual(source.SIZE,256*224*4)
        self.assertEqual(source.callback_numbers(5447)[0],1279)
        self.assertEqual(source.callback_numbers(5447)[-1],5439)
        for value in (0,2000,3499,9505):
            with self.subTest(value=value),self.assertRaises(ValueError):
                source.callback_numbers(value)

    def test_source_rom_script_and_finish_require_proven_original(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            frames=root/"frames"
            frames.mkdir()
            script=root/"script.txt"
            script.write_bytes(b"until16 0053 == F60C\n"
                               b"until16 0053 == 8610\n"
                               b"press right+p2:right 1500\n"
                               b"press p2:down 2\n"
                               b"until16 0053 == F60C\nquit\n")
            log=root/"log.txt"
            log.write_text("script f=5400 quit\n")
            core=root/"core.so"
            core.write_bytes(b"core fixture")
            rom=root/"ROM.sfc"
            rom.write_bytes(b"fake")
            with self.assertRaisesRegex(ValueError,"USA retail"):
                source.observe(frames,script,log,rom,core)
            with patch.object(source,"ROM",hashlib.sha256(rom.read_bytes()).hexdigest()):
                with self.assertRaisesRegex(ValueError,"missing"):
                    source.observe(frames,script,log,rom,core)
                script.write_bytes(script.read_bytes().replace(b"p2:down",b"p1:down"))
                with self.assertRaisesRegex(ValueError,"route"):
                    source.observe(frames,script,log,rom,core)
                script.write_bytes(b"turbo on\n"+script.read_bytes())
                with self.assertRaisesRegex(ValueError,"route"):
                    source.observe(frames,script,log,rom,core)

    def test_final_scene_must_not_be_claimed_if_script_incomplete(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            folder=root/"frames"
            folder.mkdir()
            script=root/"script"
            script.write_bytes(b"until16 0053 == F60C\n"
                               b"until16 0053 == 8610\n"
                               b"press right+p2:right 1500\n"
                               b"press p2:down 2\n"
                               b"until16 0053 == F60C\nquit\n")
            log=root/"log"
            log.write_text("not yet finished")
            rom=root/"rom"
            rom.write_bytes(b"fixture")
            core=root/"core"
            core.write_bytes(b"fixture")
            with patch.object(source,"ROM",hashlib.sha256(rom.read_bytes()).hexdigest()):
                with self.assertRaisesRegex(ValueError,"never completed"):
                    source.observe(folder,script,log,rom,core)


if __name__=="__main__":
    unittest.main()
