"""QA-02: prepublish durability guard for replaceable ghost trace sidecars."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class GhostTraceDurabilityContract(unittest.TestCase):
    def test_closed_trace_synced_before_atomic_replacement(self):
        text = (
            ROOT / "native/product/completed_run_ghost_trace.cpp"
        ).read_text(encoding="utf-8")
        block = text.split("bool save_completed_run_ghost_trace_file(", 1)[1].split(
            "\nCompletedRunGhostTraceLoadResult load_completed_run_ghost_trace_file(", 1
        )[0]
        close_codec = block.index("out.close();")
        open_for_sync = block.index("_wfopen(staged_file.c_str(), L\"rb+\")")
        os_flush = block.index("detail::sync_staged_file(sync_file)")
        close_sync = block.index("std::fclose(sync_file)")
        rename = block.index("fs::rename(staged_file, final_path, ec)")
        metadata = block.index("detail::sync_published_directory_best_effort(parent)")
        self.assertLess(close_codec, open_for_sync)
        self.assertLess(open_for_sync, os_flush)
        self.assertLess(os_flush, close_sync)
        self.assertLess(close_sync, rename)
        self.assertLess(rename, metadata)
        self.assertIn('std::fopen(staged_file.c_str(), "rb+")', block)
        self.assertIn("cannot durably flush ghost trace", block)
        self.assertIn("if (!synced || !sync_closed)", block)


if __name__ == "__main__":
    unittest.main()
