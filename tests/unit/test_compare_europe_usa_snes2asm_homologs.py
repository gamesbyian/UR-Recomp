import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "compare_europe_usa_snes2asm_homologs.py"

spec = importlib.util.spec_from_file_location("eu_us_homologs", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class EuropeUsaHomologToolTests(unittest.TestCase):
    def test_lorom_cpu_offset_roundtrip(self):
        for cpu in ("80:8050", "81:C5B3", "82:ACA5", "82:E165"):
            off = mod.cpu_to_offset(cpu)
            self.assertEqual(mod.offset_to_cpu(off), cpu)

    def test_render_separates_structural_delta_from_comparable_consensus(self):
        report = {
            "checkpoint_frame_normalization_lineage": {
                "builds": {
                    "usa-retail": {"style": "usa-style-22-byte"},
                    "legacy-beta": {"style": "usa-style-22-byte"},
                    "pal-prototype-1994-11-29": {"style": "usa-style-22-byte"},
                    "europe-retail": {"style": "europe-style-8-byte"},
                }
            },
            "totals": {
                "regions": 2,
                "comparable_homolog_regions": 1,
                "structural_delta_regions": 1,
                "aligned_opcode_pairs": 3,
                "aligned_opcode_byte_disagreements": 0,
                "aligned_operand_byte_changes": 1,
                "aligned_role_disagreements": 0,
                "aligned_mx_disagreements": 0,
                "zero_role_disagreement_regions": 1,
            },
            "regions": [
                {
                    "name": "stable",
                    "usa_start": "81:8000",
                    "usa_end": "81:8004",
                    "europe_start": "81:8000",
                    "europe_end": "81:8004",
                    "europe_shift": 0,
                    "raw_similarity_after_alignment": 0.8,
                    "aligned_opcode_byte_disagreements": 0,
                    "aligned_operand_byte_changes": 1,
                    "aligned_role_disagreements": 0,
                    "aligned_mx_disagreements": 0,
                    "aligned_opcode_changes": [],
                    "aligned_residuals": [],
                },
                {
                    "name": "delta",
                    "usa_start": "81:8102",
                    "usa_end": "81:8117",
                    "europe_start": "81:80FC",
                    "europe_end": "81:8111",
                    "europe_shift": -6,
                    "raw_similarity_after_alignment": 0.2,
                    "aligned_opcode_byte_disagreements": 4,
                    "aligned_operand_byte_changes": 6,
                    "aligned_role_disagreements": 6,
                    "aligned_mx_disagreements": 0,
                    "aligned_opcode_changes": [],
                    "aligned_residuals": [],
                    "allow_structural_delta": True,
                    "basis": "fixture contraction",
                    "structural_delta": {
                        "usa_span_bytes": 22,
                        "europe_span_bytes": 8,
                        "net_size_delta_europe_minus_usa": -14,
                        "usa_opcode_bytes": ["0xAD", "0xC9"],
                        "europe_opcode_bytes": ["0xAD"],
                        "europe_start": "81:8102",
                        "europe_end": "81:8109",
                    },
                },
            ],
        }
        rendered = mod.render(report)
        self.assertIn("Genuine structural deltas", rendered)
        self.assertIn("Net Europe size delta: -14 bytes", rendered)
        self.assertIn("Surviving analyzer disagreements\n\nNone.", rendered)


if __name__ == "__main__":
    unittest.main()
