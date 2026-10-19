"""ROM-free checks for exact source-original/native RF064→RF066 memory crosswalk."""
from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_independent_rf064_rf066_memory_crosswalk as check


class HistoricalRawCrosswalk(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.files = {
            check.RAW_ROOT + guest + "/scene-00001." + kind + ".bin":
                bytes(check.W_SIZE if kind == "wram" else check.S_SIZE)
            for guest in ("ref", "native") for kind in ("wram", "sram")
        }

    def run_pair(self, changed=None, *, required_count=4):
        old = dict(self.files)
        new = dict(self.files)
        if changed:
            changed(old, new)
        a, b = self.root / "a.zip", self.root / "b.zip"
        for file, entries in ((a, old), (b, new)):
            with zipfile.ZipFile(file, "w", compression=zipfile.ZIP_DEFLATED) as z:
                for name, content in entries.items():
                    z.writestr(name, content)
        with zipfile.ZipFile(a) as aa, zipfile.ZipFile(b) as bb:
            return check.compare_images(aa, bb, required_count=required_count)

    def test_every_original_native_full_memory_byte_reopened(self):
        value = self.run_pair()
        self.assertEqual(value["retained_original_native_raw_image_count"], 4)
        self.assertEqual(value["reopened_actual_memory_bytes"],
                         2 * (check.W_SIZE + check.S_SIZE))
        self.assertEqual(value["byte_differences_between_RF064_and_RF066"], 0)
        self.assertEqual(value["per_guest_identical_image_counts"],
                         {"ref": 2, "native": 2})

    def test_one_actual_original_or_native_memory_byte_does_not_get_masked(self):
        for guest in ("ref", "native"):
            for kind in ("wram", "sram"):
                def alter(before, after):
                    name = next(n for n in after if guest in n and n.endswith(
                        "." + kind + ".bin"))
                    arr = bytearray(after[name])
                    arr[-1] ^= 0x20
                    after[name] = bytes(arr)
                with self.subTest(guest=guest, kind=kind), self.assertRaisesRegex(
                        ValueError, "memory diverged"):
                    self.run_pair(alter)

    def test_missing_or_added_raw_image_is_not_ignored(self):
        def remove(before, after):
            del after[next(iter(after))]
        def add(before, after):
            after[check.RAW_ROOT + "native/extra.wram.bin"] = bytes(check.W_SIZE)
        for mutate in (remove, add):
            with self.subTest(mutate=mutate), self.assertRaisesRegex(
                    ValueError, "coverage changed"):
                self.run_pair(mutate)

    def test_truncated_raw_image_rejected(self):
        def mutate(before, after):
            path = next(iter(after))
            after[path] = after[path][:-1]
            before[path] = before[path][:-1]
        with self.assertRaisesRegex(ValueError, "size changed"):
            self.run_pair(mutate)

    def test_wrong_expected_cardinality_and_no_raw_passing_refused(self):
        with self.assertRaisesRegex(ValueError, "coverage changed"):
            self.run_pair(required_count=6)
        with self.assertRaisesRegex(ValueError, "coverage changed"):
            self.run_pair(required_count=0)

    def test_unknown_guest_label_is_not_a_valid_unmasked_pair(self):
        def rename(before, after):
            name = next(n for n in before if "/ref/" in n)
            updated = name.replace("/ref/", "/invented/")
            for table in (before, after):
                table[updated] = table.pop(name)
        with self.assertRaisesRegex(ValueError, "unknown original/native"):
            self.run_pair(rename)

    def test_wrong_exact_genuine_archive_refused_before_extracting(self):
        archive = self.root / "mock.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("producer-report.json", "{}")
        with self.assertRaisesRegex(ValueError, "wrong exact source-authentic ZIP"):
            check.checked_zip(archive, check.RF064_SHA)


if __name__ == "__main__":
    unittest.main()
