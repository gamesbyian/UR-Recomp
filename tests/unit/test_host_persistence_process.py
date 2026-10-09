"""QA-02 multi-process and crash-window persistence acceptance.

Each contender executes the actual host C++ store APIs in a separate OS
process. The crash mode exits inside the production staged-replace helper,
between flushed/closed staging and canonical publication.
"""
import os
import pathlib
import subprocess
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class HostPersistenceProcessTests(unittest.TestCase):
    def test_crash_recovery_and_concurrent_host_artifacts(self):
        with tempfile.TemporaryDirectory() as work:
            root = pathlib.Path(work)
            exe = root / "host-persistence-process"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra",
                    "-Werror", "-pedantic",
                    "-I", str(ROOT / "native/product"),
                    *(str(ROOT / "native/product" / path) for path in (
                        "host_product_state.cpp",
                        "output_resolution_policy.cpp",
                        "modern_racer_identity.cpp",
                        "host_profile_runtime.cpp",
                        "host_profile_state.cpp",
                        "host_profile_store.cpp",
                        "host_profile_catalog.cpp",
                        "host_product_store.cpp",
                    )),
                    str(ROOT / "tests/native/host_persistence_process_tool.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT, check=True,
            )

            def call(family, action, path, value=0):
                return subprocess.run(
                    [str(exe), family, action, str(path), str(value)],
                    cwd=ROOT, capture_output=True,
                )

            def read_value(family, path):
                result = call(family, "read", path)
                self.assertEqual(result.returncode, 0, result.stderr)
                return int(result.stdout.strip())

            for family in ("profile", "host", "catalog"):
                dest = root / (family + ".dat")
                self.assertEqual(call(family, "write", dest, 0).returncode, 0)
                for _round in range(8):
                    processes = [
                        subprocess.Popen(
                            [str(exe), family, "write", str(dest), str(i)],
                            cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        for i in range(8)
                    ]
                    statuses = [proc.communicate()[0] is not None and
                                proc.returncode for proc in processes]
                    self.assertTrue(any(rc == 0 for rc in statuses), statuses)
                    self.assertTrue(all(rc in (0, 3) for rc in statuses), statuses)
                    # A winner's complete serialized payload survives, never
                    # a spliced stream or half an SRAM mirror.
                    self.assertIn(read_value(family, dest),
                                  [i for i, status in enumerate(statuses)
                                   if status == 0])
                    self.assertFalse((root / (family + ".dat.tmp")).exists())
                    self.assertFalse(any(
                        p.name.startswith(".pending-ur" + family + "-")
                        for p in root.iterdir()
                    ), "successful writes clean staging reservations")

                previous = dest.read_bytes()
                # Nonexistent parent simulates a storage error without ever
                # exposing a partial replacement or truncating the prior file.
                bad = root / "missing-parent" / family
                self.assertEqual(call(family, "write", bad, 3).returncode, 3)
                self.assertEqual(dest.read_bytes(), previous)

            profile = root / "profile.dat"
            self.assertEqual(call("profile", "write", profile, 2).returncode, 0)
            incumbent = profile.read_bytes()
            crashed = call("profile", "crash", profile, 7)
            self.assertEqual(crashed.returncode, 77)
            self.assertEqual(profile.read_bytes(), incumbent)
            self.assertEqual(read_value("profile", profile), 2)
            # Simulate a failed fsync / FlushFileBuffers in a fresh process.
            # A false persistence success would destroy a valid SRAM mirror.
            self.assertEqual(call("profile", "syncfail", profile, 6).returncode, 0)
            self.assertEqual(profile.read_bytes(), incumbent)
            self.assertEqual(read_value("profile", profile), 2)
            abandoned = [
                p for p in root.iterdir()
                if p.name.startswith(".pending-urprofile-")
            ]
            self.assertTrue(abandoned, "crash occurred after staging reservation")
            self.assertEqual(call("profile", "write", profile, 5).returncode, 0)
            self.assertEqual(read_value("profile", profile), 5)
            self.assertTrue(all(p.exists() for p in abandoned),
                            "recovery does not delete unrelated crash evidence")

            # Compare-and-swap uses the exact prior disk snapshot rather
            # than autosave_generation alone. Both children load the SAME
            # previous SRAM before either receives the "go" marker.
            cas_path = root / "cas-profile.dat"
            self.assertEqual(call("profile", "cas-create", cas_path, 2).returncode, 0)
            self.assertEqual(call("profile", "cas-create", cas_path, 3).returncode, 6)
            self.assertEqual(read_value("profile", cas_path), 2)

            barrier = root / "barrier"
            barrier.mkdir()
            competing = [
                subprocess.Popen(
                    [str(exe), "profile", "cas-contend",
                     str(cas_path), str(value), str(barrier)],
                    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                for value in (8, 9)
            ]
            deadline = time.monotonic() + 8
            while not all((barrier / ("ready-" + str(value))).exists()
                          for value in (8, 9)):
                self.assertLess(time.monotonic(), deadline,
                                "contending writers failed to reach the barrier")
                time.sleep(0.01)
            (barrier / "go").touch()
            statuses = []
            for child in competing:
                _, stderr = child.communicate(timeout=12)
                statuses.append(child.returncode)
                self.assertIn(child.returncode, (0, 6), stderr)
            self.assertEqual(sorted(statuses), [0, 6], statuses)
            winner = read_value("profile", cas_path)
            self.assertIn(winner, (8, 9))

            # A legitimate same-process rollback may decrease generation,
            # but only if nobody replaced its exact intermediate state.
            self.assertEqual(call("profile", "cas-rollback",
                                  cas_path, 12).returncode, 0)
            self.assertEqual(read_value("profile", cas_path), winner)
            result = subprocess.run(
                [str(exe), "profile", "cas-rollback", str(cas_path),
                 "13", "interleave"],
                cwd=ROOT, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(read_value("profile", cas_path), 14)


if __name__ == "__main__":
    unittest.main()
