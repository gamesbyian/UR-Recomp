"""ROM-free falsification of exact RF062 dump-only source-script equivalence."""
from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_independent_rf062_dump_script_provenance as verify


def fixture():
    return "\n".join(("until 009F == D7 3600", "wait 60", "press a 2",
                      "dump scene-05046", "wait 54",
                      *verify.BASE_SEGMENT, "until 009F == BC 9000",
                      "dump result-onset", "quit")) + "\n"


def candidate():
    return fixture().replace("\n".join(verify.BASE_SEGMENT),
                             "\n".join(verify.CANDIDATE_SEGMENT))


class ExactSourceCommandSchedule(unittest.TestCase):
    def test_exact_three_dump_insertions_do_not_change_controller_schedule(self):
        result = verify.equivalent_scripts(fixture().encode(), candidate().encode())
        self.assertEqual(result["unchanged_wait_frame_budget"], 134)
        self.assertEqual(result["observer_dump_positions_are_source_relative_after_5100"],
                         [5105, 5106, 5107])
        self.assertEqual(len(result["exact_new_observer_dumps"]), 3)
        self.assertTrue(result["unchanged_source_controller_and_standard_dump_command_timeline"])

    def test_added_or_mutated_gameplay_command_before_after_and_between_fails(self):
        invalid = [
            candidate().replace("press a 2", "press b 2"),
            candidate().replace("wait 54", "wait 55"),
            candidate().replace("until 009F == BC 9000", "until 009F == BB 9000"),
            candidate().replace("wait 13", "wait 12"),
            candidate().replace("wait 1\ndump qa01-frame-005106",
                                "wait 2\ndump qa01-frame-005106"),
            candidate().replace("dump qa01-frame-005107",
                                "dump qa01-frame-005108"),
            candidate().replace("dump scene-05120", "dump scene-05120\npress a 2"),
            candidate().replace("dump scene-05100", "dump scene-05100\ndump extra"),
            candidate().replace("dump qa01-frame-005106",
                                "dump qa01-frame-005106\nwait 1"),
            candidate().replace("dump result-onset", "dump result-onset\nwait 1"),
        ]
        for script in invalid:
            with self.subTest(diff=script[:80]), self.assertRaises(ValueError):
                verify.equivalent_scripts(fixture().encode(), script.encode())

    def test_wrong_original_script_is_not_an_identity_oracle(self):
        with self.assertRaises(ValueError):
            verify.equivalent_scripts(fixture().replace("press a", "press b").encode(),
                                      candidate().encode())

    def test_non_ascii_or_missing_linebreaks_are_not_rewritten(self):
        for original, updated in (
            (fixture().encode(), candidate().rstrip("\n").encode()),
            (fixture().encode(), candidate().encode() + b"\xff"),
            (fixture().encode(), candidate().replace("\n", "\r\n").encode()),
        ):
            with self.subTest(updated=updated[:25]), self.assertRaises(ValueError):
                verify.equivalent_scripts(original, updated)

    def test_duplicate_legacy_dump_anchor_does_not_qualify(self):
        changed = candidate().replace("dump scene-05100",
                                      "dump scene-05100\ndump scene-05100")
        with self.assertRaisesRegex(ValueError, "boundary missing"):
            verify.equivalent_scripts(fixture().encode(), changed.encode())

    def test_exact_zip_pin_rejects_fake_valid_scripts(self):
        with tempfile.TemporaryDirectory() as d:
            fake = Path(d) / "test.zip"
            with zipfile.ZipFile(fake, "w") as archive:
                archive.writestr(verify.SCRIPT, fixture())
            with self.assertRaisesRegex(ValueError, "archive SHA256"):
                verify.open_zip(fake, verify.BASE_ZIP_SHA)


if __name__ == "__main__":
    unittest.main()
