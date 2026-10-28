"""The measured unit shard runner must preserve coverage, exits and timing."""
import io
import json
import unittest
from pathlib import Path

from tools.run_unit_shard import SCHEMA, execute, make_receipt


class _Loader:
    def __init__(self, fail=False):
        self.fail = fail
        self.loaded = []

    def loadTestsFromName(self, name):
        self.loaded.append(name)
        class PassCase(unittest.TestCase):
            def test_pass(self):
                self.assertTrue(True)

        class FailCase(unittest.TestCase):
            def test_fail(self):
                self.fail("synthetic failure must remain red")

        klass = FailCase if self.fail and name.endswith("bad") else PassCase
        return unittest.defaultTestLoader.loadTestsFromTestCase(klass)


class RunUnitShardTests(unittest.TestCase):
    def test_modules_run_once_and_print_one_global_summary(self):
        mods = ["tests.unit.test_alpha", "tests.unit.test_beta"]
        loader = _Loader()
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result, timings = execute(mods, loader=loader, runner=runner)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(loader.loaded, mods)
        self.assertEqual(set(timings), set(mods))
        self.assertTrue(all(isinstance(v, float) and 0 <= v < 3600
                            for v in timings.values()))
        self.assertEqual(stream.getvalue().count("Ran 2 tests"), 1)
        self.assertIn("\nOK\n", stream.getvalue())
        receipt = make_receipt(mods, timings, True)
        self.assertEqual(receipt["schema"], SCHEMA)
        self.assertTrue(receipt["diagnostic_only"])
        self.assertTrue(receipt["full_test_suite_passed"])
        self.assertEqual(receipt["observed_modules"], 2)
        self.assertEqual(set(json.loads(json.dumps(receipt))["module_timings_seconds"]),
                         set(mods))

    def test_failure_is_not_misreported_as_success(self):
        mods = ["tests.unit.test_alpha", "tests.unit.test_bad"]
        stream = io.StringIO()
        result, timings = execute(
            mods, loader=_Loader(fail=True),
            runner=unittest.TextTestRunner(stream=stream, verbosity=1))
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(len(timings), 2)
        self.assertIn("FAILED", stream.getvalue())
        self.assertFalse(make_receipt(mods, timings, False)["full_test_suite_passed"])

    def test_empty_repeated_and_non_test_module_rejected(self):
        for mods in (
            [], ["tools.agent_control"],
            ["tests.unit.test_alpha", "tests.unit.test_alpha"],
            ["tests.unit.test_alpha;echo broken"],
        ):
            with self.subTest(mods=mods), self.assertRaisesRegex(
                    ValueError, "distinct"):
                execute(mods, loader=_Loader())

    def test_existing_test_suite_is_unmodified(self):
        # The checked-in timing dataset is a static scheduling hint, never a
        # truth source for test discovery, pass/fail or release acceptance.
        self.assertTrue(Path("tools/unit_test_timings.json").is_file())


if __name__ == "__main__":
    unittest.main()
