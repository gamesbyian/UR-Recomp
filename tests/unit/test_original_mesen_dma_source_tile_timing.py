"""Source-bounded synthetic checks and real historical queue/PPU identity."""
import hashlib
import json
from pathlib import Path
import unittest
from tools.art.audit_original_mesen_dma_source_tile_timing import (
    ROM_SIZE, ROM_SHA, ZIP_SHA, original_lorom_source_bytes, ppu_vram_tile,
    SAMPLED_TICKS, TILE_SIZE, audit,
)

ROOT=Path(__file__).resolve().parents[2]

class SourceTileTimingTests(unittest.TestCase):
    def test_snes_lorom_source_32_bytes_and_address_bounding(self):
        fake=bytearray(ROM_SIZE)
        at=0x27*0x8000+(0xD440&0x7FFF)
        fake[at:at+32]=bytes(range(32))
        self.assertEqual(original_lorom_source_bytes(bytes(fake),0x27,0xD440),
                         bytes(range(32)))
        for bank,addr in ((0x27,0x1000),(0x40,0xD440),(0x27,0xFFF0),
                          (-1,0xD440),(True,0xD440)):
            with self.assertRaises(ValueError):
                original_lorom_source_bytes(bytes(fake),bank,addr)

    def test_source_ppu_word_address_tiles_have_32_exact_bytes(self):
        vram=bytes([x&255 for x in range(65536)])
        self.assertEqual(ppu_vram_tile(vram,0x6020),
                         vram[2*0x6020:2*0x6020+TILE_SIZE])
        for size,word in ((65535,0x6020),(65536,0x8000),(65536,0x7FFF),(65536,-1)):
            with self.assertRaises(ValueError):
                ppu_vram_tile(bytes(size),word)

    def test_actual_original_input_identity_and_all_233_source_entries(self):
        rom=(ROOT/"reference/roms/retail/Uniracers_USA.sfc").read_bytes()
        source=(ROOT/"analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip").read_bytes()
        queue=json.loads((ROOT/"analysis/data/racer-original-mesen-rider-queue-vram-tile-mapping-eight-20261103.json").read_bytes())
        self.assertEqual(hashlib.sha256(rom).hexdigest(),ROM_SHA)
        self.assertEqual(hashlib.sha256(source).hexdigest(),ZIP_SHA)
        result=audit(rom,source,queue)
        self.assertEqual(result["original_selected_ticks"],list(SAMPLED_TICKS))
        self.assertEqual(sum(x["source_queue_size"] for x in result["rows"]),233)
        self.assertTrue(result["source_held_PPU_phase_and_enqueued_NMI_transfer_not_aligned"])
        self.assertFalse(result["source_original_1994_3D_mesh_camera_pose_recovered"])
        for row in result["rows"]:
            self.assertEqual(len(row["tile_candidates"]),row["source_queue_size"])
            for delta,count in row["temporal_alignment_counts"].items():
                self.assertLessEqual(count["exact_32_byte_tile_matches"],count["compared_tiles"])
                self.assertLessEqual(count["equal_bytes_of_compared"],count["total_compared_bytes"])
                self.assertIn(int(delta),(-1,0,1))

    def test_wrong_real_source_archive_or_queue_identity_rejected(self):
        rom=bytes(ROM_SIZE)
        with self.assertRaisesRegex(ValueError,"ROM SHA"):
            audit(rom,b"",{})

if __name__=="__main__":
    unittest.main()
