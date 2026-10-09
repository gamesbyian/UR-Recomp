"""QA-02: no public run/sidecar name before OS-level data flush.

Separate native pair tests cover collision, rollback and fresh-process
admission. The source contract protects the durability ordering that these
fixtures cannot prove across actual loss of physical power.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RunMatchDurabilityContract(unittest.TestCase):
    def test_staged_run_synced_before_no_replace_claim(self):
        source = (ROOT / "native/product/completed_run_store.cpp").read_text(
            encoding="utf-8"
        )
        body = source.split("bool append_completed_run_record(", 1)[1].split(
            "\nstd::vector<InspectedRunRecordArtifact>", 1
        )[0]
        codec = body.index("save_completed_run_record_file(")
        sync = body.index("sync_closed_staged_file(staged_file)")
        claim = body.index("publish_without_replacing(staged_file, path)")
        parent = body.index("sync_published_directory_best_effort(directory_path)")
        self.assertLess(codec, sync)
        self.assertLess(sync, claim)
        self.assertLess(claim, parent)
        self.assertIn("cannot durably flush staged run record", body)

    def test_sidecar_synced_before_any_public_pair_claim(self):
        source = (ROOT / "native/product/multiplayer_match_record.cpp").read_text(
            encoding="utf-8"
        )
        body = source.split("bool append_multiplayer_match_pair(", 1)[1]
        codec = body.index("save_multiplayer_match_record_for_run(")
        sync = body.index("sync_closed_staged_file(staged_sidecar)")
        first = body.index("claim_pair_artifact(staged_sidecar_path, final_sidecar_path)")
        second = body.index("claim_pair_artifact(staged_run_path, final_run_path)")
        directory = body.index("sync_published_directory_best_effort(")
        self.assertLess(codec, sync)
        self.assertLess(sync, first)
        self.assertLess(first, second)
        self.assertLess(second, directory)
        self.assertIn("cannot durably flush staged match record", body)

    def test_reopen_uses_native_windows_path_and_checks_close(self):
        source = (
            ROOT / "native/product/local_tournament_atomic_replace.hpp"
        ).read_text(encoding="utf-8")
        body = source.split("inline bool sync_closed_staged_file(", 1)[1].split(
            "\ninline void sync_published_directory_best_effort(", 1
        )[0]
        self.assertIn("_wfopen(staged.c_str(), L\"rb+\")", body)
        self.assertIn('std::fopen(staged.c_str(), "rb+")', body)
        self.assertIn("sync_staged_file(file)", body)
        self.assertIn("std::fclose(file)", body)
        self.assertIn("return synced && closed", body)


if __name__ == "__main__":
    unittest.main()
