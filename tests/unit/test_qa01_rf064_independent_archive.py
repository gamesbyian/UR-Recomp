"""Synthetic fail-closed RF064 archive audit tests, no ROM or proprietary bytes."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf064_independent_archive as audit


def lines():
    return [
        "QA01RF045ORIGSTACK seq=1 f=1017 v=0 h=30 kind=pullW addr=01F0 width=2 value=9141 sp0=01EF sp1=01F1 pc=82:9141",
        "QA01RF064ORIGPULL f=1017 v=0 h=30 kind=pullW base=01F0 width=2 returned=9141 before=0 after=0 unique=0 pc=82:9141",
        "QA01RF044ORIGBUS f=1017 v=0 h=78 kind=ww bank=00 addr=01F0 w=2 value=914E pb=82 pc=914F S=01F1",
        "QA01RF063ORIGBUS seq=1 f=1017 v=0 h=78 kind=ww bank=00 addr=01F0 width=2 sampled=914E pc=82:914F S=01F1 phase=getset_entry",
        "QA01RF045ORIGSTACK seq=2 f=1017 v=0 h=94 kind=pushW addr=01F0 width=2 value=914E sp0=01F1 sp1=01EF pc=82:914F",
        "QA01RF063ORIGCHECKPOINT seq=2 f=1017 f1=1017 phase=post_real_nmi_push stack=26F0D48226 v=225 h=78 pc=00:8588",
        "QA01RF044ORIGNMI f=1017 f1=1017 pc=82D4F0 S0=01F0 S1=01EC old=8197005526 new=26F0D48226",
    ]


def archive_at(path: Path, source=None, changes=None):
    log = ("\n".join(lines() if source is None else source) + "\n").encode()
    members = {
        "work/zoom-zoo/replay/reference.log": log,
        "rf064-original-pulls.json": json.dumps({
            "schema": "ur-qa01-rf064-original-consumed-pull-join/1",
            "post_call_actual_original_pull_count": 1,
            "sequenced_original_bus_entries": 1,
            "actual_returns_with_unique_source_bus_entry": 0,
            "ambiguous_or_reentrant_original_pulls": 1,
            "accepted_USA_events": 0,
        }).encode(),
        "rf064-original-log-sha256.txt": (
            hashlib.sha256(log).hexdigest() + "  /tmp/reference.log\n").encode(),
        "case-result.json": json.dumps({
            "release_credit": 0, "source_sha": "a"*40,
            "evidence": {"rom_sha256": "b"*64},
        }).encode(),
    }
    members.update(changes or {})
    with zipfile.ZipFile(path, "w") as z:
        for name, body in members.items():
            z.writestr(name, body)


class IndependentRF064Archive(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "case.zip"
        archive_at(self.path)

    def test_real_return_is_preserved_without_fabricating_read_bus_entry(self):
        receipt = audit.examine(self.path)
        self.assertEqual(receipt["original_pull_returns_qualified_by_rf045"], 1)
        self.assertEqual(receipt["sequenced_original_getset_reads_observed"], 0)
        self.assertEqual(receipt["all_pull_returns_without_intervening_sequenced_bus_entry"], 1)
        self.assertFalse(receipt["actual_return_proves_specific_underlying_bus_site"])
        self.assertEqual(receipt["accepted_USA_events"], 0)

    def post_nmi_rows(self):
        return lines() + [
            "QA01RF064ORIGPULL f=1017 v=226 h=714 kind=pullB base=01ED width=1 returned=0026 before=2 after=2 unique=0 pc=80:B0EB",
            "QA01RF064ORIGPULL f=1017 v=226 h=730 kind=pullW base=01EE width=2 returned=D4F0 before=2 after=2 unique=0 pc=80:D4F0",
            "QA01RF064ORIGPULL f=1017 v=226 h=738 kind=pullB base=01F0 width=1 returned=0082 before=2 after=2 unique=0 pc=82:D4F0",
            "QA01RF064ORIGPULL f=1017 v=226 h=834 kind=pullB base=01F1 width=1 returned=0026 before=2 after=2 unique=0 pc=82:D4F5",
        ]

    def test_actual_original_nmi_return_bytes_and_pc_are_preserved(self):
        checkpoint = {"seq": "2", "f": "1017", "v": "225", "h": "78",
                      "stack": "26F0D48226"}
        witness = audit.post_nmi_return_witness(self.post_nmi_rows(), checkpoint)
        self.assertTrue(witness["matched_post_nmi_true_return_sequence"])
        self.assertEqual([r["actual_returned_value_hex"] for r in
                          witness["return_records"]], ["26", "D4F0", "82", "26"])
        self.assertEqual([r["original_post_call_pb_pcw"] for r in
                          witness["return_records"]],
                         ["80:B0EB", "80:D4F0", "82:D4F0", "82:D4F5"])
        self.assertFalse(witness["actual_underlying_read_bus_entry_proven"])
        self.assertFalse(witness["original_native_executed_pc_equivalence_proven"])

    def test_missing_source_returns_cannot_claim_nmi_consumption(self):
        checkpoint = {"seq": "2", "f": "1017", "v": "225", "h": "78",
                      "stack": "26F0D48226"}
        witness = audit.post_nmi_return_witness(lines(), checkpoint)
        self.assertFalse(witness["matched_post_nmi_true_return_sequence"])

    def test_altered_post_nmi_return_byte_rejected(self):
        checkpoint = {"seq": "2", "f": "1017", "v": "225", "h": "78",
                      "stack": "26F0D48226"}
        forged = [s.replace("returned=D4F0", "returned=D4F1")
                  for s in self.post_nmi_rows()]
        with self.assertRaisesRegex(ValueError, "return bytes disagree"):
            audit.post_nmi_return_witness(forged, checkpoint)

    def test_post_nmi_return_clock_cannot_precede_nmi_checkpoint(self):
        checkpoint = {"seq": "2", "f": "1017", "v": "225", "h": "78",
                      "stack": "26F0D48226"}
        forged = [s.replace("v=226 h=714", "v=224 h=714")
                  for s in self.post_nmi_rows()]
        with self.assertRaisesRegex(ValueError, "clock order invalid"):
            audit.post_nmi_return_witness(forged, checkpoint)

    def test_series_checks_real_return_values_for_each_original_nmi(self):
        log = self.post_nmi_rows()
        series = audit.original_nmi_return_series(log)
        self.assertEqual(series["original_nmi_observations"], 1)
        self.assertEqual(series["nmis_with_four_matching_actual_source_returns"], 1)
        self.assertTrue(series["all_observed_nmis_have_four_matching_returns"])
        self.assertFalse(series["native_equivalence_proven"])

    def test_series_without_returns_is_incomplete(self):
        series = audit.original_nmi_return_series(lines())
        self.assertEqual(series["original_nmi_observations"], 1)
        self.assertEqual(series["nmis_with_four_matching_actual_source_returns"], 0)
        self.assertFalse(series["all_observed_nmis_have_four_matching_returns"])

    def test_series_false_actual_original_return_does_not_count(self):
        forged = [s.replace("returned=D4F0", "returned=D4F1")
                  for s in self.post_nmi_rows()]
        with self.assertRaisesRegex(ValueError, "actual returned source bytes disagree"):
            audit.original_nmi_return_series(forged)

    def test_archive_hash_pin_rejects_replacement(self):
        with self.assertRaisesRegex(ValueError, "immutable archive"):
            audit.examine(self.path, "0"*64)

    def test_actual_return_cannot_differ_from_older_source_witness(self):
        archive_at(self.path, [r.replace("returned=9141", "returned=9142") for r in lines()])
        with self.assertRaisesRegex(ValueError, "returned data mismatch"):
            audit.examine(self.path)

    def test_missing_real_postcall_return_fails(self):
        archive_at(self.path, [r for r in lines() if not r.startswith("QA01RF064")])
        with self.assertRaisesRegex(ValueError, "post-call pull rows"):
            audit.examine(self.path)

    def test_ordinal_gap_is_not_joined(self):
        archive_at(self.path, [
            r.replace("seq=1 f=1017 v=0 h=78 kind=ww",
                      "seq=3 f=1017 v=0 h=78 kind=ww")
            if r.startswith("QA01RF063ORIGBUS") else r for r in lines()])
        with self.assertRaisesRegex(ValueError, "local ordinal"):
            audit.examine(self.path)

    def test_getset_sample_must_match_original_rf044_source(self):
        archive_at(self.path, [r.replace("sampled=914E", "sampled=1111")
                               for r in lines()])
        with self.assertRaisesRegex(ValueError, "same genuine RF044"):
            audit.examine(self.path)

    def test_nmi_checkpoint_must_match_unmasked_original_stack(self):
        archive_at(self.path, [r.replace("stack=26F0D48226", "stack=26F0D48227")
                               for r in lines()])
        with self.assertRaisesRegex(ValueError, "checkpoint does not match"):
            audit.examine(self.path)

    def test_truncated_original_trace_cannot_promote(self):
        archive_at(self.path, lines() + ["QA01RF064ORIGPULL_TRUNCATED"])
        with self.assertRaisesRegex(ValueError, "overflow"):
            audit.examine(self.path)

    def test_forged_reference_log_sha_rejected(self):
        archive_at(self.path, changes={
            "rf064-original-log-sha256.txt": b"0"*64+b"  /tmp/reference.log\n"})
        with self.assertRaisesRegex(ValueError, "log hash differs"):
            audit.examine(self.path)

    def test_producer_claims_do_not_override_actual_log(self):
        forged = {
            "schema": "ur-qa01-rf064-original-consumed-pull-join/1",
            "post_call_actual_original_pull_count": 1,
            "sequenced_original_bus_entries": 1,
            "actual_returns_with_unique_source_bus_entry": 1,
            "ambiguous_or_reentrant_original_pulls": 0,
            "accepted_USA_events": 0,
        }
        archive_at(self.path, changes={
            "rf064-original-pulls.json": json.dumps(forged).encode()})
        with self.assertRaisesRegex(ValueError, "claims do not agree"):
            audit.examine(self.path)


if __name__ == "__main__":
    unittest.main()
