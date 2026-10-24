"""Offline tests for periodic Vault checkpointing, budgets and source nonpublication."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from tools import vault_scheduled_intake as recurring

NOW = datetime(2026, 10, 23, 21, 0, tzinfo=timezone.utc)
A = "1C57qeOCaNH7EHxVDNZaM6qcy3W7SeCji"
B = "1kULfQIJSV-YJ1lwWBPJAnH6iLtzt5W9d"
C = "1PiSt8K1rQgC27TuMxQ7-aNRvPeyW0Q9C"


def item(file_id, path):
    return {"id": file_id, "path": path, "url": "https://drive.google.com/uc?id=" + file_id}


def archive_result(entry, bytes_=100, unmatched=2):
    return {
        "id": entry["id"], "path": entry["path"],
        "sha256": "a" * 64, "bytes": bytes_,
        "published": False, "integrated": False,
        "zip": {"archive": "a" * 64, "crosswalk": {
            "source_like_members": 3, "exact_blob_occurrences": 1,
            "unmatched_or_unexamined": unmatched,
            "nested_archives_encountered": 0,
        }},
    }


class RecurringVaultTests(unittest.TestCase):
    def listing(self, url):
        self.assertEqual(url, recurring.DEFAULT_FOLDER)
        return [
            item(A, "a-first.zip"), item(B, "b-second.zip"),
            item(C, "notes.txt"),
        ]

    def test_first_cycle_writes_complete_metadata_only_checkpoint(self):
        observed = []
        def downloader(entry, out, git_tree, *, stage):
            self.assertFalse(stage)
            observed.append(entry["id"])
            return archive_result(entry)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "first"
            report, queue = recurring.run_cycle(
                out=out, enumerator=self.listing, downloader=downloader,
                git_tree=b"", max_files=2, max_total_bytes=1000, now=NOW,
            )
            self.assertEqual(observed, [A, B])
            self.assertEqual(report["listed_files"], 3)
            self.assertEqual(report["downloaded_bytes"], 200)
            self.assertEqual(report["remaining_due"], 1)
            self.assertEqual(queue["needs_first_audit"][0]["id"], C)
            self.assertEqual(len(queue["needs_engineering_review"]), 2)
            self.assertFalse(queue["automatic_publication_authorized"])
            self.assertFalse(report["automatic_publication_authorized"])
            self.assertFalse((out / "downloads").exists())
            state = json.loads((out / "checkpoint.json").read_text())
            self.assertEqual(set(state["items"]), {A, B})
            self.assertNotIn("source", json.dumps(state).lower().replace("source_like_members",""))

    def test_checkpoint_skips_fresh_and_resumes_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            recurring.run_cycle(
                out=first, enumerator=self.listing,
                downloader=lambda entry, out, tree, stage=False: archive_result(entry),
                git_tree=b"", max_files=1, now=NOW,
            )
            visited = []
            second, _ = recurring.run_cycle(
                out=Path(tmp) / "second", previous=first / "checkpoint.json",
                enumerator=self.listing,
                downloader=lambda entry, out, tree, stage=False:
                    (visited.append(entry["id"]) or archive_result(entry)),
                git_tree=b"", max_files=2, now=NOW + timedelta(hours=6),
            )
            self.assertEqual(visited, [B, C])
            self.assertEqual(second["previously_verified_skipped"], 1)
            self.assertEqual(second["verified_total"], 3)
            third, _ = recurring.run_cycle(
                out=Path(tmp) / "third",
                previous=Path(tmp) / "second" / "checkpoint.json",
                enumerator=self.listing,
                downloader=lambda *a, **k: self.fail("unexpected repeat"),
                git_tree=b"", now=NOW + timedelta(days=1),
            )
            self.assertEqual(len(third["processed"]), 0)
            self.assertEqual(third["previously_verified_skipped"], 3)

    def test_refresh_and_force_selected_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            recurring.run_cycle(
                out=first, enumerator=self.listing,
                downloader=lambda entry, out, tree, stage=False: archive_result(entry),
                git_tree=b"", max_files=3, now=NOW,
            )
            due, skipped = recurring.make_queue(
                self.listing(recurring.DEFAULT_FOLDER),
                recurring.read_checkpoint(first / "checkpoint.json")["items"],
                NOW + timedelta(days=15), 14,
            )
            self.assertEqual(len(due), 3)
            self.assertEqual(len(skipped), 0)
            observed = []
            report, _ = recurring.run_cycle(
                out=Path(tmp) / "probe", previous=first / "checkpoint.json",
                enumerator=self.listing, forced_id=B,
                downloader=lambda entry, out, tree, stage=False:
                    (observed.append(entry["id"]) or archive_result(entry)),
                git_tree=b"", now=NOW + timedelta(hours=1),
            )
            self.assertEqual(observed, [B])
            self.assertEqual(report["queued_before_batch"], 1)

    def test_failed_archive_does_not_checkpoint_and_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "failure"
            def downloader(entry, *a, **kw):
                if entry["id"] == A:
                    raise ValueError("unsafe ZIP member")
                return archive_result(entry)
            report, queue = recurring.run_cycle(
                out=out, enumerator=self.listing, downloader=downloader,
                git_tree=b"", max_files=2, now=NOW,
            )
            self.assertEqual(report["errors"][0]["id"], A)
            self.assertEqual(report["remaining_due"], 2)
            self.assertIn(A, [item["id"] for item in queue["download_errors"]])
            checkpoint = recurring.read_checkpoint(out / "checkpoint.json")
            self.assertNotIn(A, checkpoint["items"])
            self.assertIn(A, checkpoint["failures"])
            visited = []
            recurring.run_cycle(
                out=Path(tmp) / "next", previous=out / "checkpoint.json",
                enumerator=self.listing, max_files=1, git_tree=b"",
                downloader=lambda entry, out, tree, stage=False:
                    (visited.append(entry["id"]) or archive_result(entry)),
                now=NOW + timedelta(hours=6),
            )
            self.assertEqual(visited, [C], "failed ZIP must not starve fresh work")

    def test_budget_deferred_not_marked_as_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "budget"
            report, _ = recurring.run_cycle(
                out=out, enumerator=self.listing,
                downloader=lambda entry, out, tree, stage=False:
                    archive_result(entry, bytes_=80),
                git_tree=b"", max_files=3, max_total_bytes=100, now=NOW,
            )
            self.assertEqual(len(report["processed"]), 1)
            self.assertEqual(report["remaining_due"], 2)
            self.assertTrue(any(d["reason"].startswith("batch_byte_limit")
                                for d in report["deferred"]))
            self.assertEqual(len(recurring.read_checkpoint(out / "checkpoint.json")["items"]), 1)

    def test_scheduled_workflow_restores_checkpoints_and_uses_bounded_twelve_archive_batch(self):
        workflow = (Path(__file__).resolve().parents[2]
                    / '.github/workflows/vault-recurring-intake.yml').read_text()
        self.assertIn("github.event_name == 'schedule' || inputs.scope == 'both'", workflow)
        self.assertIn("github.event_name == 'schedule' && '12'", workflow)
        self.assertIn("options: ['1', '2', '3', '6', '12']", workflow)
        self.assertEqual(recurring.MAX_BATCH, 12)
        self.assertIn("MAX_MIB: ${{ github.event_name == 'pull_request' && '32' || '64' }}", workflow)
        self.assertIn('vault-recurring-state-${{ matrix.scope }}', workflow)

    def test_oversized_failure_cools_down_without_losing_pending_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            def too_large(entry, *args, **kwargs):
                raise ValueError("download exceeds single-file byte budget")
            failed, _ = recurring.run_cycle(
                out=first, enumerator=self.listing, downloader=too_large,
                git_tree=b"", max_files=1, now=NOW,
            )
            self.assertEqual(failed["errors"], [])
            self.assertEqual([x["id"] for x in failed["retry_cooldown"]], [A])
            self.assertEqual(failed["retry_cooldown"][0]["retry_after"],
                             (NOW + timedelta(days=14)).isoformat())
            self.assertNotIn(A, recurring.read_checkpoint(
                first / "checkpoint.json")["items"])
            self.assertIn(A, recurring.read_checkpoint(
                first / "checkpoint.json")["failures"])
            seen = []
            resumed, queue = recurring.run_cycle(
                out=Path(tmp) / "second", previous=first / "checkpoint.json",
                enumerator=self.listing, git_tree=b"", max_files=3,
                downloader=lambda entry, out, tree, stage=False:
                    (seen.append(entry["id"]) or archive_result(entry)),
                now=NOW + timedelta(hours=6),
            )
            self.assertEqual(seen, [B, C])
            self.assertEqual(resumed["remaining_due"], 1)
            self.assertEqual(resumed["errors"], [])
            self.assertEqual(resumed["retry_cooldown"][0]["id"], A)
            self.assertEqual(queue["retry_cooldown"][0]["reason"], "oversize_retry_cooldown")
            self.assertNotIn(A, resumed["processed"])
            self.assertNotIn(A, recurring.read_checkpoint(
                Path(tmp) / "second" / "checkpoint.json")["items"])
            forced = []
            recurring.run_cycle(
                out=Path(tmp) / "forced", previous=first / "checkpoint.json",
                enumerator=self.listing, git_tree=b"", forced_id=A,
                downloader=lambda entry, out, tree, stage=False:
                    (forced.append(entry["id"]) or archive_result(entry)),
                now=NOW + timedelta(hours=6),
            )
            self.assertEqual(forced, [A], "explicit probe bypasses cooldown")
            expired = []
            recurring.run_cycle(
                out=Path(tmp) / "expired", previous=first / "checkpoint.json",
                enumerator=self.listing, git_tree=b"", max_files=3,
                downloader=lambda entry, out, tree, stage=False:
                    (expired.append(entry["id"]) or archive_result(entry)),
                now=NOW + timedelta(days=15),
            )
            self.assertIn(A, expired, "14-day cooldown must expire")

    def test_first_six_attempts_count_budget_cooldowns_but_not_red_transport(self):
        observed = []
        def downloader(entry, out, tree, stage=False):
            observed.append(entry["id"])
            if entry["id"] == A:
                raise ValueError("download exceeds single-file byte budget")
            if entry["id"] == B:
                raise ValueError("expanded ZIP budget exceeded")
            return archive_result(entry)
        with tempfile.TemporaryDirectory() as tmp:
            report, queue = recurring.run_cycle(
                out=Path(tmp) / "first", enumerator=self.listing,
                downloader=downloader, git_tree=b"", now=NOW,
                max_files=3,
            )
            self.assertEqual(observed, [A, B, C])
            self.assertEqual(report["errors"], [])
            self.assertEqual(len(report["processed"]), 1)
            self.assertEqual(report["processed"][0]["id"], C)
            self.assertEqual([x["id"] for x in report["retry_cooldown"]],
                             [A, B])
            self.assertEqual(len(queue["retry_cooldown"]), 2)
            self.assertEqual(report["remaining_due"], 2)
            ck = recurring.read_checkpoint(Path(tmp) / "first/checkpoint.json")
            self.assertEqual(set(ck["items"]), {C})
            self.assertEqual(set(ck["failures"]), {A, B})
            # The next run proceeds without new errors or repeated downloads.
            again = []
            nxt, _ = recurring.run_cycle(
                out=Path(tmp) / "next",
                previous=Path(tmp) / "first/checkpoint.json",
                enumerator=self.listing, git_tree=b"",
                downloader=lambda item, *args, **kwargs: (
                    again.append(item["id"]) or archive_result(item)),
                now=NOW + timedelta(hours=6),
            )
            self.assertEqual(again, [])
            self.assertEqual(nxt["errors"], [])
            self.assertEqual(len(nxt["retry_cooldown"]), 2)

    def test_explicit_oversize_probe_is_a_hard_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, _ = recurring.run_cycle(
                out=Path(tmp) / "probe", enumerator=self.listing,
                forced_id=A, git_tree=b"",
                downloader=lambda *args, **kwargs: (
                    (_ for _ in ()).throw(
                        ValueError("download exceeds single-file byte budget"))),
                now=NOW,
            )
            self.assertEqual(len(report["errors"]), 1)
            self.assertEqual(report["errors"][0]["id"], A)
            self.assertEqual(report["retry_cooldown"], [])

    def test_untrusted_error_text_cannot_masquerade_as_budget_sentinel(self):
        self.assertFalse(recurring.is_deterministic_budget_error(
            "gdown failed on file named download exceeds single-file byte budget"))
        self.assertFalse(recurring.is_deterministic_budget_error(
            "unsafe ZIP member: expanded ZIP budget exceeded"))
        with tempfile.TemporaryDirectory() as tmp:
            report, _ = recurring.run_cycle(
                out=Path(tmp) / "hostile", enumerator=self.listing,
                git_tree=b"", max_files=1, now=NOW,
                downloader=lambda *a, **k: (_ for _ in ()).throw(
                    OSError("download exceeds single-file byte budget")),
            )
            self.assertEqual(len(report["errors"]), 1)
            self.assertEqual(report["retry_cooldown"], [])
            self.assertIn(A, recurring.read_checkpoint(
                Path(tmp) / "hostile/checkpoint.json")["failures"])

    def test_expanded_and_nested_zip_budget_failures_share_retry_cooldown(self):
        for error in ("expanded ZIP budget exceeded",
                      "nested ZIP exceeds byte budget"):
            with self.subTest(error=error):
                previous = {"path": "a-first.zip", "error": error,
                            "last_attempt": NOW.isoformat()}
                due = recurring.oversized_retry_after(
                    previous, item(A, "a-first.zip"),
                    NOW + timedelta(hours=6), 14)
                self.assertIsNotNone(due)
                self.assertIsNone(recurring.oversized_retry_after(
                    previous, item(A, "renamed.zip"),
                    NOW + timedelta(hours=6), 14))
                self.assertIsNone(recurring.oversized_retry_after(
                    previous, item(A, "a-first.zip"),
                    NOW + timedelta(days=15), 14))

    def test_member_review_fingerprints_survive_checkpoint_carry_forward(self):
        lead = {"member": "payload/tools/new.py", "sha256": "b" * 64,
                "bytes": 17, "kind": "source_or_test",
                "status": "unmatched_needs_review"}
        def downloader(entry, out, tree, stage=False):
            result = archive_result(entry)
            result["zip"]["review_leads"] = [lead]
            result["zip"]["review_leads_filtered_or_truncated"] = 2
            return result
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            recurring.run_cycle(
                out=first, enumerator=self.listing, downloader=downloader,
                git_tree=b"", max_files=1, now=NOW,
            )
            checkpoint = recurring.read_checkpoint(first / "checkpoint.json")
            self.assertEqual(checkpoint["items"][A]["review_leads"], [lead])
            second, queue = recurring.run_cycle(
                out=Path(tmp) / "second", previous=first / "checkpoint.json",
                enumerator=self.listing, downloader=downloader,
                git_tree=b"", max_files=1, now=NOW + timedelta(hours=6),
            )
            self.assertEqual(second["previously_verified_skipped"], 1)
            self.assertEqual(queue["needs_engineering_review"][0]["review_leads"], [lead])
            self.assertEqual(queue["needs_engineering_review"][0][
                "review_leads_filtered_or_truncated"], 2)
            checkpoint["items"][A]["review_leads"][0]["sha256"] = "invalid"
            damaged = Path(tmp) / "tampered.json"
            damaged.write_text(json.dumps(checkpoint))
            with self.assertRaisesRegex(ValueError, "invalid checkpoint review lead"):
                recurring.read_checkpoint(damaged)

    def test_workflow_failure_summary_uses_stable_categories_and_ids(self):
        categories = {
            "download exceeds single-file byte budget": "archive-size-budget",
            "expanded ZIP budget exceeded": "expanded-zip-budget",
            "nested ZIP exceeds byte budget": "nested-zip-budget",
            "unsafe ZIP member": "unsafe-archive-member",
            "invalid or corrupt source ZIP": "invalid-archive",
            "gdown: temporary failure": "download-or-inspection-error",
        }
        for detail, category in categories.items():
            with self.subTest(detail=detail):
                self.assertEqual(recurring.classify_intake_error(detail), category)
        self.assertEqual(recurring.classify_intake_error(
            "bad raw markdown in filename ](https://invalid.example)"),
            "download-or-inspection-error")
        workflow = (Path(__file__).resolve().parents[2] /
                    ".github/workflows/vault-recurring-intake.yml").read_text()
        self.assertIn("Failed Drive ID", workflow)
        self.assertIn("Deferred Drive ID", workflow)
        self.assertIn("oversized archives cooling down", workflow)
        self.assertIn("ID_PATTERN.fullmatch(drive_id)", workflow)
        self.assertIn("classify_intake_error(error.get", workflow)

    def test_invalid_prior_and_empty_inventory_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prior.json"
            path.write_text('{"schema":"wrong","items":{}}')
            with self.assertRaisesRegex(ValueError, "incompatible"):
                recurring.read_checkpoint(path)
            with self.assertRaisesRegex(ValueError, "empty public folder"):
                recurring.run_cycle(
                    out=Path(tmp) / "out", enumerator=lambda url: [],
                    git_tree=b"",
                )


if __name__ == "__main__":
    unittest.main()
