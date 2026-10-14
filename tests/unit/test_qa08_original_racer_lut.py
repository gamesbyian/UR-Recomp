"""Read-only source-original 65816 palette lookup tests; synthetic selector values."""
import json
from pathlib import Path
import tempfile
import unittest
from tools import check_qa08_original_racer_lut as probe
from tools import instrument_snesref_qa08_hdma_opcode_context as patch

LAYOUT_PATH = (Path(__file__).resolve().parents[2] / "analysis" / "data" /
    "qa08-original-2p-channel5-executed-opcode-table-layout.json")


def fixtures():
    layout = json.loads(LAYOUT_PATH.read_text(encoding="utf8"))
    opcodes = {
        "schema":probe.OPCODE,
        "original_Snes9x_frame":1781,
        "independently_source_accepted_WRAM_writer_PCs":18,
        "actual_executed_original_opcode_records":55,
        "original_native_same_input_frame_parity_proven":False,
        "actual_opcode_sequence":[{
            "executed_65816_PC":r["original_PC"].replace(":",""),
            "actual_instruction_bytes_hex":r["actual_ROM_instruction_hex"]
        } for r in layout["original_source_opcode_sequence"]]
    }
    receipt = {
        "USA_ROM_SHA256":probe.ROM_SHA,
        "original_script_SHA256":layout["original_2P_input_script_SHA256"],
        "original_t480_WRAM_SHA256":layout["original_full_t480_WRAM_SHA256"],
        "second_camera_0DDB":1, "in_race_0313":1,
        "source_65816_writer_PCs":18,
    }
    # Chosen indices are expressly synthetic. Real selector values must be
    # observed by the genuine source workflow before any claim is promoted.
    lines = [
        "UR_QA08_ORIGINAL_RACER_LUT frame=1781 pc=82D5D1 kind=selector a=0002 x=0000",
        "UR_QA08_ORIGINAL_RACER_LUT frame=1781 pc=82D5D4 kind=lookup a=0008 x=0008 bytes=2F408004",
        "UR_QA08_ORIGINAL_RACER_LUT frame=1781 pc=82D61E kind=selector a=0004 x=0008",
        "UR_QA08_ORIGINAL_RACER_LUT frame=1781 pc=82D621 kind=lookup a=0010 x=0010 bytes=20538004",
    ]
    return layout, opcodes, receipt, lines


def execute(root: Path, data):
    layout, opcodes, receipt, lines = data
    def out(filename, obj):
        path = root / filename
        path.write_text(json.dumps(obj), encoding="utf8")
        return path
    a = out("opcode.json", opcodes)
    b = out("layout.json", layout)
    c = out("receipt.json", receipt)
    log = root / "original.log"
    log.write_text("\n".join(lines)+"\n", encoding="utf8")
    return probe.check(log, a, b, c)


class OriginalRacerLookupTests(unittest.TestCase):
    def test_original_instrumentation_is_disabled_and_uses_direct_ROM(self):
        original = ('#include "memmap.h"\nvoid S9xMainLoop (void) {\n'
                    'Op = CPU.PCBase[Registers.PCw];\n'
                    + patch.ANCHOR + '\n}\n')
        code = patch.patch_source(original)
        self.assertIn("UR_QA08_ORIGINAL_HDMA_OPCODE_FRAME", code)
        self.assertIn("UR_QA08_ORIGINAL_RACER_LUT", code)
        self.assertIn("Registers.A.W", code)
        self.assertIn("Registers.X.W", code)
        self.assertIn("CPU.PCBase[qa08_lut_base + 3u]", code)
        self.assertIn("qa08_lut_idx > 255u", code)
        self.assertEqual(code.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        with self.assertRaisesRegex(ValueError, "already present"):
            patch.patch_source(code)

    def test_synthetic_observation_contract_without_true_selector_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = execute(Path(tmp), fixtures())
            self.assertEqual([r["actual_original_selector_low8"] for r in
                              result["actual_original_palette_entries"]], [2,4])
            self.assertEqual(result["independent_source_register_observations"], 4)
            self.assertFalse(result["original_native_same_input_frame_parity_proven"])
            self.assertFalse(result["current_HD_racer_art_likeness_approved"])

    def test_four_source_PCs_frame_and_index_must_be_authentic(self):
        for old, new in (
            ("pc=82D5D4", "pc=82D5D5"),
            ("frame=1781", "frame=1782"),
            ("kind=lookup", "kind=selector"),
            ("x=0008 bytes=2F", "x=000C bytes=2F"),
            ("bytes=20538004", "bytes=20538003"),
        ):
            with self.subTest(modification=(old,new)):
                f = fixtures()
                f[3][:] = [x.replace(old,new) for x in f[3]]
                with tempfile.TemporaryDirectory() as tmp:
                    with self.assertRaises(ValueError):
                        execute(Path(tmp), f)

    def test_missing_extra_overflow_or_bad_native_promotion_fails(self):
        for change in ("missing", "extra", "overflow", "receipt", "opcode"):
            with self.subTest(change=change):
                f = fixtures()
                if change == "missing": f[3].pop()
                if change == "extra": f[3].append(f[3][-1])
                if change == "overflow":
                    f[3].append("UR_QA08_ORIGINAL_RACER_LUT_INVALID frame=1781 pc=82D621 x=FFFF")
                if change == "receipt": f[2]["original_script_SHA256"] = "0"*64
                if change == "opcode": f[1]["actual_opcode_sequence"][0]["actual_instruction_bytes_hex"] = "8F"
                with tempfile.TemporaryDirectory() as tmp:
                    with self.assertRaises(ValueError):
                        execute(Path(tmp), f)


if __name__ == "__main__":
    unittest.main()
