"""Read-only RF-015 original opcode/native APU port observer safety tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_apu_phase_observers as patch
import qa01_apu_phase_report as report


def original(pc: str, op: str, *, nxt: str, f: int = 5195,
             p0: str = "30", a1: str = "0042") -> str:
    vals = {
        "f0": str(f), "f1": str(f), "v0": "225", "v1": "225",
        "h0": "100", "h1": "125", "pc": pc, "next": nxt, "op": op,
        "p0": p0, "p1": p0, "db0": "00", "db1": "00",
        "a0": "0000", "a1": a1,
        "rd0": "00", "rd1": "00", "wr0": "01", "wr1": "01",
        "ack0": "42", "ack1": "42", "c60": "1E", "c61": "1E",
    }
    return report.ORIGINAL + " ".join(f"{k}={vals[k]}" for k in report.ORIG_KEYS)


def native(*, f: int = 5196, mode: int = 1,
           direction: str = "R", value: str = "42") -> str:
    vals = {
        "f": str(f), "dir": direction, "reg": "2142",
        "width": "1" if direction == "R" else "2", "value": value,
        "cpu_master": "432120", "apu_cycle": "34210",
        "spc_portclock": "34210", "frame_clock": str(mode),
        "extended": "0", "memsel": "1", "rd": "00",
        "wr": "01", "ack": "42", "c6": "1E",
    }
    return report.NATIVE + " ".join(f"{k}={vals[k]}" for k in report.NATIVE_KEYS)


class ApuPhaseObserversTest(unittest.TestCase):
    def test_source_only_patch_preserves_unique_original_cpu_dispatch(self):
        source = "before\n" + patch.SOURCE_MARKER + "\nafter\n"
        compiled = patch.patch_original(source)
        self.assertEqual(compiled.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertEqual(compiled.count("Registers.PCw++;"), 1)
        self.assertIn(patch.SOURCE_STAMP, compiled)
        for name in ("82803C", "828043", "82804E", "828059", "828066",
                     "82806D", "80FADB", "80FAE2"):
            self.assertIn(name, compiled)
        self.assertIn("Memory.RAM[0x2000]", compiled)
        self.assertIn("Registers.A.W", compiled)
        self.assertIn("Registers.PL", compiled)
        self.assertIn("Registers.DB", compiled)
        self.assertIn("QA01APUORIG_TRUNCATED", compiled)
        self.assertIn("UR_QA01_APU_ORIGINAL_FIRST", compiled)
        with self.assertRaisesRegex(ValueError, "already installed"):
            patch.patch_original(compiled)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            patch.patch_original(source + patch.SOURCE_MARKER)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            patch.patch_original("no original dispatch")

    def test_native_patch_preserves_actual_apu_read_and_word_write(self):
        source = ("\nstatic bool g_apu_frame_time_valid;\n"
                  "static uint64_t rtl_apu_guest_cycle(void) {return 2;}\n"
                  "uint8 ReadRegOpenBus(uint16 reg, uint8 open_bus) {\n"
                  + patch.NATIVE_READ_MARKER
                  + "\n" + patch.NATIVE_WRITE_MARKER + "\n")
        compiled = patch.patch_native(source)
        self.assertIn("uint8 observed = snes_read(g_snes, reg);", compiled)
        self.assertIn("return observed;", compiled)
        self.assertIn("ur_rf015_apu_log(reg, observed, 1u, 'R');", compiled)
        self.assertIn("ur_rf015_apu_log(reg, value, 2u, 'W');", compiled)
        self.assertIn("g_apu_frame_time_valid", compiled)
        self.assertIn("rtl_apu_guest_cycle()", compiled)
        self.assertIn("g_snes->apu->portClock", compiled)
        self.assertIn("QA01APUNATIVE_TRUNCATED", compiled)
        self.assertEqual(compiled.count("void WriteRegWord(uint16 reg, uint16 value)"), 1)
        self.assertIn(patch.NATIVE_STAMP, compiled)
        with self.assertRaisesRegex(ValueError, "already installed"):
            patch.patch_native(compiled)
        with self.assertRaisesRegex(ValueError, "ambiguous Baldosa APU read"):
            patch.patch_native(source.replace(patch.NATIVE_READ_MARKER,
                                              "return value;"))
        with self.assertRaisesRegex(ValueError, "ambiguous Baldosa 16-bit"):
            patch.patch_native(source.replace(patch.NATIVE_WRITE_MARKER,
                                              "void Unknown(void) {"))

    @staticmethod
    def logs() -> tuple[str, str]:
        return (
            "\n".join((original("82803C", "AD", nxt="82803F"),
                       original("828043", "D0", nxt="828045"))),
            native() + "\n" + native(direction="W", value="1234"),
        )

    def test_trace_census_preserves_independent_clock_and_no_claim(self):
        ref, guest = self.logs()
        r = report.analyze(ref, guest)
        self.assertEqual(r["original_apu_read_count"], 1)
        self.assertEqual(r["original_apu_data_banks_observed"], [0])
        self.assertIs(r["original_apu_opcode_effective_bank_hw_mapped"], True)
        self.assertEqual(r["original_apu_read_low_bytes_sample"], [0x42])
        self.assertEqual(r["original_ack_branch_not_taken"], 1)
        self.assertEqual(r["original_ack_branch_taken"], 0)
        self.assertEqual(r["native_apu_word_write_count"], 1)
        self.assertEqual(r["native_apu_read_low_bytes_sample"], [0x42])
        self.assertEqual(r["native_frame_clock_modes_observed"], [1])
        self.assertEqual((r["original_first_frame"], r["native_first_frame"]),
                         (5195, 5196))
        for key in ("source_and_native_frames_calibrated_equivalent",
                    "source_cpu_pc_equals_native_AOT_function_scope_proven",
                    "native_apu_port_read_clock_equals_source_opcode_instant_proven",
                    "source_same_movie_guest_identity_proven_by_logs_alone",
                    "apu_handshake_caused_RF015_proven"):
            self.assertIs(r[key], False)
        self.assertEqual(r["release_gate_credit"], 0)

    def test_original_read_to_branch_pairs_are_executed_local_evidence_only(self):
        # The synthetic source stream proves parser behavior, not a real
        # original/native APU clock alignment or a completed course.
        a = original("82803C", "AD", nxt="82803F", a1="12A7")
        b = original("828043", "D0", nxt="828077")
        guest = native()
        paired = report.analyze(a + "\n" + b, guest)
        self.assertEqual(paired["original_ack_read_branch_pairs_count"], 1)
        self.assertEqual(paired["original_unpaired_apu_reads"], 0)
        self.assertEqual(paired["original_unpaired_ack_branches"], 0)
        self.assertTrue(paired["original_ack_read_branch_pairs_complete"])
        observed = paired["original_ack_read_branch_pairs_sample"][0]
        self.assertEqual(observed["read_low_byte"], 0xA7)
        self.assertEqual(observed["observed_bne_destination"], "828077")
        self.assertTrue(observed["observed_bne_taken"])
        self.assertEqual(observed["original_read_frame"], 5195)
        self.assertTrue(paired["original_ack_pairs_same_original_cpu_stream_only"])
        self.assertFalse(paired["native_apu_port_read_clock_equals_source_opcode_instant_proven"])
        self.assertFalse(paired["apu_handshake_caused_RF015_proven"])
        self.assertEqual(paired["release_gate_credit"], 0)

        # A different executing opcode in between may represent an
        # interrupt or other re-entry. Never pair across it.
        other = original("80FAE2", "C6", nxt="80FAE4")
        interrupted = report.analyze(a + "\n" + other + "\n" + b, guest)
        self.assertEqual(interrupted["original_ack_read_branch_pairs_count"], 0)
        self.assertEqual(interrupted["original_unpaired_apu_reads"], 1)
        self.assertEqual(interrupted["original_unpaired_ack_branches"], 1)
        self.assertFalse(interrupted["original_ack_read_branch_pairs_complete"])

        # Equally, a distant source frame cannot be presented as one
        # directly observed CPU read/branch decision.
        delayed = report.analyze(a + "\n" +
                                 original("828043", "D0", nxt="828045", f=5198),
                                 guest)
        self.assertEqual(delayed["original_ack_read_branch_pairs_count"], 0)
        self.assertEqual(delayed["original_unpaired_ack_branches"], 1)
        self.assertEqual(delayed["release_gate_credit"], 0)

        # PL.Z is not an admissible branch oracle in this Snes9x port,
        # whose effective flags may be lazily maintained. The executed
        # next PC is the only direction recorded.
        not_taken = report.analyze(a + "\n" +
                                   original("828043", "D0", nxt="828045"),
                                   guest)
        self.assertFalse(not_taken["original_ack_read_branch_pairs_sample"][0][
            "observed_bne_taken"])

    def test_campaign_trace_is_manual_only_and_fails_unrelated_selection(self):
        workflow = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text(
            encoding="utf-8")
        self.assertEqual(workflow.count("      qa01_apu_phase:"), 2)
        self.assertIn("QA01_APU_PHASE: ${{ inputs.qa01_apu_phase }}", workflow)
        self.assertIn('if [[ "$QA01_APU_PHASE" == "true" && "$SELECTED" != "zoom-zoo" ]]', workflow)
        self.assertIn('if [[ "${{ inputs.qa01_apu_phase }}" == "true" ]]', workflow)
        self.assertIn("qa01_apu_phase_observers.py original", workflow)
        self.assertIn("qa01_apu_phase_observers.py native", workflow)
        self.assertIn("qa01_apu_phase_report.py", workflow)
        self.assertIn("qa01-apu-edge-report.json", workflow)
        self.assertIn('UR_QA01_APU_ORIGINAL_FIRST: "6748"', workflow)
        self.assertIn('UR_QA01_APU_NATIVE_LAST: "6778"', workflow)
        self.assertIn("  workflow_dispatch:", workflow)
        self.assertIn("  workflow_call:", workflow)
        self.assertNotIn("  schedule:", workflow)
        self.assertNotIn("  pull_request:", workflow)

    def test_original_cpu_bank80_mirror_is_valid_but_wram_is_not(self):
        ref, guest = self.logs()
        shadow = ref.replace("db0=00", "db0=80").replace("db1=00", "db1=80")
        self.assertEqual(report.analyze(shadow, guest)[
            "original_apu_data_banks_observed"], [0x80])
        for bank in ("40", "7E", "C0", "FF"):
            with self.subTest(data_bank=bank):
                bad = ref.replace("db0=00", f"db0={bank}").replace(
                    "db1=00", f"db1={bank}")
                with self.assertRaisesRegex(ValueError, "hardware|I/O"):
                    report.analyze(bad, guest)

    def test_branch_taken_is_recorded_not_invented_from_ack_bytes(self):
        ref, native_log = self.logs()
        ref = ref.replace("next=828045", "next=828077")
        r = report.analyze(ref, native_log)
        self.assertEqual(r["original_ack_branch_taken"], 1)
        self.assertEqual(r["original_ack_branch_not_taken"], 0)
        self.assertIs(r["apu_handshake_caused_RF015_proven"], False)

    def test_bad_traces_fail_closed(self):
        ref, guest = self.logs()
        cases = (
            ("empty source", "", guest),
            ("empty native", ref, ""),
            ("source truncation", ref + "\nQA01APUORIG_TRUNCATED limit=6000", guest),
            ("native truncation", ref, guest + "\nQA01APUNATIVE_TRUNCATED limit=6000"),
            ("changed original opcode", ref.replace("op=AD", "op=A9"), guest),
            ("wrong original PC", ref.replace("pc=82803C", "pc=83803C"), guest),
            ("wrong source branch", ref.replace("next=828045", "next=828046"), guest),
            ("wrong A width", ref.replace("p0=30", "p0=10"), guest),
            ("wrong original DBR", ref.replace("db0=00", "db0=7E"), guest),
            ("changed DBR inside read", ref.replace("db1=00", "db1=7E"), guest),
            ("spurious release credit", ref + " release_gate_credit=1", guest),
            ("native frame invalid", ref, guest.replace("frame_clock=1", "frame_clock=2")),
            ("native PORT incorrect", ref, guest.replace("reg=2142", "reg=2140")),
            ("native read width invalid", ref, guest.replace("dir=R reg=2142 width=1",
                                                             "dir=R reg=2142 width=2")),
            ("native nonhex data", ref, guest.replace("value=42", "value=0x42")),
            ("original duplicate field", ref.replace("op=AD", "op=AD op=AD"), guest),
        )
        for name, source, native_log in cases:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    report.analyze(source, native_log)

    def test_original_word_write_width_and_queue_branch_validation(self):
        ref, guest = self.logs()
        ref += "\n" + original("82806D", "8D", nxt="828070", p0="10",
                                a1="1234")
        self.assertEqual(report.analyze(ref, guest)["original_events"], 3)
        with self.assertRaisesRegex(ValueError, "16-bit outgoing"):
            report.analyze(ref.replace("p0=10", "p0=30"), guest)
        ref += "\n" + original("82804E", "F0", nxt="828077")
        self.assertEqual(report.analyze(ref, guest)[
            "original_queue_empty_branch_taken"], 1)


if __name__ == "__main__":
    unittest.main()
