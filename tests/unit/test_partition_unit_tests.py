import unittest

from tools.partition_unit_tests import discover, partition
from pathlib import Path


class PartitionUnitTests(unittest.TestCase):
    def test_every_module_in_exactly_one_shard(self):
        mods = discover(Path("tests/unit"))
        self.assertIn("tests.unit.test_partition_unit_tests", mods)
        for n in (1, 2, 4, 7):
            parts = partition(mods, {mods[0]: 50.0}, n)
            flat = [m for p in parts for m in p]
            self.assertEqual(sorted(flat), mods)
            self.assertEqual(len(flat), len(set(flat)))

    def test_balanced_and_deterministic(self):
        mods = [f"m{i}" for i in range(8)]
        t = {m: 10.0 for m in mods}
        parts = partition(mods, t, 4)
        self.assertEqual([len(p) for p in parts], [2, 2, 2, 2])
        self.assertEqual(parts, partition(list(reversed(mods)), t, 4))

    def test_unknown_modules_still_covered(self):
        self.assertEqual(sum(len(p) for p in partition(["a", "b", "c"], {}, 2)), 3)


if __name__ == "__main__":
    unittest.main()
