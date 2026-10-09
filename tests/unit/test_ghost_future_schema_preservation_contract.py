"""QA-02: downgrade must not destroy valid future .urghost."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class GhostFutureSchemaPreservation(unittest.TestCase):
    def test_real_writer_locks_and_checks_version_before_staging(self):
        text = (ROOT / "native/product/completed_run_ghost_trace.cpp").read_text(
            encoding="utf-8"
        )
        body = text.split("bool save_completed_run_ghost_trace_file(", 1)[1].split(
            "\nCompletedRunGhostTraceLoadResult load_completed_run_ghost_trace_file(", 1
        )[0]
        lock = body.index("TournamentLaunchPathLock lock(path)")
        reread = body.index("load_completed_run_ghost_trace_file(path)")
        version = body.index("CompletedRunGhostTraceLoadStatus::UnsupportedVersion")
        stage = body.index("fs::create_directory(staging, ec)")
        rename = body.index("fs::rename(staged_file, final_path, ec)")
        self.assertLess(lock, reread)
        self.assertLess(reread, version)
        self.assertLess(version, stage)
        self.assertLess(stage, rename)
        self.assertIn("refusing to replace future ghost trace schema", body)
        self.assertIn("if (!lock.acquired())", body)


if __name__ == "__main__":
    unittest.main()
