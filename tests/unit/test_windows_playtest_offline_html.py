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
BOARD = ROOT / "docs/HOURLY-AGENT-LINES.md"
QUEUE = ROOT / "docs/WORK-QUEUE.md"


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
            "250e0803a1791d9deda7a715614d49f4752cd374",
            "586c32e344af30cfeb61152c475838fbc6aeab7c64d239e560ecd8c4a6bd7616",
            "c9f51257fb84aaddec54c728a64b5c5738393d62932956b6855c1413ba82f3e0",
        ):
            with self.subTest(pin=pin):
                self.assertIn(pin, self.js)
                self.assertIn(pin, INSTRUCTIONS.read_text(encoding="utf-8"))
        self.assertIn("12850662557", self.html)
        self.assertIn("40763949905", self.js)
        self.assertIn("exact merged main", self.html)
        self.assertIn("distinct Return guest Start", self.html)
        self.assertIn("November 11, 2026 at 20:54 UTC", INSTRUCTIONS.read_text(encoding="utf-8"))
        self.assertNotIn("7cad82adcac82dad1b13cb386c89b2f740162efcffa1b4e72b3e4b57b5006fbf", self.js)
        self.assertNotIn("8d7cf72c7e5ad7a394438337c9496bcbd1de306a140cc2959fa0d0a7998c40a2", self.js)
        self.assertLess(INSTRUCTIONS.read_text(encoding="utf-8").index("Preferred #2792"),
                        INSTRUCTIONS.read_text(encoding="utf-8").index("Superseded post-#2688"))
        # A future physical candidate nomination must update both operator
        # entry points rather than silently leaving the recorder on old bytes.
        for authority in (BOARD, QUEUE):
            with self.subTest(authority=authority):
                text = authority.read_text(encoding="utf-8")
                self.assertIn("12850662557", text)
                self.assertIn("586c32e344af30cfeb61152c475838fbc6aeab7c64d239e560ecd8c4a6bd7616", text)
                self.assertIn("c9f51257fb84aaddec54c728a64b5c5738393d62932956b6855c1413ba82f3e0", text)

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
