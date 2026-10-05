import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "compare_regional_audio_packages.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("regional_audio", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RegionalAudioPackageComparisonTests(unittest.TestCase):
    def test_compare_blocks(self):
        tool = load_tool()
        usa = {
            "blocks": [
                {
                    "record_sha256": "a",
                    "payload_sha256": "pa",
                    "total_length": 10,
                },
                {
                    "record_sha256": "b",
                    "payload_sha256": "pb",
                    "total_length": 20,
                },
            ]
        }
        eur = {
            "blocks": [
                {
                    "record_sha256": "a",
                    "payload_sha256": "pa",
                    "total_length": 10,
                },
                {
                    "record_sha256": "c",
                    "payload_sha256": "pc",
                    "total_length": 22,
                },
            ]
        }
        rows = tool.compare_blocks(usa, eur)
        self.assertTrue(rows[0]["record_identical"])
        self.assertFalse(rows[1]["record_identical"])
        self.assertEqual(rows[1]["length_delta"], 2)

    def test_actual_retail_pools_parse(self):
        tool = load_tool()
        usa = tool.checked_rom(
            ROOT / "reference/roms/retail/Uniracers_USA.sfc", "usa"
        )
        eur = tool.checked_rom(
            ROOT / "reference/roms/retail/Unirally_Europe.sfc", "europe"
        )
        report = tool.build_report(usa, eur)
        self.assertEqual(report["blocks"]["count"], 0x32)
        self.assertEqual(report["pool"]["cpu_start"], "0x108000")
        self.assertEqual(
            len(report["selector_tables"]["same_address_rows"]), 6
        )
        # Do not hard-code whether PAL package content is identical here.
        # The retained generated report is the evidence for that result.


if __name__ == "__main__":
    unittest.main()
