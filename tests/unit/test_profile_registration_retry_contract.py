"""QA-02: a recoverable profile registration conflict must be retryable."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ProfileRegistrationRetryContract(unittest.TestCase):
    def test_creation_retries_safe_mutex_only_root_and_refreshes_roster(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        create = host.split("bool create_profile_from_editor() {", 1)[1].split(
            "\n}\n\nbool rename_profile_from_editor", 1
        )[0]
        rename = host.split("bool rename_profile_from_editor() {", 1)[1].split(
            "\n}\n\nvoid open_profile_menu", 1
        )[0]
        self.assertIn("reusable_aborted_profile_creation_root", create)
        self.assertIn("save_host_profile_state_file_if_current(", create)
        self.assertIn("remove_host_profile_state_file_if_current(", create)
        self.assertIn("persist_profile_catalog(prior_catalog)", create)
        self.assertIn("persist_profile_catalog(original_catalog)", rename)
        self.assertIn("load_host_profile_catalog_file(", create)
        self.assertIn("load_host_profile_catalog_file(", rename)
        self.assertLess(
            create.index("remove_host_profile_state_file_if_current("),
            create.rindex("load_host_profile_catalog_file("),
        )


if __name__ == "__main__":
    unittest.main()
