"""QA-02: real OS-process death at immutable run and receipt boundaries.

A separate compiled production-store executable publishes real canonical
artifacts, calls std::_Exit between artifacts, and is relaunched with only
its on-disk root. This is process-kill evidence, not a power-loss witness.
"""
import pathlib
import subprocess
import tempfile
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
