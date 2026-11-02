"""Shared OpenSCAD declaration safety for all ART-4K pose export routes."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/art/export_articulated_unicycle.py"
spec = importlib.util.spec_from_file_location("export_articulated_unicycle", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)
SOURCE = (ROOT / "tools/art/candidates/unicycle_shared_rig.scad").read_text()


def injected(declaration: str) -> str:
    assert SOURCE.count("rig(rig_pose);") == 1
    return SOURCE.replace("rig(rig_pose);", declaration + "\nrig(rig_pose);")


class SharedDeclarationGuardTests(unittest.TestCase):
    def test_canonical_named_and_custom_source_remains_valid(self):
        exporter.source_without_entrypoint(SOURCE)
        for name in exporter.POSES:
            with self.subTest(name=name):
                exporter.pose_recipe(SOURCE, name)

    def test_builtin_module_shadows_fail_before_any_pose_export(self):
        for name in ("rotate", "translate", "color"):
            altered = injected(f"module {name}(v=0) {{ children(); }}")
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "builtin module shadowed"):
                    exporter.source_without_entrypoint(altered)
                with self.assertRaisesRegex(ValueError, "builtin module shadowed"):
                    exporter.pose_recipe(altered, "wheelie")
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    src = root / "shadow.scad"
                    src.write_text(altered)
                    for pose in ("wheelie", "custom"):
                        out = root / pose
                        out.mkdir()
                        pointer = out / "articulated_blockout_current.json"
                        previous = '{"attempt_id":"previous-success"}\n'
                        pointer.write_text(previous)
                        with self.assertRaisesRegex(ValueError, "builtin module shadowed"):
                            exporter.export(src, out, rig_pose=pose)
                        self.assertEqual(pointer.read_text(), previous)
                        state = json.loads((out / "articulated_blockout_last_attempt.json").read_text())
                        self.assertEqual(state["status"], "failed")
                        self.assertFalse(state["current_output_usable"])

    def test_builtin_function_shadows_fail_for_named_and_custom(self):
        for name in ("sin", "is_undef"):
            altered = injected(f"function {name}(x)=0;")
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "builtin function shadowed"):
                    exporter.source_without_entrypoint(altered)
                with self.assertRaisesRegex(ValueError, "builtin function shadowed"):
                    exporter.pose_recipe(altered, "wheelie")

    def test_comment_only_declarations_do_not_block_valid_poses(self):
        altered = injected("// module rotate(a) { children(); }\n"
                           "/* module translate(v) { children(); }\n"
                           "   function sin(x)=0; */")
        exporter.source_without_entrypoint(altered)
        exporter.pose_recipe(altered, "wheelie")


if __name__ == "__main__":
    unittest.main()
