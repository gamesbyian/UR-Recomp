"""Offline contract tests for public contributor outreach metadata."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/contributor_ops/validate_campaign.py"
SPEC = importlib.util.spec_from_file_location("contributor_campaign_validator", SOURCE)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ContributorCampaignTests(unittest.TestCase):
    def test_current_campaign_has_valid_drafts(self):
        self.assertEqual([], VALIDATOR.validate(ROOT))

    def test_duplicate_id_and_false_post_claim_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = ROOT / "docs/contributors/campaign.json"
            config = json.loads(base.read_text(encoding="utf-8"))
            first = copy.deepcopy(config["venues"][0])
            first["state"] = "posted"
            first["posted_url"] = None
            first["posted_at_utc"] = None
            config["venues"].append(first)
            dest = root / "docs/contributors"
            dest.mkdir(parents=True)
            (dest / "campaign.json").write_text(json.dumps(config), encoding="utf-8")
            findings = VALIDATOR.validate(root)
            self.assertTrue(any("duplicate" in s for s in findings), findings)
            self.assertTrue(any("posted record requires" in s for s in findings), findings)

    def test_insecure_forum_url_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = json.loads((ROOT / "docs/contributors/campaign.json").read_text())
            config["venues"] = [copy.deepcopy(config["venues"][0])]
            config["venues"][0]["forum_url"] = "http://not-secure.invalid"
            dest = root / "docs/contributors"
            dest.mkdir(parents=True)
            (dest / "campaign.json").write_text(json.dumps(config), encoding="utf-8")
            self.assertTrue(any("HTTPS" in s for s in VALIDATOR.validate(root)))


if __name__ == "__main__":
    unittest.main()
