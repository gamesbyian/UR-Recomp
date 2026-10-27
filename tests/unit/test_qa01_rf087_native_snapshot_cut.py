"""RF087 source-native dump metadata joins, without extra C instrumentation."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf087_native_snapshot_cut_receipt as receipt


def sample(directory, tag, frame, master, ptr, counter, **updates):
    data = {"frame": frame, "master_clock": master, "vpos": 224,
            "hpos": 726, "source": "snesrecomp"}
    data.update(updates)
    (directory / (tag + ".info.json")).write_text(json.dumps(data))
    wram = bytearray(131072)
    wram[0x63:0x65] = ptr.to_bytes(2, "little")
    wram[0x69] = counter
    (directory / (tag + ".wram.bin")).write_bytes(wram)


class NativeSnapshotCutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        sample(self.root, "scene-05039", 6058, 12345, 0xC6B0, 0x9F)
        sample(self.root, "scene-05040", 6059, 12456, 0xC74D, 0x97)
        self.log = (b"script f=6058 dump scene-05039 ok\n"
                    b"script f=6059 dump scene-05040 ok\n")

    def test_existing_dump_metadata_and_raw_wram_form_real_cut(self):
        report = receipt.audit(self.root, self.log)
        self.assertEqual(report["native_cut_rows"][0]["pointer16_at_cut"], 0xC6B0)
        self.assertEqual(report["native_cut_rows"][1]["pointer16_at_cut"], 0xC74D)
        self.assertEqual(report["native_cut_rows"][1]["counter8_at_cut"], 0x97)
        self.assertEqual(report["native_cut_rows"][1]["native_master_at_cut"], 12456)
        self.assertEqual(report["release_credit"], 0)
        self.assertFalse(report["original_native_clock_registration_proven"])
        self.assertEqual(len(report["native_dump_member_hashes"]), 2)

    def test_missing_partial_duplicate_or_mismatched_log_rejected(self):
        for raw in (b"", self.log.replace(b" ok", b" partial"),
                    self.log + self.log.splitlines(keepends=True)[0],
                    self.log.replace(b"6059", b"6060")):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                receipt.audit(self.root, raw)

    def test_metadata_and_raw_wram_fail_closed(self):
        info = self.root / "scene-05040.info.json"
        wram = self.root / "scene-05040.wram.bin"
        good_info, good_wram = info.read_bytes(), wram.read_bytes()
        mutations = [b"{", b"{}", good_info.replace(b"6059", b"6058"),
                     good_info.replace(b"12456", b"12000"),
                     good_info.replace(b'"snesrecomp"', b'"unknown"')]
        for data in mutations:
            info.write_bytes(data)
            with self.subTest(data=data), self.assertRaises(ValueError):
                receipt.audit(self.root, self.log)
        info.write_bytes(good_info)
        wram.write_bytes(good_wram[:65536])
        with self.assertRaisesRegex(ValueError, "128 KiB"):
            receipt.audit(self.root, self.log)
        wram.unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            receipt.audit(self.root, self.log)

    def test_workflow_retains_existing_info_files(self):
        workflow = (Path(__file__).resolve().parents[2] /
                    ".github/workflows/qa01-event-campaign.yml").read_text()
        self.assertIn("replay/native/*.info.json", workflow)
        self.assertIn("--native-dir", workflow)
        self.assertNotIn("tools/qa01_rf087_native_snapshot_cut.py --root", workflow)


if __name__ == "__main__":
    unittest.main()
