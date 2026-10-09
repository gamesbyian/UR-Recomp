"""QA-02: real OS-process death at immutable run and receipt boundaries.

A separate compiled production-store executable publishes real canonical
artifacts, calls std::_Exit between artifacts, and is relaunched with only
its on-disk root. This is process-kill evidence, not a power-loss witness.
"""
import pathlib
import subprocess
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCES = (
    "modern_racer_identity.cpp",
    "host_profile_runtime.cpp",
    "host_product_state.cpp",
    "output_resolution_policy.cpp",
    "completed_run_record.cpp",
    "completed_run_store.cpp",
    "local_multiplayer_match_binding.cpp",
    "multiplayer_match_record.cpp",
    "local_tournament_session_store.cpp",
    "local_tournament_fixture_launch_store.cpp",
    "local_tournament_result_link_store.cpp",
    "local_tournament_session_coordinator.cpp",
)


class FixtureHardkillProcessTests(unittest.TestCase):
    def test_c14_c15_durable_result_boundaries_across_real_process_death(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            exe = root / "qa02-fixture-hardkill"
            cmd = [
                "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-pedantic", "-pthread",
                "-I", str(ROOT / "native/product"),
                "-I", str(ROOT / "native/title"),
                *[str(ROOT / "native/product" / name) for name in SOURCES],
                str(ROOT / "tests/native/qa02_fixture_hardkill_process.cpp"),
                "-o", str(exe),
            ]
            subprocess.run(cmd, check=True, cwd=ROOT)
            user_root = root / "player-data"

            def call(action, expected):
                result = subprocess.run(
                    [str(exe), action, str(user_root)],
                    cwd=ROOT, capture_output=True, timeout=20,
                )
                self.assertEqual(
                    result.returncode, expected,
                    (action, result.stdout.decode(errors="replace"),
                     result.stderr.decode(errors="replace")),
                )
                return result

            instance = "a" * 32
            tournament = user_root / "local-tournaments" / instance
            receipt = tournament / "fixtures" / "fixture-0.urfixture"
            pending = tournament / "pending.urlaunch"
            records = user_root / "multiplayer-runs"

            # C09 uses its own complete event namespace. The pair writer
            # exits inside its REAL sidecar-claimed/pre-run publication hook.
            # A fresh reader must see no public run, PB or fixture credit.
            c09_root = root / "c09-player-data"
            c09 = subprocess.run(
                [str(exe), "kill-c09", str(c09_root)], cwd=ROOT,
                capture_output=True, timeout=20,
            )
            self.assertEqual(c09.returncode, 79, c09.stderr)
            orphan_records = c09_root / "multiplayer-runs"
            self.assertEqual(len(list(orphan_records.glob("*.urrun"))), 0)
            self.assertEqual(len(list(orphan_records.glob("*.urmatch"))), 1)
            for _ in range(2):
                check = subprocess.run(
                    [str(exe), "verify-c09", str(c09_root)], cwd=ROOT,
                    capture_output=True, timeout=20,
                )
                self.assertEqual(check.returncode, 0, check.stderr)
                self.assertIn(b"QA02_C09_NO_RUN_NO_CREDIT", check.stdout)
            recovered = subprocess.run(
                [str(exe), "recover-c09", str(c09_root)], cwd=ROOT,
                capture_output=True, timeout=20,
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertIn(b"QA02_C09_LATER_VALID_RETRY", recovered.stdout)
            self.assertEqual(len(list(orphan_records.glob("*.urrun"))), 1)
            self.assertEqual(len(list(orphan_records.glob("*.urmatch"))), 2)
            verify_credit = subprocess.run(
                [str(exe), "verify-c15", str(c09_root)], cwd=ROOT,
                capture_output=True, timeout=20,
            )
            self.assertEqual(verify_credit.returncode, 0, verify_credit.stderr)

            # J-07 process-level overlap: old window has a valid completed
            # saved pair, but a second window supersedes its pending token.
            # Only the NEW durable checkpoint owner may claim the receipt.
            overlap = root / "same-event-two-windows"
            seeded = subprocess.run(
                [str(exe), "seed-overlap", str(overlap)], cwd=ROOT,
                capture_output=True, timeout=20,
            )
            self.assertEqual(seeded.returncode, 0, seeded.stderr)
            old = subprocess.Popen(
                [str(exe), "contend-old", str(overlap)], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            new = None
            try:
                deadline = time.monotonic() + 10
                while not (overlap / "barrier" / "old-ready").exists():
                    self.assertLess(time.monotonic(), deadline,
                                    "old game never armed its exact attempt")
                    time.sleep(0.01)
                new = subprocess.Popen(
                    [str(exe), "contend-new", str(overlap)], cwd=ROOT,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                out_old, err_old = old.communicate(timeout=20)
                self.assertEqual(old.returncode, 0, err_old)
                self.assertIn(b"QA02_LIVE_OWNER_COMMITTED", out_old)
                out_new, err_new = new.communicate(timeout=20)
                self.assertEqual(new.returncode, 0, err_new)
                self.assertIn(b"QA02_BUSY_AND_STALE_RETRY_REJECTED", out_new)
            finally:
                for child in (old, new):
                    if child and child.poll() is None:
                        child.kill()
                        child.communicate(timeout=5)
            overlap_records = overlap / "multiplayer-runs"
            self.assertEqual(len(list(overlap_records.glob("*.urrun"))), 1)
            self.assertEqual(
                len(list(overlap_records.glob("*.urrun.urmatch"))), 1)
            overlap_receipts = list(
                (overlap / "local-tournaments").glob(
                    "*/fixtures/fixture-0.urfixture"))
            self.assertEqual(len(overlap_receipts), 1)
            restored_overlap = subprocess.run(
                [str(exe), "verify-c15", str(overlap)], cwd=ROOT,
                capture_output=True, timeout=20,
            )
            self.assertEqual(restored_overlap.returncode, 0,
                             restored_overlap.stderr)
            self.assertIn(
                b"QA02_C15_SINGLE_RECEIPT_SINGLE_AWARD",
                restored_overlap.stdout,
            )

            # A dead owner must release its *OS handle*, not rely on
            # timeout/pid cleanup. An explicit new attempt uses fresh token,
            # leaves the old saved run as ordinary Records, and credits only
            # the new real fixture result.
            dead_root = root / "dead-fixture-owner"
            died = subprocess.run(
                [str(exe), "owner-crash", str(dead_root)], cwd=ROOT,
                capture_output=True, timeout=20,
            )
            self.assertEqual(died.returncode, 81, died.stderr)
            self.assertTrue((
                dead_root / "local-tournaments" / instance /
                "pending.urlaunch").exists())
            self.assertEqual(
                len(list((dead_root / "multiplayer-runs").glob("*.urrun"))),
                1,
            )
            retired = subprocess.run(
                [str(exe), "retry-owner-crash", str(dead_root)], cwd=ROOT,
                capture_output=True, timeout=20,
            )
            self.assertEqual(retired.returncode, 0, retired.stderr)
            self.assertIn(b"QA02_CRASH_RELEASED_AND_RETRIED", retired.stdout)
            self.assertEqual(
                len(list((dead_root / "multiplayer-runs").glob("*.urrun"))),
                2,
            )
            verified_dead = subprocess.run(
                [str(exe), "verify-c15", str(dead_root)], cwd=ROOT,
                capture_output=True, timeout=20,
            )
            self.assertEqual(verified_dead.returncode, 0,
                             verified_dead.stderr)

            # Stronger than std::_Exit: the OS test controller forcibly
            # terminates an owner that is demonstrably still alive while
            # holding the fixture lease. No destructor/normal release runs.
            hard_root = root / "hard-killed-fixture-owner"
            owner = subprocess.Popen(
                [str(exe), "owner-hold", str(hard_root)], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            try:
                deadline = time.monotonic() + 12
                marker = hard_root / "barrier" / "owner-live"
                while not marker.exists():
                    self.assertIsNone(
                        owner.poll(), "owner died before acquiring live lease"
                    )
                    self.assertLess(time.monotonic(), deadline,
                                    "live OS owner did not reach kill barrier")
                    time.sleep(0.01)
                self.assertIsNone(owner.poll())
                owner.kill()  # SIGKILL / TerminateProcess, not a polite exit
                owner.communicate(timeout=10)
                self.assertNotEqual(owner.returncode, 0)
            finally:
                if owner.poll() is None:
                    owner.kill()
                    owner.communicate(timeout=5)
            owner_data = hard_root / "multiplayer-runs"
            self.assertEqual(len(list(owner_data.glob("*.urrun"))), 1)
            recovered = subprocess.run(
                [str(exe), "retry-owner-crash", str(hard_root)],
                cwd=ROOT, capture_output=True, timeout=20,
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertEqual(len(list(owner_data.glob("*.urrun"))), 2)
            verified = subprocess.run(
                [str(exe), "verify-c15", str(hard_root)],
                cwd=ROOT, capture_output=True, timeout=20,
            )
            self.assertEqual(verified.returncode, 0, verified.stderr)


            # QA-03: complete TWO different tournament formats, fixture by
            # fixture, with *every* credit performed in a new OS process.
            # These exercise durable coordinator/Records semantics. They are
            # genuine saved 2P pair fixtures, not proof of a guest-played
            # controller/Windows tournament.
            for create_action, total, verify_action in (
                ("qa03-create-duel", 3, "qa03-verify-duel"),
                ("qa03-create-round-robin", 6,
                 "qa03-verify-round-robin"),
            ):
                journey = root / create_action

                def step(action):
                    result = subprocess.run(
                        [str(exe), action, str(journey)],
                        cwd=ROOT, capture_output=True, timeout=20,
                    )
                    self.assertEqual(
                        result.returncode, 0,
                        (action, result.stdout.decode(errors="replace"),
                         result.stderr.decode(errors="replace")),
                    )
                    return result

                self.assertIn(
                    b"QA03_CREATED_UNPLAYED",
                    step(create_action).stdout,
                )
                self.assertIn(
                    b"QA03_CANCELLED_WITHOUT_CREDIT",
                    step("qa03-cancel-next").stdout,
                )
                records_root = journey / "multiplayer-runs"
                self.assertEqual(len(list(records_root.glob("*.urrun"))), 0)
                receipts_root = journey / "local-tournaments" / instance / "fixtures"
                for index in range(total):
                    self.assertIn(
                        f"QA03_CREDITED_FIXTURE {index}".encode(),
                        step("qa03-credit-next").stdout,
                    )
                    self.assertEqual(
                        len(list(records_root.glob("*.urrun"))), index + 1,
                        "each fresh process adds exactly one durable run",
                    )
                    self.assertEqual(
                        len(list(receipts_root.glob("fixture-*.urfixture"))),
                        index + 1,
                        "each fixture credited once, never inferred from Records",
                    )
                for _ in range(2):
                    self.assertIn(
                        b"QA03_COMPLETED_RESTORED_STANDINGS_HISTORY_RECORDS",
                        step(verify_action).stdout,
                    )
                self.assertIn(
                    b"QA03_REPLACED_WITH_COMPLETED_HISTORY_PRESERVED",
                    step("qa03-replace-completed").stdout,
                )
                self.assertEqual(
                    len(list(records_root.glob("*.urrun"))), total,
                    "replacing active event preserves old Records pairs",
                )
                self.assertEqual(
                    len(list(receipts_root.glob("fixture-*.urfixture"))),
                    total,
                    "replacing active event preserves immutable receipts",
                )


            # Recover a 3-player event AFTER its first credited fixture.
            # The second owner's process dies after real run+match publication
            # but before receipt claim. The first result must survive while
            # the orphan pair remains ordinary Records, not tournament points.
            interrupted = root / "qa03-midseries-c14"

            def resume(action, expected=0):
                result = subprocess.run(
                    [str(exe), action, str(interrupted)],
                    cwd=ROOT, capture_output=True, timeout=20,
                )
                self.assertEqual(
                    result.returncode, expected,
                    (action, result.stdout.decode(errors="replace"),
                     result.stderr.decode(errors="replace")),
                )
                return result

            resume("qa03-create-round-robin")
            self.assertIn(
                b"QA03_CREDITED_FIXTURE 0",
                resume("qa03-credit-next").stdout,
            )
            resume("qa03-kill-midseries", 82)
            int_records = interrupted / "multiplayer-runs"
            int_receipts = interrupted / "local-tournaments" / instance / "fixtures"
            self.assertEqual(len(list(int_records.glob("*.urrun"))), 2)
            self.assertEqual(
                len(list(int_receipts.glob("fixture-*.urfixture"))), 1,
                "a saved run without receipt never awards the second leg",
            )
            for index in range(1, 6):
                self.assertIn(
                    f"QA03_CREDITED_FIXTURE {index}".encode(),
                    resume("qa03-credit-next").stdout,
                )
            self.assertIn(
                b"QA03_COMPLETED_RESTORED_STANDINGS_HISTORY_RECORDS",
                resume("qa03-verify-round-robin-interrupted").stdout,
            )
            self.assertEqual(len(list(int_records.glob("*.urrun"))), 7)
            self.assertEqual(
                len(list(int_receipts.glob("fixture-*.urfixture"))), 6,
                "all six fixtures have one immutable receipt after takeover",
            )
            resume("qa03-replace-completed")

            call("kill-c14", 77)
            pair_before = list(records.glob("*.urrun"))
            self.assertEqual(len(pair_before), 1)
            self.assertTrue((pathlib.Path(str(pair_before[0]) + ".urmatch")).is_file())
            self.assertFalse(receipt.exists())
            c14 = call("verify-c14", 0)
            self.assertIn(b"QA02_C14_ZERO_CREDIT", c14.stdout)
            self.assertTrue(pending.is_file())
            # Two independent launches cannot manufacture fixture credit
            # from a saved pair in an abandoned first attempt.
            call("verify-c14", 0)

            call("kill-c15", 78)
            pairs_after = list(records.glob("*.urrun"))
            self.assertEqual(len(pairs_after), 2)
            self.assertEqual(
                len(list(records.glob("*.urrun.urmatch"))), 2,
                "both matches must remain bound to complete run files",
            )
            self.assertTrue(receipt.is_file())
            self.assertTrue(pending.is_file(),
                            "test killed before pending retirement")
            original_receipt = receipt.read_bytes()
            original_pending = pending.read_bytes()
            for _ in range(3):
                c15 = call("verify-c15", 0)
                self.assertIn(
                    b"QA02_C15_SINGLE_RECEIPT_SINGLE_AWARD", c15.stdout)
                self.assertEqual(receipt.read_bytes(), original_receipt)
                self.assertEqual(pending.read_bytes(), original_pending)

            # Corrupt only the published authority, retaining run evidence:
            # a fresh reader must fail closed rather than count the saved pair.
            receipt.write_bytes(b"CORRUPTED-IMMUTABLE-RECEIPT")
            rejected = call("verify-corrupt", 0)
            self.assertIn(b"QA02_CORRUPT_RECEIPT_REJECTED", rejected.stdout)
            self.assertEqual(
                receipt.read_bytes(), b"CORRUPTED-IMMUTABLE-RECEIPT")
            self.assertEqual(pending.read_bytes(), original_pending)
            receipt.write_bytes(original_receipt)
            call("verify-c15", 0)


if __name__ == "__main__":
    unittest.main()
