"""QA-02 C12: race actual full tournament creation in separate processes.

This is stronger than a file-store-only CAS race: each process creates its
archive and then competes to publish the active event through the complete
production coordinator. The result must be one active winner or fail closed.
"""
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
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


class CoordinatorCreateProcessRaceTests(unittest.TestCase):
    def test_two_creators_cannot_claim_same_active_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "qa02-coordinator-create-race"
            subprocess.run([
                "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-pedantic", "-pthread",
                "-I", str(ROOT / "native/product"),
                "-I", str(ROOT / "native/title"),
                *[str(ROOT / "native/product" / p) for p in SOURCES],
                str(ROOT / "tests/native/qa02_coordinator_create_race_process.cpp"),
                "-o", str(exe),
            ], cwd=ROOT, check=True)

            for trial in range(5):
                user_root = root / ("trial-%02d" % trial)
                barrier = user_root / "barrier"
                barrier.mkdir(parents=True)
                ids = ("b" * 32, "c" * 32)
                children = [
                    subprocess.Popen(
                        [str(exe), "contend", str(user_root), key],
                        cwd=ROOT, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    for key in ids
                ]
                deadline = time.monotonic() + 10
                try:
                    while not all((barrier / ("ready-" + key)).exists()
                                  for key in ids):
                        self.assertLess(time.monotonic(), deadline,
                                        "C12 contenders never reached barrier")
                        time.sleep(0.01)
                    (barrier / "go").touch()
                    statuses = []
                    for child in children:
                        output, error = child.communicate(timeout=20)
                        statuses.append(child.returncode)
                        self.assertIn(child.returncode, (0, 6),
                                      (output, error))
                    self.assertEqual(sorted(statuses), [0, 6], statuses)
                    for _ in range(2):
                        reader = subprocess.run(
                            [str(exe), "verify", str(user_root), ids[0]],
                            cwd=ROOT, capture_output=True, timeout=20,
                        )
                        self.assertEqual(reader.returncode, 0, reader.stderr)
                        self.assertIn(
                            b"QA02_C12_SINGLE_ACTIVE_NO_CREDIT",
                            reader.stdout,
                        )
                finally:
                    for child in children:
                        if child.poll() is None:
                            child.kill()
                            child.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
