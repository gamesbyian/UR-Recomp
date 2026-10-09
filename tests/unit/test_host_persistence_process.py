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

            # Global host settings and active-profile selection are shared
            # across processes. A stale instance must not silently switch
            # another instance's selected racer back to its old value.
            global_host = root / "cas-host.dat"
            self.assertEqual(call("host", "cas-create", global_host, 2).returncode, 0)
            self.assertEqual(call("host", "cas-create", global_host, 3).returncode, 6)
            barrier_host = root / "barrier-host"
            barrier_host.mkdir()
            host_children = [
                subprocess.Popen(
                    [str(exe), "host", "cas-contend",
                     str(global_host), str(value), str(barrier_host)],
                    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                for value in (8, 9)
            ]
            deadline = time.monotonic() + 8
            while not all((barrier_host / ("ready-" + str(value))).exists()
                          for value in (8, 9)):
                self.assertLess(time.monotonic(), deadline,
                                "host writers failed to reach the barrier")
                time.sleep(0.01)
            (barrier_host / "go").touch()
            statuses = []
            for child in host_children:
                _, stderr = child.communicate(timeout=12)
                statuses.append(child.returncode)
                self.assertIn(child.returncode, (0, 6), stderr)
            self.assertEqual(sorted(statuses), [0, 6], statuses)
            self.assertIn(read_value("host", global_host), (8, 9))
            prior_selected = read_value("host", global_host)
            # Failed second-phase SRAM write is permitted to restore only
            # the global selection this process just published.
            self.assertEqual(
                call("host", "cas-rollback", global_host, 11).returncode, 0
            )
            self.assertEqual(read_value("host", global_host), prior_selected)
            # If another game advances the global selection before rollback,
            # its new racer must survive the stale compensating write.
            conflict = subprocess.run(
                [str(exe), "host", "cas-rollback",
                 str(global_host), "12", "interleave"],
                cwd=ROOT, capture_output=True,
            )
            self.assertEqual(conflict.returncode, 0, conflict.stderr)
            self.assertEqual(read_value("host", global_host), 13)

            corrupt_host = root / "corrupt-host.dat"
            corrupt_host.write_text("bad historic state", encoding="utf-8")
            before = corrupt_host.read_bytes()
            self.assertEqual(
                call("host", "cas-create", corrupt_host, 5).returncode, 6
            )
            self.assertEqual(corrupt_host.read_bytes(), before)

            # A catalog CAS failure can delete the just-created profile
            # but cannot unlink its persistent OS-handle lock pathname. An
            # explicit retry must work without adopting unknown old SRAM.
            retry_root = root / "registration-retry"
            self.assertEqual(
                call("profile", "root-reusable", retry_root).returncode, 6
            )
            retry_root.mkdir()
            self.assertEqual(
                call("profile", "root-reusable", retry_root).returncode, 0
            )
            lock_file = retry_root / "host-profile.txt.urmutex"
            lock_file.touch()
            self.assertEqual(
                call("profile", "root-reusable", retry_root).returncode, 0
            )
            unknown_sram = retry_root / "save.srm"
            unknown_sram.write_bytes(b"existing progress")
            self.assertEqual(
                call("profile", "root-reusable", retry_root).returncode, 6
            )
            unknown_sram.unlink()
            abandoned_stage = retry_root / ".pending-urprofile-old"
            abandoned_stage.mkdir()
            self.assertEqual(
                call("profile", "root-reusable", retry_root).returncode, 6
            )
            abandoned_stage.rmdir()
            lock_file.unlink()
            lock_file.mkdir()  # A lock *directory* is never an OS lock file.
            self.assertEqual(
                call("profile", "root-reusable", retry_root).returncode, 6
            )

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
            # Failed catalog registration must never delete the profile
            # after another process has saved newer canonical SRAM.
            self.assertEqual(
                call("profile", "cas-delete-stale",
                     cas_path, 15).returncode, 0
            )
            self.assertEqual(read_value("profile", cas_path), 15)
            self.assertEqual(
                call("profile", "cas-delete", cas_path).returncode, 0
            )
            deleted = call("profile", "read", cas_path)
            self.assertEqual(deleted.returncode, 4)


            # Profile roster lost-update is a separate artifact from SRAM:
            # two different new racers based on an identical pre-save
            # catalogue must not silently replace each other's entry.
            catalog_path = root / "catalog-cas.dat"
            self.assertEqual(call("catalog", "write",
                                  catalog_path, 0).returncode, 0)
            roster_barrier = root / "roster-barrier"
            roster_barrier.mkdir()
            roster_children = [
                subprocess.Popen(
                    [str(exe), "catalog", "cas-roster-contend",
                     str(catalog_path), str(value), str(roster_barrier)],
                    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                for value in (8, 9)
            ]
            deadline = time.monotonic() + 8
            while not all((roster_barrier / ("ready-" + str(value))).exists()
                          for value in (8, 9)):
                self.assertLess(time.monotonic(), deadline,
                                "catalog contenders did not reach barrier")
                time.sleep(0.01)
            (roster_barrier / "go").touch()
            statuses = []
            for child in roster_children:
                _, stderr = child.communicate(timeout=12)
                statuses.append(child.returncode)
                self.assertIn(child.returncode, (0, 6), stderr)
            self.assertEqual(sorted(statuses), [0, 6], statuses)
            result = call("catalog", "cas-roster-read", catalog_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            roster = result.stdout.decode().strip().split()
            self.assertEqual(roster[0], "2")
            self.assertIn("racer", roster)
            self.assertEqual(
                len(set(roster).intersection({"racer-8", "racer-9"})), 1
            )


if __name__ == "__main__":
    unittest.main()
