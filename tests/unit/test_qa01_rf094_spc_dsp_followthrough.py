"""RF094 source-bounded post-DSP writes and stricter late F7 receipts.

No game ROM, emulator runtime, event admission or executable-source change.
"""
from pathlib import Path
import sys
import tarfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_rf094_spc_dsp_followthrough as obs
import qa01_rf092_original_spc_edges as orig
import qa01_rf093_native_spc_edges as native
import qa01_rf094_spc_dsp_report as report


class RF094DSPSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = ROOT / "third_party/src/snes9x-libretro"
        pre = tuple((root / path).read_text(encoding="utf-8")
                    for path in (orig.SMP, orig.CORE, orig.MEMORY))
        cls.staged = orig.patch(*pre)
        archive = ROOT / "third_party/archives/snesrecomp-cd5875cbdaf19f5e.tar.gz"
        with tarfile.open(archive, "r:gz") as tf:
            entries = [m for m in tf.getmembers()
                       if (m.name == "runner/src/snes/apu.c" or
                           m.name.endswith("/runner/src/snes/apu.c"))
                       and m.isfile()]
            if len(entries) != 1:
                raise AssertionError("exact pinned native APU source missing")
            cls.stock_native = tf.extractfile(entries[0]).read().decode("utf-8")
        cls.staged_native = native.patch(cls.stock_native)

    def test_original_original_dsp_and_later_port_staged_exactly_once(self):
        smp, memory = obs.patch_original(self.staged[0], self.staged[2])
        self.assertEqual(smp.count(obs.ORIGINAL_STAMP), 1)
        self.assertIn("frame >= 6445u && frame <= 6451u", smp)
        self.assertIn("frame < 6445u || frame > 6451u", smp)
        self.assertIn("rf092_spc_ticks", smp)
        self.assertIn("QA01RF094ORIG_TRUNCATED", smp)
        self.assertIn("dsp.write(status.dsp_addr, data);\n"
                      "    rf094_original_dsp_write(status.dsp_addr, data);", memory)
        self.assertEqual(memory.count("dsp.write(status.dsp_addr, data);"),
                         self.staged[2].count("dsp.write(status.dsp_addr, data);"))
        self.assertEqual(memory.count("if(status.dsp_addr & 0x80) break;"), 1)
        self.assertLess(smp.index("static unsigned long long rf092_spc_ticks;"),
                        smp.index("static void rf094_original_dsp_write("))
        self.assertLess(smp.index("static void rf094_original_dsp_write("),
                        smp.index('#include "algorithms.cpp"'))
        with self.assertRaisesRegex(ValueError, "pristine RF092"):
            obs.patch_original(smp, memory)

    def test_native_dsp_post_commit_and_source_continuation(self):
        source = obs.patch_native(self.staged_native)
        self.assertIn("QA01RF094NATIVE_TRUNCATED", source)
        self.assertIn("snes_frame_counter >= 6447 && snes_frame_counter <= 6453",
                      source)
        self.assertIn("snes_frame_counter < 6447 || snes_frame_counter > 6453",
                      source)
        self.assertIn("dsp_write(apu->dsp, apu->dspAdr, val);\n"
                      "        ur_rf094_native_dsp_write(apu, apu->dspAdr, val);",
                      source)
        self.assertEqual(source.count("dsp_write(apu->dsp, apu->dspAdr, val);"),
                         self.staged_native.count("dsp_write(apu->dsp, apu->dspAdr, val);"))
        self.assertEqual(source.count("apu->portClock++"),
                         self.staged_native.count("apu->portClock++"))
        self.assertEqual(source.count("apu->outPorts[adr - 0xf4] = val;"),
                         self.staged_native.count("apu->outPorts[adr - 0xf4] = val;"))
        with self.assertRaisesRegex(ValueError, "pristine RF093"):
            obs.patch_native(source)

    def test_untouched_sources_and_ambiguous_calls_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "RF092"):
            obs.patch_original("SMP smp;\n", self.staged[2])
        with self.assertRaisesRegex(ValueError, "RF093"):
            obs.patch_native(self.stock_native)
        for bad in (self.staged_native.replace(obs.NATIVE_WRITE, ""),
                    self.staged_native + obs.NATIVE_WRITE,
                    self.staged_native.replace(obs.NATIVE_FRAME_OLD, "")):
            with self.subTest(kind="native", length=len(bad)):
                with self.assertRaisesRegex(ValueError, "drift"):
                    obs.patch_native(bad)
        for bad in (self.staged[2].replace(obs.ORIGINAL_WRITE, ""),
                    self.staged[2] + obs.ORIGINAL_WRITE):
            with self.subTest(kind="original", length=len(bad)):
                with self.assertRaisesRegex(ValueError, "drift"):
                    obs.patch_original(self.staged[0], bad)

    def test_campaign_stages_only_under_explicit_dsp_input(self):
        flow = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text()
        self.assertIn("qa01_rf094_spc_dsp:", flow)
        self.assertIn("RF094 requires paired RF084/echo source", flow)
        self.assertLess(flow.index("qa01_rf092_original_spc_edges.py --root"),
                        flow.index("qa01_rf094_spc_dsp_followthrough.py --original"))
        self.assertLess(flow.index("qa01_rf093_native_spc_edges.py --root"),
                        flow.index("qa01_rf094_spc_dsp_followthrough.py --native"))
        self.assertIn("export UR_QA01_RF094_SPC_DSP=1", flow)
        self.assertIn("qa01_rf094_spc_dsp_report.py", flow)
        self.assertIn("QA01RF094ORIG_TRUNCATED", flow)
        self.assertIn("QA01RF094NATIVE_TRUNCATED", flow)
        self.assertNotIn("schedule:\n", flow)

    def test_campaign_artifact_retains_actual_rf094_json_and_raw_logs(self):
        flow = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text()
        block = flow.split(
            "      - name: Always retain per-case receipt and bounded diagnostic logs\n", 1
        )[1].split("\n  aggregate:", 1)[0]
        self.assertIn("uses: actions/upload-artifact@v4", block)
        for suffix in (
            "qa01-rf094-spc-dsp-followthrough.json",
            "work/${{ matrix.case }}/replay/reference.log",
            "work/${{ matrix.case }}/replay/native.log",
        ):
            with self.subTest(suffix=suffix):
                self.assertIn("            ${{ runner.temp }}/qa01-case/" + suffix, block)


