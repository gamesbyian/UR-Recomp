import unittest

from tools.measure_racer_hd_source_visibility import analyze


def frame(number, top, bottom):
    return (
        f"UR_RACER_HD_CENSUS frame={number} phase=present "
        "status=hd reason=full-pair\n"
        f"UR_RACER_HD_SOURCE_OBJ frame={number} "
        f"top_opaque={top} bottom_opaque={bottom} "
        f"top_painted={int(top > 0)} bottom_painted={int(bottom > 0)}"
    )


class RacerOriginalObjSourceVisibilityTests(unittest.TestCase):
    def test_native_visible_source_top_only_and_bottom_only_sequences(self):
        log = "\n".join([
            frame(1220, 372, 0),
            frame(1221, 374, 0),
            frame(1222, 0, 181),
            frame(1224, 10, 10),
        ])
        result = analyze(log, 1220, 1224)
        m = result["measurement"]
        self.assertEqual(m["hd_guest_frames"], 4)
        self.assertEqual(m["top_obj_absent_frames"], 1)
        self.assertEqual(m["bottom_obj_absent_frames"], 2)
        self.assertEqual(m["top_only_obj_frames"], 2)
        self.assertEqual(m["bottom_only_obj_frames"], 1)
        self.assertEqual(m["both_obj_present_frames"], 1)
        self.assertEqual(m["adjacent_hd_guest_edges"], 2)
        self.assertEqual(m["top_source_visibility_switches"], 1)
        self.assertEqual(m["bottom_source_visibility_switches"], 1)
        self.assertEqual(result["examples"]["bottom_obj_absent"], [1220, 1221])

    def test_zero_source_is_counted_without_fabricating_visible_rider(self):
        result = analyze(frame(1300, 0, 0), 1300, 1300)
        self.assertEqual(result["measurement"]["both_obj_absent_frames"], 1)
        self.assertEqual(result["measurement"]["bottom_obj_absent_frames"], 1)

    def test_individual_footprints_prevent_same_viewport_phantom(self):
        # Two riders may share one viewport but be spatially disjoint.
        # Only the first emitted source OBJ pixels. A viewport-level
        # top_opaque=9 would otherwise authorize both host drawings.
        log = (
            frame(1220, 9, 0) + "\n"
            "UR_RACER_HD_SOURCE_FOOTPRINTS frame=1220 count=4 "
            "alpha0=9 alpha1=0 alpha2=0 alpha3=0"
        )
        result = analyze(log, 1220, 1220)
        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(result["footprint_measurement"]["empty_footprints"], 3)
        self.assertEqual(
            result["footprint_measurement"]["one_empty_top_rider_footprint_frames"], 1
        )
        self.assertEqual(result["footprint_measurement"]["nonempty_footprints"], 1)

    def test_p1_only_footprint_order_and_malformed_counts(self):
        log = (
            frame(1300, 3, 2).replace("full-pair", "p1-only") + "\n"
            "UR_RACER_HD_SOURCE_FOOTPRINTS frame=1300 count=2 "
            "alpha0=3 alpha1=2 alpha2=0 alpha3=0"
        )
        self.assertEqual(
            analyze(log, 1300, 1300)["footprint_measurement"]["p1_only_frames"], 1
        )
        with self.assertRaisesRegex(ValueError, "summary disagreement"):
            analyze(log.replace("alpha0=3", "alpha0=4"), 1300, 1300)
        with self.assertRaisesRegex(ValueError, "inactive P1-only"):
            analyze(log.replace("alpha2=0", "alpha2=1"), 1300, 1300)
        with self.assertRaisesRegex(ValueError, "duplicate OBJ footprint"):
            analyze(log + "\n" + log.splitlines()[-1], 1300, 1300)
        with self.assertRaisesRegex(ValueError, "does not match HD source"):
            analyze(
                log + "\nUR_RACER_HD_SOURCE_FOOTPRINTS frame=1301 "
                "count=2 alpha0=0 alpha1=0 alpha2=0 alpha3=0",
                1300, 1301
            )

    def test_missing_duplicate_and_incorrect_paint_witness_fail(self):
        with self.assertRaisesRegex(ValueError, "no real HD"):
            analyze("", 1220, 1220)
        with self.assertRaisesRegex(ValueError, "does not match"):
            analyze(
                "UR_RACER_HD_CENSUS frame=1220 phase=present status=hd reason=full-pair",
                1220, 1220
            )
        with self.assertRaisesRegex(ValueError, "duplicate OBJ"):
            analyze(frame(1220, 1, 0) + "\n" + frame(1220, 1, 0), 1220, 1220)
        with self.assertRaisesRegex(ValueError, "source-empty viewport"):
            analyze(
                frame(1220, 1, 0).replace("bottom_painted=0", "bottom_painted=1"),
                1220, 1220
            )
        with self.assertRaisesRegex(ValueError, "invalid inclusive"):
            analyze(frame(1220, 1, 1), 1230, 1220)


if __name__ == "__main__":
    unittest.main()
