"""Pure contract tests for the optional ART-4K articulated WIP exporter."""
import importlib.util
import json
import math
import tempfile
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

    def test_two_pose_controls_change_only_the_owned_components(self):
        source = "module rig(x) {}\nrig(rig_pose);\n"
        for name in ("tire", "rim_and_hub", "fork_and_frame"):
            self.assertEqual(module.component_source(source, name),
                             module.component_source(source, name, pedal_phase=88,
                                                     saddle_lean=-5))
        self.assertTrue(module.component_source(source, "pedals").endswith("pedals(18);\n"))
        self.assertTrue(module.component_source(source, "saddle").endswith("saddle(0);\n"))
        self.assertTrue(module.component_source(source, "pedals", pedal_phase=88).endswith(
            "pedals(88);\n"))
        self.assertTrue(module.component_source(source, "saddle", saddle_lean=-5).endswith(
            "saddle(-5);\n"))
        for phase, lean in ((math.nan, 0), (math.inf, 0), (-361, 0),
                            (361, 0), (18, math.nan), (18, math.inf),
                            (18, -31), (18, 31)):
            with self.subTest(phase=phase, lean=lean):
                with self.assertRaises(ValueError):
                    module.component_source(source, "saddle", pedal_phase=phase,
                                            saddle_lean=lean)

    def test_saddle_pivot_comes_from_geometry_source(self):
        source = "module saddle(lean=0) { translate([0.04,0,2.27])rotate([0,lean,0]) {} }"
        mount = module.saddle_mount_from_source(source)
        self.assertEqual(mount, (0.04, 0.0, 2.27))
        self.assertEqual(module.part_translation("saddle", mount), (0.04, 0.0, 3.27))
        for name in ("tire", "rim_and_hub", "fork_and_frame", "pedals"):
            self.assertEqual(module.part_translation(name, mount), (0.0, 0.0, 1.0))
        moved = source.replace("2.27", "2.91").replace("0.04", "-0.13")
        self.assertEqual(module.part_translation("saddle", module.saddle_mount_from_source(moved)),
                         (-0.13, 0.0, 3.91))
        for invalid in ("module saddle(lean=0) {translate([0,0,0])}",
                        source + source, "module saddle(lean=0) { rotate([0,0,0]) {} }"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    module.saddle_mount_from_source(invalid)
        with self.assertRaises(ValueError):
            module.part_translation("fake", mount)

    def test_failed_rerun_does_not_publish_stale_asset_as_current(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            out = root / "output"
            out.mkdir()
            prior = out / "attempts" / "earlier-success"
            prior.mkdir(parents=True)
            glb = prior / "unicycle_articulated_blockout.glb"
            glb.write_bytes(b"previously valid artifact")
            receipt = prior / "articulated_blockout_receipt.json"
            receipt.write_text('{"previous":true}', encoding="utf-8")
            current = out / "articulated_blockout_current.json"
            old_pointer = '{"attempt_id":"earlier-success","status":"succeeded"}\n'
            current.write_text(old_pointer, encoding="utf-8")
            invalid = root / "invalid.scad"
            invalid.write_text("module rig() {}\nrig(rig_pose);\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "saddle mount"):
                module.export(invalid, out)
            status = json.loads((out / "articulated_blockout_last_attempt.json").read_text())
            self.assertEqual(status["status"], "failed")
            self.assertFalse(status["current_output_usable"])
            self.assertEqual(status["source_sha256"], module.sha256_bytes(invalid.read_bytes()))
            self.assertNotEqual(status["attempt_id"], "earlier-success")
            self.assertEqual(current.read_text(), old_pointer)
            self.assertEqual(glb.read_bytes(), b"previously valid artifact")
            self.assertEqual(receipt.read_text(), '{"previous":true}')


if __name__ == "__main__":
    unittest.main()
