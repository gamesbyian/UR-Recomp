import hashlib
from pathlib import Path

from tools.evaluate_cc65_da65_closure import inventory


def test_inventory_is_path_ordered_and_content_sensitive(tmp_path: Path):
    (tmp_path / "b.txt").write_text("beta")
    (tmp_path / "a.txt").write_text("alpha")
    report = inventory(tmp_path)
    assert report["file_count"] == 2
    assert report["total_bytes"] == 9
    assert [row["path"] for row in report["files"]] == ["a.txt", "b.txt"]

    before = report["tree_sha256"]
    (tmp_path / "a.txt").write_text("ALPHA")
    assert inventory(tmp_path)["tree_sha256"] != before
