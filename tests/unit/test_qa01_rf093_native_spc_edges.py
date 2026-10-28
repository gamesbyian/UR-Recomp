"""RF093 native SPC edge observer: pinned-anchor and noninterference contracts."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/qa01_rf093_native_spc_edges.py"
spec = importlib.util.spec_from_file_location("rf093", SCRIPT)
rf093 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rf093)

def fixture():
    return "\n".join((
        rf093.ENTRY,
        "void apu_writePortNow(Apu *apu, uint8_t port, uint8_t val) {",
        rf093.NOW,
        "}",
        "static void apu_applyPortWrite(Apu *apu, const ApuPortWrite *w) {",
        rf093.QUEUE,
        "}",
        "bool apu_schedulePortWrite(Apu *apu, uint8_t port, uint8_t val, uint64_t guest_cycle) {",
        rf093.SCHEDULE,
        "}",
        "uint8_t apu_cpuRead(Apu *apu, uint16_t adr) {",
        rf093.READ,
        "return v;",
        "}",
        "void apu_cpuWrite(Apu *apu, uint16_t adr, uint8_t val) {",
        rf093.WRITE,
        "}",
        "void apu_cycle(Apu *apu) { apu->portClock++; }",
    ))

class NativeSpcEdgesTest(unittest.TestCase):
    def test_pinned_patch_preserves_executed_operations(self):
        source = fixture()
        result = rf093.patch(source)
        self.assertEqual(result.count(rf093.STAMP), 1)
        for anchor in (rf093.NOW, rf093.QUEUE, rf093.SCHEDULE,
                       rf093.READ, rf093.WRITE):
            self.assertEqual(result.count(anchor), 1)
        for kind in ("CPU_TO_SPC_APPLY", "QUEUE_APPLY", "QUEUE_SCHEDULE",
                     "CPU_TO_SPC_READ", "SPC_TO_CPU_WRITE"):
            self.assertIn('"' + kind + '"', result)
        self.assertIn("clock=native_spc", result)
        self.assertIn("QA01RF093NATIVE_TRUNCATED", result)
        self.assertIn("apu->portClock", result)
        self.assertIn("snes_frame_counter >= 6054 && snes_frame_counter <= 6059", result)
        self.assertIn("snes_frame_counter >= 6447 && snes_frame_counter <= 6451", result)
        self.assertIn("!((snes_frame_counter >= 6054", result)

    def test_repeat_and_partial_stage_rejected(self):
        result = rf093.patch(fixture())
        with self.assertRaises(ValueError):
            rf093.patch(result)
        with self.assertRaises(ValueError):
            rf093.patch(fixture() + "\nur_rf093_note(")

    def test_source_drift_and_ambiguous_anchor_rejected(self):
        with self.assertRaises(ValueError):
            rf093.patch(fixture().replace(rf093.READ, "return 0;"))
        with self.assertRaises(ValueError):
            rf093.patch(fixture() + "\n" + rf093.WRITE)

    def test_source_is_opt_in_and_no_extra_bus_calls(self):
        result = rf093.patch(fixture())
        self.assertIn('flag[0] != \'1\'', result)
        self.assertEqual(result.count("audio_trace_on_spc_port_read("), 1)
        self.assertEqual(result.count("audio_trace_on_spc_port_write("), 1)
        self.assertEqual(result.count("apu_writePortNow("), 2)
        self.assertEqual(result.count("apu->portClock++;"), 1)

if __name__ == "__main__":
    unittest.main()
