"""ROM-free negative tests for independent genuine original RF064 read-coverage."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_independent_rf064_original_return_coverage as evidence


def checked(pulls, buses, *, joined=0, ambiguity=None, all_qualified=False):
    return {
        "post_call_actual_original_pull_count": len(pulls),
        "sequenced_original_bus_entries": len(buses),
        "actual_returns_with_unique_source_bus_entry": joined,
        "ambiguous_or_reentrant_original_pulls":
            len(pulls) - joined if ambiguity is None else ambiguity,
        "original_return_join_all_qualified": all_qualified,
    }


class OriginalRF064ReadCoverage(unittest.TestCase):
    def test_actual_bounded_original_write_only_trace_does_not_invent_read_join(self):
        # Genuine original RF064 shape: 710 word pulls, 193 byte pulls;
        # RF063 only sees 710 word WRITES and 193 byte WRITES.
        pulls = [
            {"before": str(i), "after": str(i), "kind":
             "pullW" if i < 710 else "pullB"}
            for i in range(903)
        ]
        buses = [
            {"kind": "ww" if i < 710 else "wb"}
            for i in range(903)
        ]
        outcome = evidence.classify(pulls, buses, checked(pulls, buses))
        self.assertEqual(outcome["source_getset_read_entries"], 0)
        self.assertEqual(outcome["source_getset_write_entries"], 903)
        self.assertEqual(outcome["pulls_with_no_getset_ordinal_increase"], 903)
        self.assertEqual(outcome["real_post_call_values_attributed_to_actual_bus_reads"], 0)
        self.assertEqual(outcome["reason"], "original_getset_read_path_not_observed")

    def test_actual_unique_entry_is_distinct_from_observed_writer_count(self):
        pulls = [{"before": "0", "after": "1", "kind": "pullB"}]
        buses = [{"kind": "rb"}]
        result = evidence.classify(
            pulls, buses, checked(pulls, buses, joined=1, all_qualified=True))
        self.assertEqual(result["source_getset_read_entries"], 1)
        self.assertEqual(result["pulls_with_exactly_one_getset_ordinal_increase"], 1)
        self.assertEqual(result["reason"], "bounded_postcall_read_entries_joined")

    def test_multiple_ordinal_events_are_not_laundered_into_single_read(self):
        pulls = [{"before": "2", "after": "4", "kind": "pullW"}]
        buses = [{"kind": "rw"}, {"kind": "ww"}]
        result = evidence.classify(pulls, buses, checked(pulls, buses))
        self.assertEqual(result["pulls_with_multiple_getset_ordinal_increases"], 1)
        self.assertEqual(result["real_post_call_values_attributed_to_actual_bus_reads"], 0)
        self.assertEqual(result["reason"], "incomplete_or_mixed_original_read_attribution")

    def test_regressed_or_false_join_counters_fail(self):
        cases = [
            ([{"before": "2", "after": "1", "kind": "pullB"}],
             [{"kind": "wb"}], None),
            ([{"before": "0", "after": "1", "kind": "pullB"}],
             [{"kind": "rb"}], {"joined": 0}),
            ([{"before": "0", "after": "0", "kind": "pullW"}],
             [{"kind": "ww"}], {"ambiguity": 0}),
            ([{"before": "0", "after": "0", "kind": "pullW"}],
             [{"kind": "invented"}], None),
        ]
        for pulls, buses, kw in cases:
            with self.subTest(pulls=pulls, buses=buses), self.assertRaises(ValueError):
                evidence.classify(pulls, buses, checked(pulls, buses, **(kw or {})))

    def test_absent_pinned_case_cannot_impersonate_real_zip(self):
        with tempfile.TemporaryDirectory() as d:
            archive = Path(d) / "synthetic.zip"
            with zipfile.ZipFile(archive, "w") as out:
                out.writestr("rf064-original-pulls.json", "{}")
            with self.assertRaisesRegex(ValueError, "wrong exact ZIP provenance"):
                evidence.zip_open(archive, evidence.DEFAULT_DIGESTS["case"])

    def test_duplicate_zip_member_is_rejected_even_with_correct_zip_hash(self):
        with tempfile.TemporaryDirectory() as d:
            archive = Path(d) / "case.zip"
            with zipfile.ZipFile(archive, "w") as out:
                out.writestr("same", "one")
                out.writestr("same", "two")
            digest = evidence.sha256(archive.read_bytes())
            with self.assertRaisesRegex(ValueError, "duplicated"):
                evidence.zip_open(archive, digest)


if __name__ == "__main__":
    unittest.main()
