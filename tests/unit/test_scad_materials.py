"""Pure ART-4K source-material extraction tests, with optional real OpenSCAD."""
import importlib.util
import tempfile
import subprocess
import shutil
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "art" / "scad_materials.py"
spec = importlib.util.spec_from_file_location("scad_materials", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
materials_for_part = module.materials_for_part
material_pass_source = module.material_pass_source
uncolored_probe_source = module.uncolored_probe_source

SOURCE = '''
$fn=24;
rig_color=is_undef(rig_color)?[0.11,0.35,0.87]:rig_color;
module helper() { color([0.9,0.1,0.1]) sphere(0.4); }
module tire() {
  color([0.075,0.083,0.09]) torus();
  color([0.14,0.16,0.16]) torus();
}
module torus() { rotate_extrude() translate([1,0,0]) circle(r=0.2); }
module fork_and_frame() { color(rig_color) cube(1); helper(); }
module shared_rig() { tire(); fork_and_frame(); }
// color([1,0,0]) must not be interpreted as source geometry
/* color([0,0,1]) is also inert */
shared_rig();
'''

class MaterialContract(unittest.TestCase):
    def test_source_owned_part_and_recursive_helper_colors(self):
        self.assertEqual(materials_for_part(SOURCE, 'tire'),
                         [(19,21,23,255),(36,41,41,255)])
        self.assertEqual(materials_for_part(SOURCE, 'fork_and_frame'),
                         [(28,89,222,255),(230,26,26,255)])
        self.assertEqual(len(materials_for_part(SOURCE, 'shared_rig')), 4)

    def test_actual_unmodified_blockout_material_groups(self):
        source = (SCRIPT.parent / "candidates" / "unicycle_shared_rig.scad").read_text()
        expected = {"tire": 2, "rim_and_hub": 5, "fork_and_frame": 4,
                    "pedals": 3, "saddle": 2}
        for part, count in expected.items():
            with self.subTest(part=part):
                colors = materials_for_part(source, part)
                self.assertEqual(len(colors), count)
                self.assertEqual(len(set(colors)), count)
                self.assertTrue(all(len(c) == 4 for c in colors))

    def test_material_filter_keeps_only_selected_source_colors(self):
        red = (230,26,26,255)
        filtered = material_pass_source(SOURCE, red)
        self.assertIn('if (true) sphere(0.4)', filtered)
        self.assertIn('if (false) cube(1)', filtered)
        self.assertIn('// color([1,0,0])', filtered)
        self.assertIn('/* color([0,0,1])', filtered)
        self.assertEqual(filtered.count('if (true)'), 1)
        self.assertEqual(filtered.count('if (false)'), 3)


    def test_uncolored_probe_filters_all_colored_children(self):
        probe = uncolored_probe_source(SOURCE)
        self.assertEqual(probe.count('if (false)'), 4)
        self.assertIn('translate([100,100,100]) cube([1,1,1]);', probe)
        self.assertIn('// color([1,0,0])', probe)

    @unittest.skipUnless(shutil.which('openscad'), 'optional OpenSCAD not installed')
    def test_real_openscad_uncolored_geometry_probe(self):
        try:
            import trimesh
        except ImportError:
            self.skipTest('optional trimesh not installed')
        clean = SOURCE.replace('shared_rig();', 'fork_and_frame();')
        leaked = clean.replace('helper(); }',
                               'helper(); translate([4,0,0]) cube(1); }')
        self.assertNotEqual(clean, leaked)
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            for label, source in [('clean', clean), ('leaked', leaked)]:
                scad = root / (label + '.scad')
                stl = root / (label + '.stl')
                scad.write_text(uncolored_probe_source(source))
                run = subprocess.run(['openscad', '-o', str(stl), str(scad)],
                                     capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stderr)
                mesh = trimesh.load_mesh(stl, file_type='stl', process=True)
                clean_bounds = [[100, 100, 100], [101, 101, 101]]
                if label == 'clean':
                    self.assertEqual(mesh.bounds.tolist(), clean_bounds)
                    self.assertAlmostEqual(mesh.volume, 1.0)
                    self.assertEqual(len(mesh.faces), 12)
                else:
                    self.assertNotEqual(mesh.bounds.tolist(), clean_bounds)
                    self.assertGreater(mesh.volume, 1.0)

    def test_ambiguous_color_source_fails_closed(self):
        for broken in (SOURCE.replace('color(rig_color)', 'color(variable_color)'),
                       SOURCE.replace('color(rig_color)', 'color([2,0,0])'),
                       SOURCE.replace('color(rig_color)', 'color([0.2,0.3])'),
                       SOURCE.replace('module tire()', 'module missing()'),
                       SOURCE.replace('rig_color=is_undef(rig_color)?[0.11,0.35,0.87]:rig_color;',
                                      'rig_color=[0.1,0.2,0.3];')):
            with self.subTest(broken=broken[:80]), self.assertRaises(ValueError):
                if 'module missing()' in broken:
                    materials_for_part(broken,'tire')
                else:
                    material_pass_source(broken,(28,89,222,255))

    @unittest.skipUnless(shutil.which('openscad'), 'optional OpenSCAD not installed')
    def test_real_openscad_isolates_material_geometry(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            for i, color in enumerate(materials_for_part(SOURCE, 'tire')):
                scad = root / f'material-{i}.scad'
                stl = root / f'material-{i}.stl'
                scad.write_text(material_pass_source(SOURCE,color))
                p = subprocess.run(['openscad','-o',str(stl),str(scad)],
                                   capture_output=True,text=True,timeout=30)
                self.assertEqual(p.returncode,0,p.stderr)
                self.assertGreater(stl.stat().st_size,200)

if __name__ == '__main__':
    unittest.main()
