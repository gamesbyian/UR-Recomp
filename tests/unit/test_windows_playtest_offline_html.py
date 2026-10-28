"""Offline physical H01-H07 recorder is source-pinned, private and QA-non-authoritative."""
import html.parser
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RECORDER = ROOT / "docs/playtest/windows-h01-h07-offline.html"
INSTRUCTIONS = ROOT / "docs/WINDOWS-PLAYTEST-INSTRUCTIONS.md"
SHEET = ROOT / "docs/WINDOWS-PLAYTEST-RESULTS-TEMPLATE.md"


class _Tags(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class OfflineWindowsH01H07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = RECORDER.read_text(encoding="utf-8")
        cls.tags = _Tags()
        cls.tags.feed(cls.html)
        scripts = re.findall(r"<script>(.*?)</script>", cls.html, flags=re.S)
        if len(scripts) != 1:
            raise ValueError("offline recorder must have exactly one embedded script")
        cls.js = scripts[0]

    def test_immutable_candidate_pins_match_current_owner_instructions(self):
        for pin in (
            "93d6251dc1edad80d350be46a11be715883b46a3",
            "f52e39b1059ebf0047a2cd81eb3c84e179db9bdda51f0323e4065e2bf4e312a1",
            "68a80457a321aa318c182c7eb8cf49fb7587b13bfbcf32c4190d057fdea3d8a9",
        ):
            with self.subTest(pin=pin):
                self.assertIn(pin, self.js)
                self.assertIn(pin, INSTRUCTIONS.read_text(encoding="utf-8"))
        self.assertIn("12803447603", self.html)
        self.assertIn("40658096254", self.js)
        self.assertIn("source-tree-equivalent", self.html)
        self.assertIn("November 4, 2026", INSTRUCTIONS.read_text(encoding="utf-8"))
        self.assertNotIn("930f16ed4536aea83450335bd550aa9afefd98f1", self.js)
        self.assertLess(INSTRUCTIONS.read_text(encoding="utf-8").index("Preferred #2763"),
                        INSTRUCTIONS.read_text(encoding="utf-8").index("Superseded post-#2688"))

    def test_all_seven_physical_journeys_and_statuses_present(self):
        for n in range(1, 8):
            self.assertIn('"H0' + str(n) + '"', self.js)
            self.assertIn("| H0" + str(n) + " |", SHEET.read_text())
        self.assertIn("PASS", self.html)
        self.assertIn("FAIL", self.html)
        self.assertIn("BLOCKED", self.html)
        self.assertIn("NOT_RUN", self.js)
        self.assertIn("three dissimilar Windows setups", self.html)

    def test_no_upload_remote_dependencies_or_persistent_data_storage(self):
        # Manual navigation to GitHub download is allowed, background transfer
        # of local observations or saved ROM data is not.
        for forbidden in (
            "fetch(", "XMLHttpRequest", "sendBeacon", "localStorage",
            "sessionStorage", "indexedDB", "WebSocket", "serviceWorker",
            "external script", "type=\"submit\"", "<form", "data:application",
        ):
            with self.subTest(fragment=forbidden):
                self.assertNotIn(forbidden, self.html)
        self.assertFalse(any(tag in ("iframe", "img") for tag, _ in self.tags.tags))
        self.assertFalse(any(tag == "script" and "src" in attrs
                             for tag, attrs in self.tags.tags))
        self.assertFalse(any(tag == "link" and "href" in attrs
                             for tag, attrs in self.tags.tags))
        self.assertIn("Blob([body]", self.js)
        self.assertIn("download(name,body,type)", self.js)
        self.assertIn("file.size>65536", self.js)

    def test_report_cannot_self_admit_release_or_edit_candidate(self):
        for literal in (
            "unreviewed_tester_observations_zero_release_credit",
            "independent_qa_review: \"PENDING\"",
            "official_release_gates_accepted_by_this_report: 0",
            "complete_usa_events_accepted_by_this_report: 0",
            "Wrong candidate/schema or incomplete H01-H07",
            "Object.keys(candidate).some(k=>candidate[k]!==c[k])",
            "if (!preserveImported) capture()",
            "show(index, true)",
        ):
            self.assertIn(literal, self.js)
        self.assertIn("ROM", self.html)
        self.assertIn("SRAM", self.html)

    def test_touch_target_keyboard_privacy_and_safe_text_insertion(self):
        self.assertIn("min-height: 44px", self.html)
        self.assertIn("min-height: 48px", self.html)
        self.assertIn("focus-visible", self.html)
        self.assertIn("prefers-reduced-motion", self.html)
        self.assertIn("aria-live=\"polite\"", self.html)
        self.assertIn("textContent", self.js)
        self.assertNotIn("innerHTML", self.js)
        for field in ("source-pin", "zip-pin", "exe-pin", "step-nav",
                      "previous", "next", "save-json", "save-md", "copy-md", "import"):
            self.assertTrue(any(attrs.get("id") == field for _, attrs in self.tags.tags),
                            field)

    def test_embedded_javascript_parses_with_node_when_available(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node runtime not available")
        with tempfile.TemporaryDirectory() as d:
            script = Path(d) / "offline-playtest.js"
            script.write_text(self.js, encoding="utf-8")
            result = subprocess.run([node, "--check", str(script)],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
