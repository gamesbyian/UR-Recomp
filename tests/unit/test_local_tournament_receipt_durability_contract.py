"""QA-02 source guard: fixture receipts must be durable before authority moves.

The existing native result-link/receipt tests exercise race-safe no-replace
publication and fresh restore. This ordering guard makes a prepublication
OS data flush a non-optional precondition; it is not a power-loss witness.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class FixtureReceiptDurabilityContract(unittest.TestCase):
    def test_receipt_publisher_flushes_before_no_replace_visibility(self):
        data = (ROOT / "native/product/local_tournament_result_link_store.cpp").read_text(
            encoding="utf-8"
        )
        body = data.split("LinkPublishStatus publish_link(", 1)[1].split(
            "\nstd::optional<std::string> read_link(", 1
        )[0]
        write = body.index("std::fwrite(")
        flush = body.index("std::fflush(")
        sync = body.index("detail::sync_staged_file(file)")
        close = body.index("std::fclose(file)")
        no_replace = body.index("fs::create_hard_link(")
        self.assertLess(write, flush)
        self.assertLess(flush, sync)
        self.assertLess(sync, close)
        self.assertLess(close, no_replace)
        self.assertIn("!synced", body)
        self.assertIn("detail::sync_published_directory_best_effort(", body)
        self.assertLess(
            no_replace,
            body.index("detail::sync_published_directory_best_effort("),
        )
        self.assertIn("LinkPublishStatus::Conflict", body)


if __name__ == "__main__":
    unittest.main()
