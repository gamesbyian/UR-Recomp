import unittest

from tools.analyze_translation_controls import analyze


def ips_record(offset: int, data: bytes) -> bytes:
    return (
        b"PATCH"
        + offset.to_bytes(3, "big")
        + len(data).to_bytes(2, "big")
        + data
        + b"EOF"
    )


class TranslationControlTests(unittest.TestCase):
    def test_preserved_and_changed_nonprintables_are_separated(self):
        base = bytearray(b" " * 0x100)
        base[0x20:0x26] = b"A\x01B\x02C!"
        patch = ips_record(0x20, b"X\x01Y\x03Z!")
        report = analyze(bytes(base), patch)
        rows = {row["value"]: row for row in report["control_values"]}
        self.assertEqual(rows[0x01]["preserved_count"], 1)
        self.assertEqual(rows[0x01]["changed_count"], 0)
        self.assertEqual(rows[0x03]["changed_count"], 1)
        self.assertEqual(
            report["changed_control_pairs"],
            [{"before": "0x02", "after": "0x03", "count": 1}],
        )
        runs = {row["hex"]: row["count"] for row in report["control_runs"]}
        self.assertEqual(runs["01"], 1)
        self.assertEqual(runs["03"], 1)


if __name__ == "__main__":
    unittest.main()
