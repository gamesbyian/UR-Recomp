"""Small ROM-free truth checks for the visual-first art review handoff."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "media/showcase/art-reconstruction/2026-10-10"
PAGE = ROOT / "tools/art/model-review/visual-review.html"


class LikenessReviewTests(unittest.TestCase):
    def test_all_historical_original_and_rejected_art_pairs_really_exist(self):
        # The 4x art is technical history, never current likeness acceptance.
        sums = (SOURCE / "SHA256SUMS").read_text(encoding="utf-8")
        found = {}
        for line in sums.splitlines():
            m = re.fullmatch(
                r"([0-9a-f]{64})  media/showcase/art-reconstruction/2026-10-10/(stock|authored)/(p[12]-0[0-6]\.png)",
                line,
            )
            if m:
                key = (m.group(2), m.group(3))
                self.assertNotIn(key, found)
                found[key] = m.group(1)
        self.assertEqual(len(found), 28)
        for kind in ("stock", "authored"):
            for player in ("p1", "p2"):
                for n in range(7):
                    name = f"{player}-{n:02}.png"
                    path = SOURCE / kind / name
                    with self.subTest(kind=kind, name=name):
                        self.assertEqual(
                            hashlib.sha256(path.read_bytes()).hexdigest(),
                            found[(kind, name)],
                        )

    def test_one_viewer_and_two_verified_site_stagers(self):
        reviewer = PAGE.read_text(encoding="utf-8")
        base = (ROOT / "tools/art/model-review/index.html").read_text(encoding="utf-8")
        atlas = (ROOT / "tools/windows_visual_atlas.py").read_text(encoding="utf-8")
        opt_in = (ROOT / "tools/art/model-review/stage_pages.py").read_text(encoding="utf-8")
        for string in (
            'id="modelFrame"', 'src="./index.html"',
            'id="stock"', 'id="old"', 'id="overall"', 'id="notes"',
            'data-manual="side"', 'data-manual="three-quarter"', 'data-manual="action"',
            'id="capture"', 'id="sheet"', 'id="download"',
            'UR-ART4K-VISUAL-LIKENESS-VERDICT/1',
            "experimental_model_likeness_approved:false",
            "source_to_model_pose_mapping_verified:false",
        ):
            self.assertIn(string, reviewer)
        self.assertIn('href="./visual-review.html"', base)
        self.assertIn("window.__art4kReviewCapture", base)
        self.assertIn("renderer.domElement.toDataURL('image/png')", base)
        for content in (atlas, opt_in):
            self.assertIn('"visual-review.html"', content)
            self.assertIn('"visual-review-assets.json"', content)
            self.assertIn('"legacy-art"', content)
        self.assertIn("historical_hashes", atlas)
        self.assertIn("digest(source) != expected_hash", opt_in)
        self.assertNotIn('likeness_approved": True', reviewer)

    @unittest.skipUnless(shutil.which("node"), "Node not installed")
    def test_browser_script_is_valid_javascript(self):
        source = PAGE.read_text(encoding="utf-8")
        scripts = re.findall(r"<script>(.*?)</script>", source, flags=re.DOTALL)
        self.assertEqual(len(scripts), 1)
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "likeness-review.js"
            target.write_text(scripts[0], encoding="utf-8")
            process = subprocess.run(
                ["node", "--check", str(target)],
                text=True, capture_output=True, timeout=10,
            )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)


if __name__ == "__main__":
    unittest.main()
