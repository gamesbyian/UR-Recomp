"""Pure offline regressions; synthetic ZIPs never represent accepted gameplay."""
from __future__ import annotations
import io
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from tools.art.no_replace_report import publish_text_once

try:
    from tools import hp_science_archive_audit as audit
except (ModuleNotFoundError, ImportError):
    import hp_science_archive_audit as audit

RUN_ID = 41264488130
SHA = "d6eb79fca675aff52744ab4a817afd99115a86b4"
EXE = b"MZ" + bytes(range(256))
FIXTURES = ("1" * 64, "2" * 64)


def run(event="workflow_dispatch"):
    return {"id": RUN_ID, "name": audit.RUN_NAME, "path": audit.RUN_PATH,
            "head_branch": "main", "head_sha": SHA, "event": event,
            "status": "completed", "conclusion": "success",
            "html_url": f"https://github.com/{audit.EXPECTED_REPO}/actions/runs/{RUN_ID}",
            "repository": {"full_name": audit.EXPECTED_REPO}}


def sample(workers=8):
    exe_sha = hashlib.sha256(EXE).hexdigest()
    report = {
        "schema": audit.SCHEMA, "run_id": RUN_ID, "source_sha": SHA,
        "status": "completed_positive", "workers": workers,
        "elapsed_seconds": 201.0, "accepted_cases": workers,
        "attempted_cases": workers, "real_guest_processes": workers * 4,
        "issues": [], "release_gate_credit": 0,
        "original_native_event_credit": 0, "physical_gamepads_tested": False,
        "candidate_identity": {
            "source_commit": SHA, "rom_sha256": audit.ROM_SHA,
            "native_executable_sha256": exe_sha,
            "stock_input_sha256": FIXTURES[0], "stock_script_sha256": FIXTURES[1],
        },
        "per_worker": [{
            "worker": i, "case_count": 1, "shard": i % 2,
            "seed_first": RUN_ID % 10000000 + (i // 2) * 25000000
                          + (i % 2) * 1000003,
            "elapsed_seconds": 198.0,
        } for i in range(workers)],
    }
    report["receipt_sha256"] = audit._hash_json(report)
    binding = {"schema": audit.BINDING_SCHEMA, "source_commit": SHA,
               "executable_sha256": exe_sha, "executable_bytes": len(EXE),
               "release_gate_credit": 0, "physical_windows_accepted": False,
               "original_zip_uploaded": False, "rom_or_player_data_uploaded": False}
    return report, binding


def make_zip(report, binding, *, exe=EXE, extra=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(audit.RECEIPT, json.dumps(report))
        z.writestr(audit.BINDING, json.dumps(binding))
        z.writestr(audit.EXECUTABLE, exe)
        for name, body in (extra or {}).items():
            z.writestr(name, body)
    return stream.getvalue()


class HpScienceArchiveAuditTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "evidence.zip"

    def check(self, *, workers=8, receipt=None, binding=None, exe=EXE,
              metadata=None, extra=None, fixtures=FIXTURES):
        default_receipt, default_binding = sample(workers)
        self.path.write_bytes(make_zip(receipt or default_receipt,
                                      binding or default_binding, exe=exe, extra=extra))
        return audit.audit(self.path, metadata or run(), fixture_sha256=fixtures)

    def test_four_and_eight_workers_each_bind_source_run_executable_and_seeds(self):
        for workers in (4, 8):
            with self.subTest(workers=workers):
                result = self.check(workers=workers)
                self.assertTrue(result["positive_receipt_verified"])
                self.assertEqual(result["workers"], workers)
                self.assertEqual(result["accepted_cases"], workers)
                self.assertEqual(result["real_guest_processes"], workers * 4)
                self.assertTrue(result["fixture_source_rechecked"])
                self.assertEqual(result["release_gate_credit"], 0)

    def test_bad_actions_event_and_identity_rejected(self):
        for mutation in ({"event": "push"}, {"head_branch": "evil"},
                         {"head_sha": "a" * 40}, {"id": RUN_ID + 1},
                         {"path": "another.yml"}, {"conclusion": "failure"},
                         {"repository": {"full_name": "bad/repo"}},
                         {"html_url": "https://other.invalid"}):
            with self.subTest(mutation=mutation), self.assertRaises(audit.AuditError):
                self.check(metadata={**run(), **mutation})

    def test_rehashing_fake_accepted_result_still_fails_cross_checks(self):
        for mutation in (
            {"source_sha": "f" * 40}, {"run_id": RUN_ID + 1},
            {"accepted_cases": 100}, {"release_gate_credit": 1},
            {"issues": [{"reason": "unverified"}]}, {"workers": 4},
        ):
            receipt, binding = sample()
            receipt.update(mutation)
            receipt.pop("receipt_sha256")
            receipt["receipt_sha256"] = audit._hash_json(receipt)
            with self.subTest(mutation=mutation), self.assertRaises(audit.AuditError):
                self.check(receipt=receipt, binding=binding)

    def test_declared_science_wall_horizon_requires_manual_provenance(self):
        # Old source-era receipts deliberately have no horizon claim.
        old = self.check(metadata=run("schedule"))
        self.assertIsNone(old["declared_cohort_wall_seconds_budget"])
        for horizon in (360, 600):
            receipt, binding = sample()
            receipt.pop("receipt_sha256")
            receipt["wall_seconds_budget"] = horizon
            receipt["receipt_sha256"] = audit._hash_json(receipt)
            manual = self.check(receipt=receipt, binding=binding)
            self.assertEqual(manual["declared_cohort_wall_seconds_budget"], horizon)
            if horizon == 360:
                self.assertEqual(self.check(receipt=receipt, binding=binding,
                                            metadata=run("schedule"))[
                                                "declared_cohort_wall_seconds_budget"], 360)
            else:
                with self.assertRaisesRegex(audit.AuditError, "manual dispatch"):
                    self.check(receipt=receipt, binding=binding,
                               metadata=run("schedule"))

    def test_forged_or_unsupported_science_horizon_fails_closed(self):
        for invalid in (None, False, True, 0, 599, 601, 600.0, "600"):
            receipt, binding = sample()
            receipt.pop("receipt_sha256")
            receipt["wall_seconds_budget"] = invalid
            receipt["receipt_sha256"] = audit._hash_json(receipt)
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                    audit.AuditError, "science cohort wall budget"):
                self.check(receipt=receipt, binding=binding)

    def test_wrong_executable_rejected_even_when_zip_crc_passes(self):
        with self.assertRaisesRegex(audit.AuditError, "real executable differs"):
            self.check(exe=EXE + b"tampered")

    def test_corrupted_unsealed_receipt_rejected(self):
        receipt, binding = sample()
        receipt["workers"] = 2
        with self.assertRaisesRegex(audit.AuditError, "self-hash mismatch"):
            self.check(receipt=receipt, binding=binding)

    def test_duplicate_and_malformed_worker_seed_rejected(self):
        for kind in ("duplicate", "seed", "cases"):
            receipt, binding = sample()
            if kind == "duplicate":
                receipt["per_worker"][2]["worker"] = 1
            elif kind == "seed":
                receipt["per_worker"][2]["seed_first"] += 1
            else:
                receipt["per_worker"][2]["case_count"] = 2
            receipt.pop("receipt_sha256")
            receipt["receipt_sha256"] = audit._hash_json(receipt)
            with self.subTest(kind=kind), self.assertRaises(audit.AuditError):
                self.check(receipt=receipt, binding=binding)

    def test_malicious_path_and_wrong_fixtures_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "unsafe archive path"):
            self.check(extra={"../escape.txt": b"no"})
        with self.assertRaisesRegex(audit.AuditError, "fixture hashes"):
            self.check(fixtures=("0" * 64, "2" * 64))

    def test_binary_binding_mismatch_and_archive_identity_rejected(self):
        for mutation in ({"source_commit": "a" * 40},
                         {"executable_sha256": "f" * 64},
                         {"executable_bytes": len(EXE) + 1},
                         {"physical_windows_accepted": True}):
            receipt, binding = sample()
            binding.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(audit.AuditError):
                self.check(receipt=receipt, binding=binding)

    def test_rejects_failed_archive_integrity_without_unpacking(self):
        receipt, binding = sample()
        self.path.write_bytes(make_zip(receipt, binding))
        payload = bytearray(self.path.read_bytes())
        entry = payload.index(EXE)
        payload[entry] ^= 1
        self.path.write_bytes(payload)
        with self.assertRaisesRegex(audit.AuditError, "CRC"):
            audit.audit(self.path, run())

    def test_atomic_publication_rejects_dangling_symlink_existing_and_racing_writer(self):
        out = self.path.parent / "report.json"
        foreign = self.path.parent / "foreign.json"
        try:
            out.symlink_to(foreign)
        except (OSError, NotImplementedError):
            self.skipTest("local symlinks unavailable")
        self.assertFalse(out.exists())
        with self.assertRaises(OSError):
            publish_text_once(out, "safe report")
        self.assertFalse(foreign.exists())
        out.unlink()
        out.write_text("existing-owned-content")
        with self.assertRaises(OSError):
            publish_text_once(out, "new report")
        self.assertEqual(out.read_text(), "existing-owned-content")
        out.unlink()
        publish_text_once(out, "first-complete-report")
        with self.assertRaises(OSError):
            publish_text_once(out, "competing report")
        self.assertEqual(out.read_text(), "first-complete-report")
        source = Path(audit.__file__).read_text()
        self.assertIn("publish_text_once(args.out, output)", source)
        self.assertNotIn("args.out.write_text", source)

    def test_snapshot_hash_and_verified_bytes_cannot_diverge_on_path_replacement(self):
        receipt, binding = sample()
        initial = make_zip(receipt, binding)
        self.path.write_bytes(initial)
        real_check = audit._safe_zip_members
        def replace_path_after_snapshot(z):
            self.path.write_bytes(b"unrelated local bytes")
            return real_check(z)
        with patch.object(audit, "_safe_zip_members", side_effect=replace_path_after_snapshot):
            report = audit.audit(self.path, run(), fixture_sha256=FIXTURES)
        self.assertEqual(report["archive_sha256"], hashlib.sha256(initial).hexdigest())
        self.assertNotEqual(report["archive_sha256"],
                            hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "duplicate JSON field"):
            audit._strict_json(b'{"x": 1, "x": 2}')


if __name__ == "__main__":
    unittest.main()
