"""QA-02 C12 manual campaign receipt/producer protocol regression tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa02_c12_campaign as campaign  # noqa: E402


SOURCE_SHA = "a" * 40
BINARY_DIGEST = "b" * 64
BASE_SEED = 11413


def valid_shard(index: int, *, trials: int = 3) -> dict:
    return {
        "schema": "ur-qa02-c12-campaign-shard/1",
        "source_commit": SOURCE_SHA,
        "binary_sha256": BINARY_DIGEST,
        "shard": index,
        "seed": BASE_SEED + index * 1000003,
        "requested_trials": trials,
        "attempted_trials": trials,
        "passed_trials": trials,
        "failed_trials": 0,
        "disposition": "completed_positive",
        "failures": [],
        "elapsed_ms": 1,
        "release_gate_credit": 0,
        "process_death_or_power_loss_claim": False,
    }


def populate(root: Path, *, trials: int = 3) -> None:
    for shard in range(4):
        dest = root / f"qa02-c12-shard-{shard}/result.json"
        dest.parent.mkdir()
        dest.write_text(json.dumps(valid_shard(shard, trials=trials)), encoding="utf-8")


class C12CampaignTests(unittest.TestCase):
    def test_compile_manifest_is_reused_from_original_process_fixture(self):
        sources = campaign.existing_test_sources()
        self.assertIn("local_tournament_session_coordinator.cpp", sources)
        self.assertIn("local_tournament_session_store.cpp", sources)
        self.assertEqual(len(sources), len(set(sources)))

    def test_all_four_shards_are_required_for_positive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            populate(root)
            report = campaign.aggregate(root, SOURCE_SHA, BINARY_DIGEST, 3, BASE_SEED)
            self.assertEqual(report["disposition"], "completed_positive")
            self.assertEqual(report["requested_trials"], 12)
            self.assertEqual(report["observed_trials"], 12)
            self.assertEqual(report["passed_trials"], 12)
            self.assertEqual(report["release_gate_credit"], 0)
            self.assertIn("no complete game", report["scope"])

    def test_missing_shard_cannot_be_masked_by_three_positive_shards(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            populate(root)
            (root / "qa02-c12-shard-3/result.json").unlink()
            report = campaign.aggregate(root, SOURCE_SHA, BINARY_DIGEST, 3, BASE_SEED)
            self.assertEqual(report["disposition"], "incomplete")
            self.assertEqual(report["missing_shards"], [3])
            self.assertEqual(report["observed_trials"], 9)

    def test_provenance_and_count_tampering_is_invalid(self):
        for field, value in (
            ("binary_sha256", "c" * 64),
            ("source_commit", "d" * 40),
            ("seed", BASE_SEED),
            ("attempted_trials", 2),
            ("release_gate_credit", 1),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                populate(root)
                bad = root / "qa02-c12-shard-2/result.json"
                row = json.loads(bad.read_text())
                row[field] = value
                bad.write_text(json.dumps(row), encoding="utf-8")
                report = campaign.aggregate(root, SOURCE_SHA, BINARY_DIGEST, 3, BASE_SEED)
                self.assertEqual(report["disposition"], "evidence_invalid")
                self.assertEqual(len(report["invalid_shards"]), 1)

    def test_failure_is_reproduced_and_not_promoted_to_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            populate(root)
            failed = root / "qa02-c12-shard-1/result.json"
            row = json.loads(failed.read_text())
            row["failed_trials"] = 1
            row["passed_trials"] = 2
            row["disposition"] = "observed_failure"
            row["failures"] = [{"index": 1, "passed": False, "error": "stale owner"}]
            failed.write_text(json.dumps(row), encoding="utf-8")
            report = campaign.aggregate(root, SOURCE_SHA, BINARY_DIGEST, 3, BASE_SEED)
            self.assertEqual(report["disposition"], "observed_failure")
            self.assertEqual(report["failing_shards"], [1])
            self.assertEqual(report["failed_trials"], 1)
            self.assertEqual(report["release_gate_credit"], 0)

    def test_fake_full_coverage_on_early_stop_is_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            populate(root)
            file = root / "qa02-c12-shard-0/result.json"
            row = json.loads(file.read_text())
            row.update(attempted_trials=2, passed_trials=2, disposition="completed_positive")
            file.write_text(json.dumps(row), encoding="utf-8")
            report = campaign.aggregate(root, SOURCE_SHA, BINARY_DIGEST, 3, BASE_SEED)
            self.assertEqual(report["disposition"], "evidence_invalid")

    def test_digest_bound_executable_is_required_before_trials(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fake = root / "qa02"
            fake.write_bytes(b"fake executable")
            with self.assertRaisesRegex(ValueError, "stale, missing or corrupted"):
                campaign.run_shard(executable=fake, source_sha=SOURCE_SHA,
                    binary_sha256=BINARY_DIGEST, trials=3, shard=0,
                    seed=BASE_SEED, work=root / "work")
            with self.assertRaisesRegex(ValueError, "out of bounds"):
                campaign.run_shard(executable=fake, source_sha=SOURCE_SHA,
                    binary_sha256=campaign.checksum(fake), trials=2001,
                    shard=0, seed=BASE_SEED, work=root / "work")

    def test_report_contains_counts_without_release_claims(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            populate(root)
            report = campaign.aggregate(root, SOURCE_SHA, BINARY_DIGEST, 3, BASE_SEED)
            campaign.write_report(root / "campaign.json", report, root / "summary.md")
            saved = json.loads((root / "campaign.json").read_text())
            self.assertEqual(saved["release_gate_credit"], 0)
            summary = (root / "summary.md").read_text()
            self.assertIn("12/12", summary)
            self.assertIn("Release credit: 0", summary)
            self.assertIn(SOURCE_SHA, summary)


if __name__ == "__main__":
    unittest.main()
