"""ROM-free controls for authentic original-sprite 4bpp index lookup derivation."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.art.rederive_original_sprite_indices import build, reconstruct, REPORT_SHA, MANIFEST_SHA


def digest(x):
    return hashlib.sha256(x).hexdigest()


class OriginalIndexDerivationTests(unittest.TestCase):
    def example(self):
        rgba = bytearray(64*64*4)
        rgba[4:8] = bytes((47,28,62,0))  # written transparent zero vs untouched
        rgba[8:12] = bytes((240,30,30,255))
        rgba[12:16] = bytes((40,70,220,255))
        indices = bytes((0,0,3,7)) + bytes(4092)
        return bytes(rgba), indices

    def test_lossless_index_inversion_with_nonblack_transparency(self):
        rgba, indices = self.example()
        self.assertEqual(reconstruct(rgba, {"f01e1e":3,"2846dc":7}, digest(indices)), indices)

    def test_unmapped_colours_ambiguous_indices_and_digest_drift_fail(self):
        rgba, indices = self.example()
        for palette in ({}, {"f01e1e":3}, {"f01e1e":3,"2846dc":3},
                        {"f01e1e":True,"2846dc":7}, {"f01e1e":3,"2846dc":16}):
            with self.subTest(palette=palette), self.assertRaises(ValueError):
                reconstruct(rgba, palette, digest(indices))
        with self.assertRaisesRegex(ValueError, "original ROM hash"):
            reconstruct(rgba, {"f01e1e":3,"2846dc":8}, digest(indices))
        mutated = bytearray(rgba)
        mutated[11] = 128
        with self.assertRaisesRegex(ValueError, "nonbinary"):
            reconstruct(bytes(mutated), {"f01e1e":3,"2846dc":7}, digest(indices))

    def test_original_report_digest_pin_blocks_untrusted_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "forged.json"
            file.write_text("{}")
            with self.assertRaisesRegex(ValueError, "census SHA mismatch"):
                build(Path(tmp) / "missing.zip",file)

    def test_source_evidence_hashes_are_immutable(self):
        self.assertEqual(REPORT_SHA,"b6f59fc5f9030b44ca9345bf308e5df83901f8b9534a6f33b215fa39f8e3079e")
        self.assertEqual(MANIFEST_SHA,"e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e")


if __name__=="__main__":
    unittest.main()
