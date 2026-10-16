#!/usr/bin/env python3
"""Pure byte-contract checks for two overlapping immutable real Windows games."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa02_exact_owner_two_games as qa
from verify_retained_owner_playtest import SOURCE_COMMIT, CANDIDATE_SHA256, EXE_SHA256


def row(raw: bytes, generation: int):
    typed = ("UR-HOST-PROFILE/5\n"
             f"profile=native-ci-rider\ngeneration={generation}\n"
             f"stock_sram={raw.hex()}\n").encode("ascii")
    return {"raw": raw, "typed": typed,
            "selector": b"selected:first", "catalog": b"roster:first"}


class NativeTwoRealGameProcessTests(unittest.TestCase):
    def test_original_candidate_stable_and_one_shot_workflow(self):
        self.assertEqual(SOURCE_COMMIT, "11501a15dea38fa912335cfc63103ce3a7208001")
        self.assertEqual(CANDIDATE_SHA256,
                         "5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7")
        self.assertEqual(EXE_SHA256,
                         "0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9")
        source = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text("utf-8")
        self.assertIn("qa/qa02-exact-owner-two-running-games-20261016", source)
        self.assertIn("--retained", source)
        self.assertIn("12016101293", source)
        self.assertIn("tools/qa02_exact_owner_two_games.py", source)

    def test_authentic_B_commit_and_stale_A_failclosed_contract(self):
        first = bytes(range(256)) * 32
        newer = first[:-1] + bytes([first[-1] ^ 0x5a])
        old, b = row(first, 1), row(newer, 2)
        result = qa.verify_interleaving(old, b, dict(b))
        self.assertEqual(result["raw_changed_bytes"], 1)
        self.assertEqual(result["generation_before"], 1)
        self.assertEqual(result["generation_after_B"], 2)
        with self.assertRaisesRegex(ValueError, "did not save new"):
            qa.verify_interleaving(old, old, old)
        with self.assertRaisesRegex(ValueError, "overwrote second game's"):
            qa.verify_interleaving(old, b, old)
        bad_roster = dict(b, catalog=b"stale roster")
        with self.assertRaisesRegex(ValueError, "global selector"):
            qa.verify_interleaving(old, bad_roster, bad_roster)
        wrong_typed = dict(b, typed=row(first, 2)["typed"])
        with self.assertRaisesRegex(ValueError, "typed 8192 SRAM"):
            qa.verify_interleaving(old, wrong_typed, wrong_typed)
        same_generation = row(newer, 1)
        with self.assertRaisesRegex(ValueError, "did not save new"):
            qa.verify_interleaving(old, same_generation, same_generation)
        with self.assertRaisesRegex(ValueError, "partial canonical"):
            qa.verify_interleaving(old, {"raw": newer}, b)

    def test_four_canonical_files_full_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root, output = Path(temp) / "root", Path(temp) / "out"
            root.mkdir()
            sample = row(bytes(range(256)) * 32, 1)
            for label, rel in qa.FILES.items():
                f = root / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(sample[label])
            self.assertEqual(qa.snapshot(root, output, "before_A"), sample)
            receipt = json.loads((output / "before_A.json").read_text("utf-8"))
            for k in sample:
                self.assertEqual((output / f"before_A.{k}.bin").read_bytes(), sample[k])
                self.assertEqual(receipt[k]["sha256"], qa.digest(sample[k]))
            with self.assertRaisesRegex(ValueError, "unknown exact-original"):
                qa.snapshot(root, output, "bad_stage")
            (root / qa.FILES["raw"]).write_bytes(b"too short")
            with self.assertRaisesRegex(ValueError, "8192 bytes"):
                qa.snapshot(root, output, "after_B")


if __name__ == "__main__":
    unittest.main()
