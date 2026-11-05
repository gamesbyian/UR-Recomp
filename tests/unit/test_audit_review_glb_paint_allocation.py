"""Model-only original-GLB material reallocation, without a pose/IoU oracle."""
import unittest
from pathlib import Path

from tools.art.audit_review_glb_paint_allocation import (
    BLUE, CAMERA_SHA, MODEL_SHA, MODEL_URL, POLICIES, SCHEMA,
    evaluate_owner_labels,
)


def fixture():
    names = [
        BLUE, "rim_and_hub__material_1", "rim_and_hub__material_2",
        "pedals__material_0", "pedals__material_1",
        *(f"other_material_{i}" for i in range(11)),
    ]
    owners, ties = [-1] * 4096, [False] * 4096

    def add(name, coords):
        index = names.index(name)
        for x, y in coords:
            owners[y * 64 + x] = index

    # The 2026 blue fork extends 12 pixels *above* the 7px wheel rim,
    # and three pixels inside its disc. Added rim/crank paint is only
    # material relabelling, not any camera, axle or mesh transformation.
    add(BLUE, [(x, 20) for x in range(10, 22)] +
        [(32,32),(33,32),(34,32)])
    add("rim_and_hub__material_1", [(32,y) for y in range(33,37)])
    add("rim_and_hub__material_2", [(x,29) for x in range(28,34)])
    add("pedals__material_1", [(x,34) for x in range(34,37)])
    add("pedals__material_0", [(x,32) for x in range(35,37)])
    return owners, ties, names


class VisibleModelPaintAllocationTests(unittest.TestCase):
    def test_frozen_viewer_palette_modes_and_real_source_sha(self):
        self.assertEqual(list(POLICIES), ["original","area","disc","discPlus"])
        self.assertEqual(MODEL_SHA,
            "d2a2beee85f63fa074f1fa7294c5cd7522f376f9d4b02354e97c0702dda3fa7f")
        self.assertTrue(MODEL_URL.endswith("upright-d2a2beee85f63fa0.glb"))
        self.assertEqual(CAMERA_SHA,
            "1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028")
        page = (Path(__file__).resolve().parents[2] /
                "tools/art/model-review/index.html").read_text(encoding="utf-8")
        for item in ("area", "disc", "discPlus"):
            self.assertIn(item, page)
        for name in ("rim_and_hub__material_1", "rim_and_hub__material_2",
                     "pedals__material_0", "pedals__material_1"):
            self.assertIn(name, page)

    def test_exact_frontmost_pixel_census_under_material_only_reassignment(self):
        owners, ties, names = fixture()
        report = evaluate_owner_labels(owners, ties, names, centre=(32.,32.))
        self.assertEqual(report["original"]["depth_visible_painted_pixels"],15)
        self.assertEqual(report["original"]["painted_pixels_inside_7px_wheel_disc"],3)
        self.assertEqual(report["original"]["painted_fraction_inside_7px_wheel_disc"],.2)
        self.assertEqual(report["area"]["painted_pixels_inside_7px_wheel_disc"],10)
        self.assertEqual(report["disc"]["painted_pixels_inside_7px_wheel_disc"],12)
        self.assertEqual(report["discPlus"]["painted_pixels_inside_7px_wheel_disc"],14)
        self.assertEqual(report["discPlus"]["depth_visible_painted_pixels"],26)
        self.assertEqual(report["discPlus"]["painted_fraction_inside_7px_wheel_disc"],
                         round(14/26,8))
        self.assertEqual(report["original"]["painted_fraction_at_or_below_wheel_top"],.2)

    def test_depth_tie_is_unowned_even_when_new_paint_policy_includes_both(self):
        owners, ties, names = fixture()
        original = evaluate_owner_labels(owners, ties, names, centre=(32,32))
        ties[29*64+28] = True  # real model ambiguity must not count as painted
        changed = evaluate_owner_labels(owners, ties, names, centre=(32,32))
        self.assertEqual(changed["original"],original["original"])
        self.assertEqual(changed["disc"]["painted_pixels_inside_7px_wheel_disc"],11)
        self.assertEqual(changed["discPlus"]["painted_pixels_inside_7px_wheel_disc"],13)

    def test_rejects_absent_model_material_bad_camera_and_malformed_masks(self):
        owners, ties, names = fixture()
        cases = [
            (owners[:-1],ties,names,(32.,32.),7),
            (owners,ties[:-1],names,(32.,32.),7),
            (owners,ties,names[:-1],(32.,32.),7),
            (owners,ties,names[:-1]+[names[0]],(32.,32.),7),
            (owners,ties,names,(float("nan"),32.),7),
            (owners,ties,names,(32.,32.),8),
            (owners,ties,names,True,7),
        ]
        for source,tied,material,centre,radius in cases:
            with self.subTest(values=(len(source),len(tied),len(material),centre,radius)):
                with self.assertRaises((TypeError,ValueError)):
                    evaluate_owner_labels(source,tied,material,centre=centre,radius=radius)
        owners[0] = 16
        with self.assertRaises(ValueError):
            evaluate_owner_labels(owners,ties,names,centre=(32,32))


if __name__ == "__main__":
    unittest.main()
