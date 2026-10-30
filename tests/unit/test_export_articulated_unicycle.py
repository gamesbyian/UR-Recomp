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

    def test_extra_top_level_geometry_fails_closed_without_clobbering_pointer(self):
        source = (SCRIPT.parent / "candidates" / "unicycle_shared_rig.scad").read_text()
        self.assertTrue(module.component_source(source, "saddle").endswith("saddle(0);\n"))
        for injected in ("tire();",
                         "translate([0,0,0]) { tire(); }",
                         "assert(true) tire();"):
            changed = source.replace("rig(rig_pose);",
                                     injected + "\nrig(rig_pose);")
            with self.subTest(injected=injected):
                with self.assertRaisesRegex(ValueError, "top-level geometry"):
                    module.component_source(changed, "saddle")
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            out = root / "out"
            out.mkdir()
            pointer = out / "articulated_blockout_current.json"
            old_pointer = '{"attempt_id":"previous-success","status":"succeeded"}\n'
            pointer.write_text(old_pointer, encoding="utf-8")
            scad = root / "extra-call.scad"
            scad.write_text(source.replace("rig(rig_pose);",
                                           "tire();\nrig(rig_pose);"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "top-level geometry"):
                module.export(scad, out)
            status = json.loads((out / "articulated_blockout_last_attempt.json").read_text())
            self.assertEqual(status["status"], "failed")
            self.assertFalse(status["current_output_usable"])
            self.assertEqual(pointer.read_text(encoding="utf-8"), old_pointer)

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
        # Commented-out declarations must not invalidate a real source module.
        comments = source + "\n// module saddle(lean=0) {}\n/* module saddle(lean=0) {} */"
        self.assertEqual(module.saddle_mount_from_source(comments), mount)
        differently_formed = (source +
            "\nmodule saddle(lean=0) {translate([0.5,0,2.5]) scale([1,1,1]) {}}")
        with self.assertRaisesRegex(ValueError, "saddle module declaration"):
            module.saddle_mount_from_source(differently_formed)
        for invalid in ("module saddle(lean=0) {translate([0,0,0])}",
                        source + source, "module saddle(lean=0) { rotate([0,0,0]) {} }"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    module.saddle_mount_from_source(invalid)
        with self.assertRaises(ValueError):
            module.part_translation("fake", mount)

    def test_ambiguous_saddle_export_preserves_previous_success_pointer(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            out = root / "out"
            out.mkdir()
            pointer = out / "articulated_blockout_current.json"
            old_pointer = '{"attempt_id":"previous-success","status":"succeeded"}\n'
            pointer.write_text(old_pointer, encoding="utf-8")
            source = root / "ambiguous.scad"
            source.write_text(
                "module rig(p) {}\n"
                "module saddle(lean=0) { translate([0.04,0,2.27]) rotate([0,lean,0]) {} }\n"
                "module saddle(lean=0) { translate([0.5,0,2.5]) scale([1,1,1]) {} }\n"
                "rig(rig_pose);\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "saddle module declaration"):
                module.export(source, out)
            status = json.loads((out / "articulated_blockout_last_attempt.json").read_text())
            self.assertEqual(status["status"], "failed")
            self.assertFalse(status["current_output_usable"])
            self.assertEqual(pointer.read_text(encoding="utf-8"), old_pointer)

    def test_five_named_poses_derive_controls_and_transforms_from_source(self):
        source = (SCRIPT.parent / "candidates" / "unicycle_shared_rig.scad").read_text()
        expected = {"upright": (18, 0), "pedal": (88, -5),
                    "wheelie": (44, 12), "stunt": (120, -9),
                    "bank": (150, 4)}
        for name, (phase, lean) in expected.items():
            with self.subTest(name=name):
                p, l, transform = module.pose_recipe(source, name)
                self.assertEqual((p, l), (phase, lean))
                self.assertEqual(transform[3], (0., 0., 0., 1.))
                self.assertTrue(all(math.isfinite(v) for row in transform for v in row))
                self.assertTrue(module.component_source(source, "pedals", pedal_phase=p)
                                .endswith(f"pedals({phase});\n"))
                self.assertTrue(module.component_source(source, "saddle", saddle_lean=l)
                                .endswith(f"saddle({lean});\n"))
        self.assertEqual(module.pose_recipe(source, "upright")[2], module._identity())
        self.assertEqual(module.pose_recipe(source, "pedal")[2], module._identity())
        wheelie = module.pose_recipe(source, "wheelie")[2]
        self.assertAlmostEqual(wheelie[2][3], 0.16)
        self.assertAlmostEqual(wheelie[0][2], -math.sin(math.radians(28)))
        stunt = module.pose_recipe(source, "stunt")[2]
        self.assertAlmostEqual(stunt[0][3], 1.8 * math.sin(math.radians(130)))
        self.assertAlmostEqual(stunt[2][3], 1.8 * (1 - math.cos(math.radians(130))))
        bank = module.pose_recipe(source, "bank")[2]
        self.assertAlmostEqual(bank[2][1], math.sin(math.radians(11)))
        self.assertAlmostEqual(bank[1][0], -math.sin(math.radians(8)))

    def test_named_pose_parser_rejects_changed_or_ambiguous_source(self):
        source = (SCRIPT.parent / "candidates" / "unicycle_shared_rig.scad").read_text()
        for name in ("fake", "ride", "stunt_cycle"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                module.pose_recipe(source, name)
        for broken in (
            source.replace('else if(p=="wheelie")', 'else if(p=="wheelie") scale([1,2,3])'),
            source.replace('else if(p=="wheelie")', 'else if(p=="wheelie") shared_rig(pedal=1,seat_lean=1); else if(p=="wheelie")'),
            source.replace('shared_rig(pedal=44,seat_lean=12);', 'shared_rig(pedal=44,seat_lean=12); extra();'),
        ):
            with self.subTest(broken=broken[:70]), self.assertRaises(ValueError):
                module.pose_recipe(broken, "wheelie")
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            scad = root / "source.scad"
            scad.write_text(source)
            with self.assertRaisesRegex(ValueError, "named source pose cannot override"):
                module.export(scad, root / "out", rig_pose="wheelie", pedal_phase=90)
            status = json.loads((root / "out" / "articulated_blockout_last_attempt.json").read_text())
            self.assertEqual(status["status"], "failed")
            self.assertFalse(status["current_output_usable"])

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
            with self.assertRaisesRegex(ValueError, "saddle"):
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
