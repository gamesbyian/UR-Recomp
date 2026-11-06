"""Guard real OpenSCAD module redeclarations in source-bound ART-4K poses."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "tools/art/candidates/unicycle_shared_rig.scad").read_text()
MODULE = ROOT / "tools/art/continuous_pose_recipe.py"
spec = importlib.util.spec_from_file_location("continuous_pose_recipe", MODULE)
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


class ModuleRedeclarationTests(unittest.TestCase):
    def test_canonical_source_still_validates(self):
        for pose in ("ride", "stunt_cycle"):
            with self.subTest(pose=pose):
                _, _, _, meta = recipe.continuous_pose_recipe(SOURCE, pose, .25)
                self.assertTrue(meta["source_formula_validated"])

    def test_redefined_user_modules_fail_closed(self):
        # Actual OpenSCAD 2021.01 changes the generated CSG for shared_rig.
        # The formula remains byte-identical; the module binding does not.
        for module in ("shared_rig", "rig", "member", "tire"):
            with self.subTest(module=module):
                mutated = SOURCE + f"\nmodule {module}(different=0) {{ cube(3); }}\n"
                with self.assertRaisesRegex(ValueError, "duplicate OpenSCAD module"):
                    recipe.continuous_pose_recipe(mutated, "ride", .25)

    def test_duplicate_module_in_other_order_is_rejected(self):
        mutated = "module shared_rig(other=1) { sphere(2); }\n" + SOURCE
        with self.assertRaisesRegex(ValueError, "duplicate OpenSCAD module"):
            recipe.continuous_pose_recipe(mutated, "stunt_cycle", .5)

    def test_comments_do_not_create_false_duplicates(self):
        mutated = SOURCE + "\n// module shared_rig(a) { cube(1); }\n"
        mutated += "/* module rig(a) { cube(2); } */\n"
        _, _, _, meta = recipe.continuous_pose_recipe(mutated, "ride", .25)
        self.assertTrue(meta["source_formula_validated"])


if __name__ == "__main__":
    unittest.main()
