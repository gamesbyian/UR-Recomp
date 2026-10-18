"""RF048 recorder source anchors must preserve actual original CPU execution."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_rf035_sound_consumer_observer as rf035
import qa01_rf048_original_sound_pointer_witness as rf048


class OriginalPointerWitnessTests(unittest.TestCase):
    @staticmethod
    def fixture():
        # Model an already pinned genuine RF035 stage, not a pristine emulator.
        return (
            "#include <stdio.h>\n"
            + rf035.ORIG_BEFORE + "\n"
            + rf035.ORIG_DISPATCH + "\n"
            + rf035.ORIG_AFTER
            + "\n"
        )

    def test_one_actual_dispatch_and_read_only_host_ram_observer(self):
        before = self.fixture()
        after = rf048.patch_original(before)
        self.assertEqual(after.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertEqual(after.count(rf048.MARK), 1)
        self.assertEqual(after.count("Memory.RAM[rf048_dp]"), 1)
        self.assertEqual(after.count("QA01RF048ORIGPTR "), 1)
        self.assertEqual(after.count("QA01RF048ORIGPTR count="), 1)
        self.assertEqual(after.count("QA01RF048ORIGPTR_TRUNCATED"), 1)
        self.assertIn("ur_rf035_pc == 0x82F0u", after)
        self.assertEqual(rf048.patch_original(after), after)

    def test_fail_closed_on_unknown_or_tampered_original_source(self):
        before = self.fixture()
        with self.assertRaisesRegex(ValueError, "intact RF035"):
            rf048.patch_original(before.replace(rf035.ORIG_AFTER, ""))
        with self.assertRaisesRegex(ValueError, "intact RF035"):
            rf048.patch_original(before.replace("(*Opcodes[Op].S9xOpcode)();",
                                                 "incorrect_dispatch();"))
        after = rf048.patch_original(before)
        with self.assertRaisesRegex(ValueError, "partial original pointer"):
            rf048.patch_original(after.replace("rf048_target", "rf048_target_tampered", 1)
                                        .replace(rf048.AFTER, "", 1))

if __name__ == "__main__":
    unittest.main()
