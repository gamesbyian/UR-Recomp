from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import validate_external_evidence as vee


def lead(**overrides):
    item = {
        "id": "example",
        "value": "high",
        "cost": "low",
        "status": "ready",
        "source_ids": ["source-one"],
        "question": "What does this establish?",
        "next_discriminator": "Run the smallest useful check.",
        "deliverables": ["compact report"],
        "tags": ["test"],
        "artifact_need": {
            "kind": "none",
            "state": "none",
            "user_action_required": False,
            "request": "",
        },
    }
    item.update(overrides)
    return item


class ValidationTests(unittest.TestCase):
    def test_valid_worklist(self) -> None:
        leads = vee.validate({"schema_version": 1, "leads": [lead()]})
        self.assertEqual(len(leads), 1)

    def test_duplicate_id_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate lead id"):
            vee.validate({"schema_version": 1, "leads": [lead(), lead()]})

    def test_manual_request_required(self) -> None:
        item = lead()
        item["artifact_need"] = {
            "kind": "patch",
            "state": "dead-link",
            "user_action_required": True,
            "request": "",
        }
        with self.assertRaisesRegex(ValueError, "request required"):
            vee.validate({"schema_version": 1, "leads": [item]})

    def test_unknown_source_id_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown catalog id"):
            vee.validate(
                {"schema_version": 1, "leads": [lead()]},
                {"different-source"},
            )

    def test_catalog_source_ids_parses_catalog_shape(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "catalog.yml"
            path.write_text(
                'sources:\n  - id: first-source\n  - id: "second-source"\n',
                encoding="utf-8",
            )
            self.assertEqual(
                vee.catalog_source_ids(path),
                {"first-source", "second-source"},
            )

    def test_summary_surfaces_manual_actions(self) -> None:
        manual = lead(
            id="manual",
            artifact_need={
                "kind": "archive",
                "state": "dead-link",
                "user_action_required": True,
                "request": "Provide the archive if you already have it.",
            },
        )
        summary = vee.summarize([lead(), manual])
        self.assertEqual(summary["manual_action_count"], 1)
        self.assertEqual(summary["manual_actions"][0]["id"], "manual")


if __name__ == "__main__":
    unittest.main()
