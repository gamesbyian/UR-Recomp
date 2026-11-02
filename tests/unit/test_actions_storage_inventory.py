"""Offline, no-auth controls for the read-only account artifact census."""
from datetime import datetime, timezone
import unittest

from tools import actions_storage_inventory as inv


def a(ident, name, size, expired=False):
    return {
        "id": ident, "name": name, "size_in_bytes": size,
        "created_at": "2026-11-01T00:00:00Z",
        "expires_at": "2026-11-14T00:00:00Z",
        "expired": expired,
    }


class InventoryTests(unittest.TestCase):
    def test_multiple_pages_complete_and_grouped(self):
        items = [a(i + 1, "atlas" if i < 100 else "receipt", 100) for i in range(101)]
        def api(*argv):
            page = int(argv[-1].split("page=")[-1])
            return {"total_count": 101, "artifacts": items[(page - 1) * 100:page * 100]}
        listed = inv.artifact_inventory("gamesbyian/Glimpse", api=api)
        self.assertEqual(len(listed), 101)
        summary = inv.summarize("gamesbyian/Glimpse", listed,
                                now=datetime(2026, 11, 2, tzinfo=timezone.utc))
        self.assertEqual(summary["current_artifact_bytes_estimate"], 10100)
        self.assertEqual(summary["largest_name_groups"][0]["count"], 100)

    def test_refuse_partial_inventory(self):
        def api(*argv):
            return {"total_count": 2, "artifacts": [a(1, "only", 3)]}
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            inv.artifact_inventory("gamesbyian/Chunks", api=api)

    def test_refuse_changed_count_between_pages(self):
        def api(*argv):
            page = int(argv[-1].split("page=")[-1])
            return {"total_count": 101 if page == 1 else 100,
                    "artifacts": [a(i + 1, "x", 1) for i in range(100)] if page == 1 else []}
        with self.assertRaisesRegex(RuntimeError, "changed"):
            inv.artifact_inventory("gamesbyian/Chunks", api=api)

    def test_expired_does_not_count_as_current(self):
        summary = inv.summarize(
            "gamesbyian/AYA", [a(1, "old", 1_000, True), a(2, "new", 4)],
            now=datetime(2026, 11, 2, tzinfo=timezone.utc))
        self.assertEqual(summary["expired_count"], 1)
        self.assertEqual(summary["current_artifact_bytes_estimate"], 4)

    def test_invalid_page_and_names_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "repository"):
            inv.artifact_inventory("not a repo")
        with self.assertRaisesRegex(ValueError, "identifier"):
            inv.artifact_inventory("gamesbyian/Glimpse", api=lambda *_: {
                "total_count": 1, "artifacts": [dict(a(1, "x", 3), id=0)]})
        with self.assertRaisesRegex(ValueError, "timestamp"):
            inv.parse_date("2026-11-02")

    def test_output_names_are_escaped(self):
        result = inv.summarize("gamesbyian/Glimpse", [a(1, "a|b", 4)],
                               now=datetime(2026, 11, 2, tzinfo=timezone.utc))
        self.assertIn("a\\|b", inv.markdown([result]))


if __name__ == "__main__":
    unittest.main()