class RF094Receipt(unittest.TestCase):
    @staticmethod
    def row(side, seq, frame, ticks, reg="4C", val="80"):
        clock = "original_spc" if side == "ORIG" else "native_spc"
        return (f"QA01RF094{side} seq={seq} frame={frame} reg={reg} val={val} "
                f"spc_ticks={ticks} spc_next_pc=0684 clock={clock}\n")

    def test_realistic_disparate_event_frame_registration(self):
        original = self.row("ORIG", 1, 6446, 109972600)
        native = self.row("NATIVE", 1, 6449, 109616700)
        d = report.analyze(original.encode(), native.encode())
        self.assertEqual(d["original"]["first"]["entry_offset"], -1)
        self.assertEqual(d["native"]["first"]["entry_offset"], 0)
        self.assertTrue(d["same_ordered_register_values"])
        self.assertFalse(d["same_ordered_register_values_proves_audio_parity"])
        self.assertFalse(d["cross_core_clock_conversion_proven"])
        self.assertEqual(d["usa_event_credit"], 0)
        self.assertEqual(d["windows_release_gate_credit"], 0)

    def test_empty_stream_is_explicit_negative_not_false_success(self):
        d = report.analyze(b"no dsp rows\n", b"no dsp rows\n")
        self.assertTrue(d["original"]["no_dsp_write_observed"])
        self.assertEqual(d["native"]["executed_dsp_writes"], 0)
        self.assertFalse(d["same_ordered_register_values"])
        self.assertFalse(d["same_ordered_f7_bytes"])
        self.assertFalse(d["full_guest_event_admitted"])

    def test_strict_frame_reg_sequence_clock_and_truncation(self):
        a = self.row("ORIG", 1, 6445, 20)
        b = self.row("ORIG", 2, 6451, 21)
        self.assertEqual(report.audit((a+b).encode(), "ORIG")
                         ["executed_dsp_writes"], 2)
        bad = (
            a.replace("frame=6445", "frame=6444"),
            b.replace("frame=6451", "frame=6452"),
            a.replace("seq=1", "seq=2"),
            a.replace("reg=4C", "reg=80"),
            a.replace("clock=original_spc", "clock=native_spc"),
            a + b.replace("spc_ticks=21", "spc_ticks=19"),
            a + "QA01RF094ORIG_TRUNCATED\n",
            a.replace("val=80", "val=GG"),
        )
        for candidate in bad:
            with self.subTest(candidate=candidate[-100:]), self.assertRaises(ValueError):
                report.audit(candidate.encode(), "ORIG")

if __name__ == "__main__":
    unittest.main()
