import importlib.util
import pathlib
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / 'tools/art/scad_materials.py'
spec = importlib.util.spec_from_file_location('scad_materials', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SOURCE = '''
rig_color=is_undef(rig_color)?[0.11,0.35,0.87]:rig_color;
module helper() { color([0.9,0.1,0.1]) sphere(0.4); }
module fork() { color(rig_color) cube(1); helper(); }
module tire() { color([0.1,0.1,0.1]) cylinder(r=1,h=1); }
'''

class CsgSafety(unittest.TestCase):
    def test_mixed_material_subtraction_rejected(self):
        bad = SOURCE.replace('module fork() { color(rig_color) cube(1); helper(); }',
                             'module fork() { difference(){ color(rig_color) cube(1); helper(); } }')
        with self.assertRaisesRegex(ValueError, 'whole-part material equivalence'):
            module.materials_for_part(bad, 'fork')

    def test_reachable_helper_intersection_rejected(self):
        bad = SOURCE.replace('module helper() { color([0.9,0.1,0.1]) sphere(0.4); }',
                             'module helper() { intersection(){ color([0.9,0.1,0.1]) sphere(0.4); cube(1); } }')
        with self.assertRaisesRegex(ValueError, 'whole-part material equivalence'):
            module.materials_for_part(bad, 'fork')

    def test_unrelated_csg_does_not_block_source_part(self):
        source = SOURCE + '\nmodule unused() { difference(){ cube(2); cube(1); } }\n'
        self.assertEqual(module.materials_for_part(source, 'tire'), [(26,26,26,255)])

    def test_current_additive_hull_and_minkowski_remain_supported(self):
        source = SOURCE.replace('cube(1); helper();',
                                'hull(){ cube(1); sphere(0.1); } helper();')
        self.assertEqual(len(module.materials_for_part(source, 'fork')), 2)

if __name__ == '__main__': unittest.main()
