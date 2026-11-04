"""Original Mesen/actual 2026 GLB part attribution, without invented anatomy."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.art.attribute_original_mesen_upper_to_real_glb_parts import (
    ARMS, UPPER_EVENTS, SCHEMA, PARTS, union_planes, attribute_bands,
    main, analyze, FROZEN_EVEN_SOURCE_CENTRE,
)
from tools.art.score_original_mesen24_fixed_pivot_glb import source_center



class FrozenOriginalSourceAttributionTests(unittest.TestCase):
    def test_selected_authentic_upper_events_are_never_reselected_by_iou(self):
        self.assertEqual(UPPER_EVENTS,{"blue":(1602,1603),"red":(1605,1606)})
        self.assertEqual(ARMS,(
            "absolute_wheel_axle_root","reference_relative_midbody_root"))
        self.assertIn("PARENT-ATTRIBUTION",SCHEMA)

    def test_frozen_even_source_calibration_is_distinct_from_full_census(self):
        self.assertEqual(FROZEN_EVEN_SOURCE_CENTRE,(31.515625,19.578125))
        # A fully controlled 64-angle fixture with one x half-pixel offset
        # and five y half-pixel offsets among the 32 even states.
        boxes={str(k):[31,19,32,20] for k in range(64)}
        boxes["2"]=[32,20,32,20]
        for k in (4,6,8,10):
            boxes[str(k)]=[31,20,32,20]
        axis={"source_phase_variation_bbox_by_ROM_angle_index":boxes}
        self.assertEqual(source_center(axis),FROZEN_EVEN_SOURCE_CENTRE)
        # The original all-orientation census is a different denominator:
        # odd entries must not leak into this fitted even-only source null.
        boxes["3"]=[0,0,63,63]
        self.assertEqual(source_center(axis),FROZEN_EVEN_SOURCE_CENTRE)
        self.assertNotEqual(FROZEN_EVEN_SOURCE_CENTRE[1],19.5859375)

    def test_exclusive_model_parts_overlap_and_missing_source_are_distinct(self):
        source=bytearray(4096)
        parts={p:bytearray(4096) for p in PARTS}
        # A true-positive saddle-exclusive source pixel.
        parts["saddle"][3*64+10]=1
        source[3*64+10]=1
        # Two 2026 parts project to the same source-positive pixel:
        # it must never be credited as an exclusive saddle/fork match.
        parts["saddle"][4*64+11]=1
        parts["fork_and_frame"][4*64+11]=1
        source[4*64+11]=1
        # False-positive rim-only pixel.
        parts["rim_and_hub"][5*64+13]=1
        # Missing upper source pixel unaccounted for by any candidate part.
        source[7*64+9]=1
        # Lower region positive to prove bands partition rather than crop.
        parts["tire"][33*64+31]=1
        source[33*64+31]=1
        aligned={name:bytes(m) for name,m in parts.items()}
        whole=union_planes(aligned)
        self.assertEqual(sum(whole),4)
        result=attribute_bands(bytes(source),aligned)
        upper=result["upper_y0_14"]
        self.assertEqual(upper["source_opaque_pixels"],3)
        self.assertEqual(upper["model_union_pixels"],3)
        self.assertEqual(upper["model_union_alpha_tp_fp_fn"],{"tp":2,"fp":1,"fn":1})
        self.assertAlmostEqual(upper["model_union_iou"],0.5)
        self.assertEqual(upper["model_ambiguous_overlapping_parent_pixels"],1)
        self.assertEqual(upper["source_opaque_pixels_missing_all_2026_parts"],1)
        self.assertEqual(upper["per_2026_parent"]["saddle"]["exclusive_union_pixels"],1)
        self.assertEqual(upper["per_2026_parent"]["saddle"]["exclusive_true_positive_source_pixels"],1)
        self.assertEqual(upper["per_2026_parent"]["saddle"]["possible_true_positive_with_overlaps"],2)
        self.assertEqual(upper["per_2026_parent"]["fork_and_frame"]["exclusive_union_pixels"],0)
        self.assertEqual(upper["per_2026_parent"]["rim_and_hub"]["exclusive_false_positive_source_pixels"],1)
        self.assertEqual(result["lower_y27_63"]["model_union_alpha_tp_fp_fn"],
                         {"tp":1,"fp":0,"fn":0})
        for key in ("tp","fp","fn"):
            self.assertEqual(sum(result[b]["model_union_alpha_tp_fp_fn"][key]
                                 for b in result),
                             {"tp":3,"fp":1,"fn":1}[key])

    def test_bad_model_masks_and_source_labels_fail_closed(self):
        empty={name:bytes(4096) for name in PARTS}
        with self.assertRaisesRegex(ValueError,"five aligned"):
            union_planes({**empty,"unknown":bytes(4096)})
        with self.assertRaisesRegex(ValueError,"five aligned"):
            union_planes({**empty,"saddle":b"bad"})
        with self.assertRaisesRegex(ValueError,"genuine binary"):
            attribute_bands(bytes([2])+bytes(4095),empty)

    def test_cli_writes_one_immutable_source_report_after_scorer(self):
        record={"schema":SCHEMA,"aggregates":{"test":"verified"}}
        with tempfile.TemporaryDirectory() as dirname:
            root=Path(dirname)
            inputs=[]
            for i in range(4):
                file=root/f"source-{i}.bin"
                file.write_bytes(b"dummy")
                inputs.append(str(file))
            out=root/"report.json"
            argv=["prog","--source-zip",inputs[0],
                  "--pose-report",inputs[1],"--axis-report",inputs[2],
                  "--camera",inputs[3],
                  "--verified-exports",str(root),"--out",str(out)]
            with patch("sys.argv",argv),patch(
                    "tools.art.attribute_original_mesen_upper_to_real_glb_parts.analyze",
                    return_value=record),patch("sys.stdout",new_callable=io.StringIO) as stream:
                main()
                self.assertIn("OK ART4K_REAL_2026_DYNAMIC_PARENT_SOURCE_UPPER",
                              stream.getvalue())
            self.assertEqual(json.loads(out.read_text()),record)
            with patch("sys.argv",argv),patch(
                    "tools.art.attribute_original_mesen_upper_to_real_glb_parts.analyze",
                    return_value=record),patch("sys.stdout",new_callable=io.StringIO):
                with self.assertRaises(FileExistsError):
                    main()


if __name__=="__main__":
    unittest.main()
