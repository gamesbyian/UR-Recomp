"""QA-02: competing tournament creators must not replace an unseen active event."""
import pathlib
import subprocess
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class TournamentActiveSessionCasTests(unittest.TestCase):
    def test_two_processes_only_one_active_pointer_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            exe = root / "tournament-active-cas"
            subprocess.run([
                "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-pedantic", "-I", str(ROOT / "native/product"),
                "-I", str(ROOT / "native/title"),
                str(ROOT / "native/product/local_tournament_session_store.cpp"),
                str(ROOT / "tests/native/local_tournament_active_session_cas_process.cpp"),
                "-o", str(exe),
            ], cwd=ROOT, check=True)
            file = root / "active.urtournament"
            barrier = root / "barrier"
            barrier.mkdir()

            def invocation(mode, instance):
                return [str(exe), mode, str(file), instance, str(barrier)]

            subprocess.run(
                invocation("seed", "a" * 32), cwd=ROOT, check=True
            )
            racers = [
                subprocess.Popen(
                    invocation("contend", letter * 32),
                    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                for letter in "bc"
            ]
            cutoff = time.monotonic() + 8
            while not all((barrier / ("ready-" + l)).exists() for l in "bc"):
                self.assertLess(time.monotonic(), cutoff,
                                "competitors failed to load common prior session")
                time.sleep(0.01)
            (barrier / "go").touch()
            statuses = []
            for process in racers:
                _, stderr = process.communicate(timeout=12)
                statuses.append(process.returncode)
                self.assertIn(process.returncode, (0, 6), stderr.decode())
            self.assertEqual(sorted(statuses), [0, 6], statuses)
            subprocess.run(
                invocation("verify", "a" * 32),
                cwd=ROOT, check=True,
            )
            # When the active record is intentionally corrupted, a fresh
            # create-only attempt must NOT reset it to an empty event.
            before = b"invalid active tournament bytes"
            file.write_bytes(before)
            attempt = subprocess.run(
                invocation("seed", "b" * 32), cwd=ROOT,
                capture_output=True,
            )
            self.assertEqual(attempt.returncode, 4)
            self.assertEqual(file.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
