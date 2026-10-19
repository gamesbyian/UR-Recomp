"""RF076 source-staged interpreter and generated compiled opcode gates."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_rf076_generated_exec_pc_gate as m


def fixture(root, *, sound_missing=(), nmi_emitted=(), location='src/gen', comment=False):
    bridge = root / m.INTERP
    recorder = root / m.RECORDER
    bridge.parent.mkdir(parents=True, exist_ok=True)
    recorder.parent.mkdir(parents=True, exist_ok=True)
    bridge.write_text('const uint8_t  op = bridge_bus_read(cpu, pc_before);\n'
                      '        ur_rf047_mark_executed_pc(pc_before, 0u);\n')
    recorder.write_text('void ur_rf047_mark_executed_pc(uint32_t pc, unsigned tier) {\n'
        + '/* UR_QA01_RF047_EXEC_PC */\n'
        + '/* stage=opcode */\n'
        + ' && '.join(f'pc != 0x{pc:06X}u' for pc in sorted(m.ALL_TARGETS))
        + '\n}\n')
    file = root/location/'bank82_part03_v2.c'
    file.parent.mkdir(parents=True, exist_ok=True)
    sites = (m.SOUND_AOT - set(sound_missing)) | set(nmi_emitted)
    lines = [f'  ur_rf047_mark_executed_pc(0x{pc:06X}u, 1u);' for pc in sorted(sites)]
    file.write_text(('/*\n' + '\n'.join(lines) + '\n*/\n') if comment
                    else '\n'.join(lines) + '\n')
    return file


class GeneratedGate(unittest.TestCase):
    def test_genuine_five_missing_nmi_aot_remain_explicitly_unproven(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root)
            v = m.inspect(root)
            self.assertEqual(v['generated_dir'], 'src/gen')
            self.assertEqual(v['generated_bank_part_count'], 1)
            self.assertEqual(set(v['NMI_candidate_AOT_sites_unmatched_by_narrow_source_regex']),
                             {f'{pc:06X}' for pc in m.NMI_CANDIDATES})
            self.assertTrue(v['actual_interpreter_fetch_hook_source_staged'])
            self.assertFalse(v['NMI_candidate_fetched_opcode_observed_in_native_guest'])
            self.assertFalse(v['unmatched_static_NMI_call_pattern_implies_absent_AOT_code'])
            self.assertFalse(v['actual_native_guest_execution_checked'])
            self.assertEqual(v['accepted_USA_events'], 0)

    def test_existing_aot_nmi_sites_are_recorded_not_assumed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            choice = next(iter(m.NMI_CANDIDATES))
            fixture(root, nmi_emitted={choice})
            v = m.inspect(root)
            self.assertEqual(v['NMI_candidate_AOT_sites_matched_by_narrow_source_regex'], [f'{choice:06X}'])
            self.assertEqual(len(v['NMI_candidate_AOT_sites_unmatched_by_narrow_source_regex']), 4)
            self.assertFalse(v['NMI_candidate_fetched_opcode_observed_in_native_guest'])

    def test_sound_missing_is_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, sound_missing={0x8282F0})
            with self.assertRaisesRegex(ValueError, '8282F0'): m.inspect(root)

    def test_comment_only_generated_source_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, comment=True)
            with self.assertRaisesRegex(ValueError, 'missing generated sound AOT'): m.inspect(root)

    def test_interpreter_fetch_hook_missing_fails_even_if_all_aot_present(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, nmi_emitted=m.NMI_CANDIDATES)
            (root/m.INTERP).write_text('const uint8_t  op = bridge_bus_read(cpu, pc_before);\n')
            with self.assertRaisesRegex(ValueError, 'interpreter opcode fetch hook'): m.inspect(root)

    def test_recorder_filter_missing_nmi_is_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root)
            file = root/m.RECORDER
            file.write_text(file.read_text().replace('pc != 0x82D4EEu', 'pc != 0x008588u'))
            with self.assertRaisesRegex(ValueError, '82D4EE'): m.inspect(root)

    def test_wrong_output_directory_cannot_substitute_for_real_gen(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, location='snesrecomp/runner/src/gen')
            (root/m.GENERATED).mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, 'no published AOT'): m.inspect(root)

    def test_missing_generated_dir_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'generated source missing'):
                m.inspect(Path(d))


if __name__ == '__main__': unittest.main()
