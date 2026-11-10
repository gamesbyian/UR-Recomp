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

    def test_exact_official_recruitment_landing_substitutes_for_github_link(self):
        # The owner-reported 3Drequests draft was written for volunteers who
        # need not have GitHub. The record of proposed post text is retained.
        raw = (ROOT / "docs/contributors/posts/3drequests.md").read_text(encoding="utf-8")
        landing = "https://gamesbyian.github.io/UR-Recomp/contributors/"
        self.assertIn("**Recruitment/contact site:** " + landing, raw)
        self.assertIn(landing + "3d/", raw)
        self.assertNotIn("https://github.com/gamesbyian/UR-Recomp", raw)
        manifest = json.loads(
            (ROOT / "docs/contributors/campaign.json").read_text(encoding="utf-8"))
        row = copy.deepcopy(next(v for v in manifest["venues"] if v["id"] == "3drequests"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            post = root / row["post_file"]
            post.parent.mkdir(parents=True)
            (root / "docs/contributors/campaign.json").write_text(
                json.dumps({"schema_version": 1, "venues": [row]}),
                encoding="utf-8")
            post.write_text(raw, encoding="utf-8")
            self.assertEqual([], VALIDATOR.validate(root))
            # A role subpage is still present, but a spoofed contact landing
            # must not satisfy the first-party source/evidence requirement.
            altered = raw.replace(
                "**Recruitment/contact site:** " + landing,
                "**Recruitment/contact site:** https://different-site.invalid/contributors/")
            self.assertIn(landing + "3d/", altered)
            post.write_text(altered, encoding="utf-8")
            self.assertTrue(
                any("missing project evidence link" in finding
                    for finding in VALIDATOR.validate(root)))

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

    def test_owner_report_without_permalink_is_distinct_from_verified_post(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = json.loads((ROOT / "docs/contributors/campaign.json").read_text())
            row = copy.deepcopy(config["venues"][0])
            row.update(
                state="reported_posted",
                report_source="owner",
                reported_posted_on="2026-11-09",
                posted_url=None,
                posted_at_utc=None,
            )
            config["venues"] = [row]
            dest = root / "docs/contributors"
            dest.mkdir(parents=True)
            (dest / "campaign.json").write_text(json.dumps(config), encoding="utf-8")
            # This isolated fixture lacks the draft and thus still reports a missing
            # file, but must not report false permalink or posting state errors.
            findings = VALIDATOR.validate(root)
            self.assertFalse(any("permalink" in s or "reported posting" in s for s in findings), findings)
            row["posted_url"] = row["forum_url"]
            (dest / "campaign.json").write_text(json.dumps(config), encoding="utf-8")
            findings = VALIDATOR.validate(root)
            self.assertTrue(any("unverified report" in s for s in findings), findings)

    def test_reported_share_url_must_match_the_subreddit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = json.loads((ROOT / "docs/contributors/campaign.json").read_text())
            row = copy.deepcopy(next(v for v in config["venues"] if v["id"] == "inat"))
            row["reported_post_url"] = "https://www.reddit.com/r/OtherSub/s/example"
            config["venues"] = [row]
            dest = root / "docs/contributors"
            dest.mkdir(parents=True)
            (dest / "campaign.json").write_text(json.dumps(config), encoding="utf-8")
            self.assertTrue(any("correct subreddit" in s for s in VALIDATOR.validate(root)))

    def test_subreddit_homepage_is_not_a_post_permalink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = json.loads((ROOT / "docs/contributors/campaign.json").read_text())
            row = copy.deepcopy(config["venues"][0])
            row.update(state="posted", posted_url=row["forum_url"], posted_at_utc="2026-11-09T22:30:00Z")
            config["venues"] = [row]
            dest = root / "docs/contributors"
            dest.mkdir(parents=True)
            (dest / "campaign.json").write_text(json.dumps(config), encoding="utf-8")
            self.assertTrue(any("subreddit homepage" in s for s in VALIDATOR.validate(root)))

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
