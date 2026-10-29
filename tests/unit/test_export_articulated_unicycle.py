"""Pure contract tests for the optional ART-4K articulated WIP exporter."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "art" / "export_articulated_unicycle.py"
spec = importlib.util.spec_from_file_location("export_articulated_unicycle", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ArticulatedBlockoutContract(unittest.TestCase):
    def test_source_entrypoint_exactly_once_at_end(self):
        source = "module rig(x) {}\nrig(rig_pose);\n"
        self.assertEqual(module.source_without_entrypoint(source), "module rig(x) {}\n")
        for invalid in ("rig(rig_pose);\nrig(rig_pose);", "module rig(x) {}", "rig(rig_pose);\nother();"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    module.source_without_entrypoint(invalid)

    def test_parts_do_not_accidentally_render_full_rig(self):
        source = "module rig(x) {}\nrig(rig_pose);\n"
        for name in module.PARTS:
            with self.subTest(name=name):
                text = module.component_source(source, name)
                self.assertNotIn("rig(rig_pose);", text)
                self.assertTrue(text.rstrip().endswith(module.PARTS[name][0]))
        with self.assertRaises(ValueError):
            module.component_source(source, "unknown")

    def test_saddle_pivot_is_independent_of_wheel_pivot(self):
        self.assertEqual(module.part_translation("saddle"), (0.04, 0.0, 3.27))
        for name in ("tire", "rim_and_hub", "fork_and_frame", "pedals"):
            self.assertEqual(module.part_translation(name), (0.0, 0.0, 1.0))
        with self.assertRaises(ValueError):
            module.part_translation("fake")


if __name__ == "__main__":
    unittest.main()
