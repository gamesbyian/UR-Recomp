"""ROM-free source guards for one opt-in RF088/RF089 paired Zoo case.

These checks validate workflow wiring only. They do not execute a ROM or
qualify original/native timing, event parity, or observer-off noninterference.
"""
import unittest
from pathlib import Path

WORKFLOW = (Path(__file__).resolve().parents[2] /
            ".github/workflows/qa01-event-campaign.yml")
WRAPPER = (Path(__file__).resolve().parents[2] /
           ".github/workflows/qa01-zoo-causal-request.yml")


class PairedEchoWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")

    def test_opt_in_defaults_and_guard(self):
        s = self.source
        self.assertEqual(s.count("      qa01_rf088_rf089_echo:"), 2)
        self.assertIn('QA01_ECHO: ${{ inputs.qa01_rf088_rf089_echo }}', s)
        self.assertIn('"$QA01_ECHO" == "true" && "$QA01_RF084" != "true"', s)
        self.assertIn("RF088/RF089 echo requires the paired RF083/RF084 Zoo case", s)
        self.assertIn('"$QA01_APU_PHASE" == "true"', s)
        self.assertNotIn("schedule:", s)

    def test_disposable_patch_after_generated_writer_before_build(self):
        s = self.source
        writer = s.index("python3 tools/qa01_rf086_native_first_boundary_commit.py --root baldosa")
        echo = s.index("python3 tools/qa01_rf088_native_apu_echo_window.py --root baldosa")
        build = s.index("cmake -S baldosa -B baldosa/build")
        self.assertLess(writer, echo)
        self.assertLess(echo, build)
        self.assertIn("test_qa01_rf088_native_apu_echo_window.py", s)
        self.assertIn("python3 tools/qa01_rf083_original_sound_dp_first_writer.py", s)

    def test_runtime_opt_ins_only_when_requested(self):
        s = self.source
        start = s.index('          if [[ "$QA01_ECHO" == "true" ]]; then',
                        s.index("          # Never set the opt-in names"))
        end = s.index("          set +e", start)
        block = s[start:end]
        self.assertIn("export UR_QA01_RF088_NATIVE_APU_ECHO=1", block)
        self.assertIn("export UR_QA01_RF089_ORIGINAL_ECHO=1", block)
        self.assertNotIn("=0", block)
        self.assertLess(end, s.index("python3 tools/probe_original_event_complete.py"))

    def test_existing_one_file_guarded_request_passes_echo_opt_in(self):
        wrapper = WRAPPER.read_text(encoding="utf-8")
        self.assertIn('      qa01_rf084_native_sound_dp: true', wrapper)
        self.assertIn('      qa01_rf088_rf089_echo: true', wrapper)
        self.assertIn('docs/qa01/REQUEST-ZOO-CAUSAL.md', wrapper)
        self.assertIn('tools/ci_playtest_request_guard.py', wrapper)
        self.assertIn('cancel-in-progress: false', wrapper)
        self.assertNotIn('schedule:', wrapper)

    def test_executed_rows_and_overflow_fail_closed(self):
        s = self.source
        self.assertIn("QA01RF089ORIG_TRUNCATED", s)
        self.assertIn("QA01RF088NATIVE_TRUNCATED", s)
        self.assertIn("for pc in 028301 028304", s)
        self.assertIn("QA01RF088NATIVE .*kind=R .*addr=2142", s)
        self.assertIn("observer-off control and clock registration still required", s)
        self.assertIn("replay/reference.log", s)
        self.assertIn("replay/native.log", s)


if __name__ == "__main__":
    unittest.main()
