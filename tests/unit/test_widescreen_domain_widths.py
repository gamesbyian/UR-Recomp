import re
import unittest
from pathlib import Path

POLICY = Path(__file__).resolve().parents[2] / "analysis" / "widescreen-policy.yml"


def section(text: str, name: str) -> str:
    match = re.search(rf"(?ms)^{name}:\n(.*?)(?=^\S|\Z)", text)
    return match.group(1) if match else ""


def entries(text: str) -> dict[str, str]:
    widths = section(text, "domain_widths")
    return dict(re.findall(r"(?ms)^  (\w+):\n(.*?)(?=^  \w+:\n|\Z)", widths))


class WidescreenDomainWidthTests(unittest.TestCase):
    def test_every_horizontal_domain_has_an_evidenced_width(self):
        text = POLICY.read_text(encoding="utf-8")
        domains = re.findall(r"(?m)^  - (\w+)$", section(text, "horizontal_domains"))
        self.assertEqual(len(domains), 5)
        found = entries(text)
        self.assertEqual(sorted(found), sorted(domains))
        for domain, body in found.items():
            with self.subTest(domain=domain):
                width = re.search(r"(?m)^    width_pixels: (\d+)$", body)
                self.assertIsNotNone(width)
                self.assertIn(int(width.group(1)), (256, 342))
                self.assertRegex(body, r"(?m)^    status: evidence-backed$")
                self.assertRegex(body, r"(?m)^    evidence: \".+\"$")

    def test_only_render_culling_widens(self):
        wide = [domain for domain, body in entries(POLICY.read_text(encoding="utf-8")).items()
                if re.search(r"(?m)^    width_pixels: 342$", body)]
        self.assertEqual(wide, ["render_culling"])


if __name__ == "__main__":
    unittest.main()
