"""Read-only Uniracers channel-7 HDMA firstline probe safety tests."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_qa08_native_firstline_hdma_readonly_patch as trace
import qa08_windows_full_twoplayer_source_coverage as capture


class FirstLineWitness(unittest.TestCase):
    def setUp(self):
        self.raw=("/* "+trace.CANDIDATE_MARK+" */\n"+trace.START+
                  "    if (!ch->hdmaActive || ch->terminated || !ch->doTransfer) continue;\n"+
                  "    int len = transferLength[ch->mode & 7];\n"+
                  "    ch->repCount--;\n    ch->doTransfer = (ch->repCount & 0x80) != 0;\n"
                  "  }\n}"+trace.END+"\n")

    def test_source_patch_only_adds_two_probes_without_guest_effects(self):
        changed=trace.patch_source(self.raw)
        self.assertEqual(trace.patch_source(changed),changed)
        self.assertEqual(changed.count(trace.MARK),1)
        self.assertEqual(changed.replace(trace.PRE,"").replace(trace.POST,""),self.raw)
        self.assertIn("mem[0x2064]",changed)
        self.assertIn('getenv("UR_QA08_WINDOWS_HDMA_FIRSTLINE_TRACE")',changed)
        self.assertIn("ch->repCount--",changed)
        self.assertNotIn("mem[0x2064] =",changed)

    def test_wrong_source_and_tampered_instrument_refused(self):
        candidates=(self.raw.replace(trace.CANDIDATE_MARK,"no_proof"),
                    self.raw.replace(trace.BEFORE,""),
                    trace.patch_source(self.raw).replace("frame=%d","frame=%u",1))
        for c in candidates:
            with self.subTest(candidate=c[:64]),self.assertRaises(ValueError):
                trace.patch_source(c)

    def test_original_bbus_firstline_probe_parses_bounded_live_source(self):
        before=("UR_QA08_WIN_HDMA7 frame=3683 phase=pre enable=1 terminated=0 "
                "transfer=1 aBank=7e aAdr=2064 tableAdr=2065 rep=80 bAdr=00 "
                "bytes=8007000780000000 inidisp=0f\n")
        after=("UR_QA08_WIN_HDMA7 frame=3683 phase=post enable=1 terminated=0 "
               "transfer=0 tableAdr=2066 rep=7f inidisp=07\n")
        receipt=capture.inspect_native_channel7_firstline(before+after)
        self.assertEqual(receipt["live_channel7_before"][0]["frame"],3683)
        self.assertEqual(receipt["live_channel7_before"][0]["live_WRAM_2064_to_206B"],
                         "8007000780000000")
        self.assertFalse(receipt["release_gate_accepted"])
        with self.assertRaises(ValueError):
            capture.inspect_native_channel7_firstline("")
        with self.assertRaises(ValueError):
            capture.inspect_native_channel7_firstline(before+before+after)
        with self.assertRaises(ValueError):
            capture.inspect_native_channel7_firstline(before.replace("bAdr=00","bAdr=04")+after)

    def test_source_game_pins_before_any_disk_write(self):
        with tempfile.TemporaryDirectory() as td:
            game=Path(td)
            p=game/trace.REL
            p.parent.mkdir(parents=True)
            p.write_text(self.raw)
            (game/"src/gen").mkdir(parents=True)
            (game/"src/gen/dispatch_v2.c").write_text("game")
            with patch.object(trace,"pinned_revision",side_effect=["wrong",trace.CORE_REV]):
                with self.assertRaises(ValueError):
                    trace.apply_game(game,write=True)
            self.assertEqual(p.read_text(),self.raw)
            with patch.object(trace,"pinned_revision",side_effect=[trace.GAME_REV,trace.CORE_REV]):
                trace.apply_game(game,write=True)
            self.assertEqual(p.read_text(),trace.patch_source(self.raw))


if __name__=="__main__":
    unittest.main()
