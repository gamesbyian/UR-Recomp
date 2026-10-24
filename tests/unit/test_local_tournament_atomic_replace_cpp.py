import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class TournamentMutableStagingTests(unittest.TestCase):
    def test_concurrent_mutable_state_writes_remain_whole(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "local-tournament-atomic-replace"
            subprocess.run(
                ["g++", "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-pthread",
                 "-I", str(ROOT / "native/product"),
                 str(ROOT / "tests/native/local_tournament_atomic_replace_test.cpp"),
                 "-o", str(exe)], check=True, cwd=ROOT)
            subprocess.run([str(exe)], check=True, cwd=ROOT)

    def test_live_tournament_writers_use_reserved_staging(self):
        for filename, family, writer in [
            ("local_tournament_session_store.cpp", "urtournament",
             "write_host_replace_staged"),
            ("local_tournament_fixture_launch_store.cpp", "urlaunch",
             "write_host_replace_staged"),
        ]:
            code = (ROOT / "native/product" / filename).read_text()
            self.assertIn(writer + "(", code)
            self.assertIn('"' + family + '"', code)
            self.assertNotIn('path + ".tmp"', code)

        # Both session and launch stores must give their lock and atomic
        # writer the same native UTF-8-converted path. A narrow-path overload
        # would regress Unicode profile roots on Windows even with staging.
        session = (ROOT / "native/product" /
                   "local_tournament_session_store.cpp").read_text()
        self.assertIn("TournamentLaunchPathLock lock(host_native_path_from_utf8(path));",
                      session)
        self.assertIn('write_host_replace_staged(host_native_path_from_utf8(path), encoded, "urtournament")',
                      session)
        self.assertIn('_wfopen(native_path.c_str(), L"rb")', session)

        launch = (ROOT / "native/product" /
                  "local_tournament_fixture_launch_store.cpp").read_text()
        self.assertIn("const auto native_path = host_native_path_from_utf8(path);",
                      launch)
        self.assertIn("TournamentLaunchPathLock lock(native_path);", launch)
        self.assertIn('write_host_replace_staged(native_path, encoded, "urlaunch")',
                      launch)

if __name__ == "__main__":
    unittest.main()
