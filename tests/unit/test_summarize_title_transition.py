import json, tempfile, unittest
from pathlib import Path
from tools.summarize_title_transition import summarize

class TitleTransitionSummaryTests(unittest.TestCase):
    def test_summarizes_named_dump(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); tag="boot-060"
            (p/f"{tag}.info.json").write_text(json.dumps({"frame":60,"fb_frame":60}))
            w=bytearray(0x4000); w[0x009F]=0x84
            (p/f"{tag}.wram.bin").write_bytes(w)
            (p/f"{tag}.fb.bgrx").write_bytes(bytes(16))
            r=summarize(p)
            self.assertEqual(r["checkpoints"][0]["menu_hex"],"0x84")
            self.assertEqual(r["checkpoints"][0]["frame"],60)
if __name__=="__main__": unittest.main()
