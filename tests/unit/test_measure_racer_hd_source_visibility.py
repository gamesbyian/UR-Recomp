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
