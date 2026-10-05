import base64
import hashlib
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "native" / "product" / "clean_stock_sram.cpp"
FIXTURE = (
    ROOT
    / "reference"
    / "imported"
    / "reverse-engineering"
    / "dessyreqt"
    / "SRAM"
    / "Clean.srm"
)


class CleanStockSramTests(unittest.TestCase):
    def test_embedded_seed_matches_canonical_clean_sram_exactly(self):
        source = SOURCE.read_text(encoding="utf-8")
        marker = "constexpr std::string_view kCleanStockSramBase64 ="
        self.assertIn(marker, source)
        payload_region = source.split(marker, 1)[1].split("\n;", 1)[0]
        encoded = "".join(
            re.findall(r'"([A-Za-z0-9+/=]+)"', payload_region)
        )
        embedded = base64.b64decode(encoded, validate=True)
        canonical = FIXTURE.read_bytes()

        self.assertEqual(len(canonical), 8192)
        self.assertEqual(embedded, canonical)

        git_blob_sha = hashlib.sha1(
            b"blob " + str(len(canonical)).encode("ascii") + b"\0" + canonical
        ).hexdigest()
        self.assertEqual(git_blob_sha, "f5c722385bca6c08fd27e47999684b05036bea4b")
        self.assertIn(f"Git blob: {git_blob_sha}", source)


if __name__ == "__main__":
    unittest.main()
