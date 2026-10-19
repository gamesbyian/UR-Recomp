"""RF076 fail-closed published C provenance tests. Never credit guest execution."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_rf076_generated_exec_pc_gate as gate


class GeneratedGate(unittest.TestCase):
    def fixture(self, root, *, missing=(), location='src/gen', comment=False):
        file = root / location / 'bank82_part03_v2.c'
        file.parent.mkdir(parents=True, exist_ok=True)
        lines = [f'  ur_rf047_mark_executed_pc(0x{pc:06X}u, 1u);'
                 for pc in sorted(gate.REQUIRED - set(missing))]
        file.write_text(('/*\n' + '\n'.join(lines) + '\n*/\n')
                        if comment else '\n'.join(lines) + '\n')
        return file

    def test_published_target_calls_only_are_qualified(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.fixture(root)
            report = gate.inspect(root)
            self.assertEqual(report['generated_dir'], 'src/gen')
            self.assertEqual(report['generated_bank_part_count'], 1)
            self.assertTrue(report['static_generated_calls_present'])
            self.assertEqual(set(report['marker_bearing_translation_units'][0]['site_counts']),
                             {f'{x:06X}' for x in gate.REQUIRED})
            self.assertFalse(report['actual_guest_opcode_executed'])
            self.assertFalse(report['original_native_same_semantic_phase'])
            self.assertEqual(report['accepted_USA_events'], 0)

    def test_old_wrong_output_path_and_checkout_decoys_rejected(self):
        for location in ('snesrecomp/runner/src/gen', 'misc', 'src/gen/decomp'):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                self.fixture(root, location=location)
                if not (root/'src/gen').exists():
                    (root/'src/gen').mkdir(parents=True)
                with self.assertRaisesRegex(ValueError, 'no published AOT'):
                    gate.inspect(root)

    def test_comment_marker_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.fixture(root, comment=True)
            with self.assertRaisesRegex(ValueError, 'missing generated opcode-PC targets'):
                gate.inspect(root)

    def test_partial_bank_still_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            pc = min(gate.REQUIRED)
            self.fixture(root, missing={pc})
            with self.assertRaisesRegex(ValueError, f'{pc:06X}'):
                gate.inspect(root)

    def test_declaration_does_not_count(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            file = self.fixture(root)
            file.write_text('extern void ur_rf047_mark_executed_pc(uint32_t, unsigned);\n')
            with self.assertRaisesRegex(ValueError, 'missing generated opcode-PC targets'):
                gate.inspect(root)

    def test_extra_generated_files_cannot_substitute_for_bank_part(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            file = self.fixture(root)
            decoy = file.with_name('unrelated.c')
            file.rename(decoy)
            with self.assertRaisesRegex(ValueError, 'no published AOT'):
                gate.inspect(root)

    def test_no_generated_path_is_diagnostic(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'generated source missing'):
                gate.inspect(Path(d))

    def test_published_multiple_bank_parts(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            file = self.fixture(root)
            lines = file.read_text().splitlines()
            file.write_text('\n'.join(lines[:4]))
            (file.parent/'bank82_part04_v2.c').write_text('\n'.join(lines[4:]))
            report = gate.inspect(root)
            self.assertEqual(report['generated_bank_part_count'], 2)
            self.assertEqual(len(report['marker_bearing_translation_units']), 2)


if __name__ == '__main__':
    unittest.main()
