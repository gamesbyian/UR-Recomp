import importlib.util
import pathlib
import shutil
import subprocess
import tempfile
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

    def test_cross_color_hull_rejected(self):
        bad = SOURCE.replace('color(rig_color) cube(1); helper();',
                             'hull(){ color(rig_color) cube(1); color([0.9,0.1,0.1]) sphere(0.4); }')
        with self.assertRaisesRegex(ValueError, 'whole-part material equivalence'):
            module.materials_for_part(bad, 'fork')

    def test_cross_color_minkowski_rejected(self):
        bad = SOURCE.replace('color(rig_color) cube(1); helper();',
                             'minkowski(){ color(rig_color) cube(1); color([0.9,0.1,0.1]) sphere(0.4); }')
        with self.assertRaisesRegex(ValueError, 'whole-part material equivalence'):
            module.materials_for_part(bad, 'fork')

    def test_cross_color_hull_via_helper_modules_rejected(self):
        bad = SOURCE.replace('color(rig_color) cube(1); helper();',
                             'hull(){ helper(); other(); }') + '\nmodule other(){ color(rig_color) cube(1); }\n'
        with self.assertRaisesRegex(ValueError, 'whole-part material equivalence'):
            module.materials_for_part(bad, 'fork')

    def test_single_color_hull_remains_supported(self):
        good = SOURCE.replace('color(rig_color) cube(1); helper();',
                              'hull(){ color(rig_color) cube(1); color(rig_color) sphere(0.4); } helper();')
        self.assertEqual(len(module.materials_for_part(good, 'fork')), 2)

    def test_unreachable_cross_color_hull_does_not_block_part(self):
        source = SOURCE + '\nmodule unused(){ hull(){ color(rig_color) cube(1); color([0.9,0.1,0.1]) sphere(1); } }\n'
        self.assertEqual(module.materials_for_part(source, 'tire'), [(26,26,26,255)])

    def test_real_openscad_cross_color_csg_loses_volume_when_split(self):
        if not shutil.which('openscad'):
            self.skipTest('OpenSCAD unavailable')
        try:
            import trimesh
        except ImportError:
            self.skipTest('trimesh unavailable')
        cases = {
            'hull': ('color([1,0,0])translate([-3,0,0])sphere(1,$fn=24);'
                     'color([0,0,1])translate([3,0,0])sphere(1,$fn=24);'),
            'minkowski': ('color([1,0,0])cube([2,2,2],center=true);'
                          'color([0,0,1])sphere(1,$fn=20);'),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for operator, children in cases.items():
                with self.subTest(operator=operator):
                    source = SOURCE + f'\nmodule bad(){{{operator}(){{{children}}}}}\nbad();\n'
                    with self.assertRaisesRegex(ValueError, 'whole-part material equivalence'):
                        module.materials_for_part(source, 'bad')
                    volumes = []
                    for label, text in (
                        ('whole', source),
                        ('red', module.material_pass_source(source, (255, 0, 0, 255))),
                        ('blue', module.material_pass_source(source, (0, 0, 255, 255))),
                    ):
                        scad = pathlib.Path(tmp) / f'{operator}-{label}.scad'
                        stl = pathlib.Path(tmp) / f'{operator}-{label}.stl'
                        scad.write_text(text, encoding='utf-8')
                        run = subprocess.run(['openscad', '-o', str(stl), str(scad)],
                                             capture_output=True, text=True, timeout=30)
                        self.assertEqual(run.returncode, 0, run.stderr)
                        volumes.append(abs(trimesh.load(stl, force='mesh').volume))
                    self.assertGreater(volumes[0], volumes[1] + volumes[2] + 1.0)

    def test_current_additive_hull_and_minkowski_remain_supported(self):
        source = SOURCE.replace('cube(1); helper();',
                                'hull(){ cube(1); sphere(0.1); } helper();')
        self.assertEqual(len(module.materials_for_part(source, 'fork')), 2)

if __name__ == '__main__': unittest.main()
