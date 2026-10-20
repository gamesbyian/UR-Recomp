"""ROM-free negative checks: selected CGRAM correlation is not pixel parity."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa08_independent_palette_rotation_audit as audit


def synthetic_rows():
    rows = []
    for frame, palette in audit.PALETTES.items():
        selected = palette[0]
        phase = 0 if frame == 5176 else 1 if frame < 5184 else 2
        rgb = [(1,2,3), (4,5,6), (7,8,9)][phase]
        for x, y in sorted(audit.POINTS):
            for sub in ("0", "1"):
                rows.append(" ".join([
                    "UR_QA08_LATE_PPU_SOURCE", f"frame={frame}", f"x={x}",
                    f"logical_y={y}", f"ppu_line={y+1}", f"sub={sub}",
                    "layer=0", "directcolor=0", "index=6c",
                    f"selected_rgb555={selected}", f"cgram_index_word={selected}",
                    *[f"cgram{n:02x}={word}" for n,word in zip(range(0x6c,0x70),palette)],
                ]))
            rows.append(" ".join([
                "UR_QA08_LATE_PPU_FINAL", f"frame={frame}", f"x={x}",
                f"logical_y={y}", f"ppu_line={y+1}",
                "RGB8=" + ",".join(map(str,rgb)),
            ]))
    return rows


class PaletteCorrelationBoundaries(unittest.TestCase):
    def test_sample_correlates_without_proving_correct_final_color(self):
        result = audit.parse_rows(synthetic_rows())
        self.assertEqual(result["palette_rotation_boundaries"], [5177,5184])
        self.assertEqual(result["main_sub_final_triplets"], 88)
        self.assertEqual(result["source_rows"], 264)
        self.assertTrue(result["source_pixel_correlation_only"])
        self.assertFalse(result["same_epoch_original_native_proven"])
        self.assertFalse(result["whole_frame_P7_noninterference_proven"])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_slot_corruption_is_rejected(self):
        rows = synthetic_rows()
        rows[0] = rows[0].replace("cgram6c=4210", "cgram6c=1111")
        with self.assertRaisesRegex(ValueError, "indexed CGRAM identity"):
            audit.parse_rows(rows)

    def test_unpaired_final_change_is_rejected(self):
        rows = synthetic_rows()
        for i,line in enumerate(rows):
            if line.startswith("UR_QA08_LATE_PPU_FINAL frame=5178 "):
                rows[i] = line.replace("RGB8=4,5,6", "RGB8=8,5,6")
                break
        with self.assertRaisesRegex(ValueError, "unexpected stage-transition"):
            audit.parse_rows(rows)

    def test_duplicate_stage_is_rejected(self):
        rows = synthetic_rows()
        rows[-1] = rows[0]
        with self.assertRaisesRegex(ValueError, "duplicate stage"):
            audit.parse_rows(rows)

    def test_missing_stage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete sample"):
            audit.parse_rows(synthetic_rows()[:-1])

    def test_unpinned_archive_rejected_before_reading_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "forged.zip"
            with zipfile.ZipFile(path,"w") as z:
                z.writestr("on-source.log", "\n".join(synthetic_rows()))
            with self.assertRaisesRegex(ValueError, "immutable hosted archive SHA"):
                audit.audit(path)


if __name__ == "__main__":
    unittest.main()
