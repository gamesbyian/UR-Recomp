"""QA-08: adversarial first-line HDMA consumption model and experimental gate."""
import copy
import json
from pathlib import Path
import unittest

from tools import qa08_model_hdma_prime as model
from tools import qa08_patch_hdma_prime_counterfactual as patch
from tools import qa08_check_hdma_prime_candidate as pixel

ROOT = Path(__file__).resolve().parents[2]


def accepted():
    return json.loads((ROOT / "analysis/data/"
                       "qa08-original-native-2p-brightness-split-channel7-handoff-20261014.json").read_text())


def fixture_source():
    return """#include "ppu.h"
static void dma_hdmaLoadDescriptor(Dma* dma, DmaChannel* ch) {}
void dma_initHdma(Dma* dma) {}
void dma_primeHdmaFirstLine(Dma* dma) {
  for (int i = 0; i < 8; i++) {
    DmaChannel* ch = &dma->channel[i];
    if (!ch->hdmaActive || ch->terminated || !ch->doTransfer) continue;
    DmaChannel save = *ch;
    int len = transferLength[ch->mode & 7];
    hdma_pin_oam_address(dma, ch);
    for (int j = 0; j < len; j++) {
      uint8_t bAdr = (uint8_t)(ch->bAdr + bAdrOffsets[ch->mode & 7][j]);
      g_ppu_wlog_src = kPpuWlogHdma;
      if (ch->indirect)
        dma_transferByte(dma, ch->size++, ch->indBank, bAdr, false, i);
      else
        dma_transferByte(dma, ch->tableAdr++, ch->aBank, bAdr, false, i);
      g_ppu_wlog_src = kPpuWlogCpu;
    }
    *ch = save;
  }
}
void dma_doHdma(Dma* dma) {}
"""


def pixels(*, black_rows, native):
    out = bytearray()
    for y in range(224):
        for _ in range(256):
            c = 0 if y in black_rows else 255
            out += (bytes((c, c, c, 255)) if native
                    else bytes((c, c, c, 0)))
    return bytes(out)


class HdmaPrimeModelTests(unittest.TestCase):
    def test_accepted_unmodified_native_and_counterfactual_rows(self):
        result = model.check(accepted())
        old = result["actual_unmodified_native_model"]
        new = result["consume_prime_once_counterfactual_model"]
        self.assertEqual(old["zero_brightness_output_rows"], [112, 113])
        self.assertEqual(new["zero_brightness_output_rows"], [111, 112])
        self.assertEqual([e["native_tag"] for e in old["log_events"]],
                         [0, 2, 113, 115])
        self.assertEqual([e["native_tag"] for e in new["log_events"]],
                         [0, 112, 114])
        self.assertFalse(result["descriptor_header_bytes_independently_read"])
        self.assertFalse(result["corrected_native_exact_binary_or_raster_executed"])

    def test_counterfactual_requires_consume_not_just_relabel(self):
        a = model.replay((111, 2, 111), (15, 0, 15), prime_consumes=False)
        b = model.replay((111, 2, 111), (15, 0, 15), prime_consumes=True)
        self.assertNotEqual(a["log_events"], b["log_events"])
        self.assertEqual(len(b["zero_brightness_output_rows"]), 2)

    def test_evidence_mutations_rejected(self):
        for mutate in [
            lambda x: x["original"]["write_values"][1].update(v=112),
            lambda x: x["native"]["write_values"][1].update(native_tag=3),
            lambda x: x["native"].update(writer_HDMA_channel=5),
            lambda x: x["original"]["write_values"][1].update(PPU_forced_blank_bit=True),
            lambda x: x["finished_source_frame_reference"].update(
                original_zero_brightness_black_rows=[112, 113]),
            lambda x: x["original"].update(archive_SHA256="0" * 64),
        ]:
            with self.subTest(mutate=mutate):
                evidence = copy.deepcopy(accepted())
                mutate(evidence)
                with self.assertRaisesRegex(ValueError, "changed"):
                    model.check(evidence)

    def test_bad_nonrepeat_descriptors_rejected(self):
        for counts, values in [((0,), (15,)), ((128,), (15,)),
                               ((2, 3), (15,)), ((2,), (256,))]:
            with self.subTest(counts=counts):
                with self.assertRaises(ValueError):
                    model.replay(counts, values, prime_consumes=True)

    def test_source_patch_is_opt_in_and_fail_closed(self):
        source = fixture_source()
        changed = patch.patch_source(source)
        self.assertIn(patch.MARK, changed)
        self.assertNotIn("DmaChannel save = *ch;", changed)
        self.assertIn("ch->repCount--;", changed)
        self.assertIn("dma_hdmaLoadDescriptor(dma, ch);", changed)
        self.assertIn("void dma_doHdma(Dma* dma) {}", changed)
        with self.assertRaises(ValueError):
            patch.patch_source(changed)
        with self.assertRaises(ValueError):
            patch.patch_source(source.replace("    *ch = save;", "    return;"))
        with self.assertRaises(ValueError):
            patch.patch_source(source.replace("    DmaChannel save = *ch;", ""))

    def test_pixel_comparator_rejects_only_seam_displacement(self):
        original = pixels(black_rows=(111, 112), native=False)
        exact = pixels(black_rows=(111, 112), native=True)
        old = pixels(black_rows=(112, 113), native=True)
        crc = b"".join(f"{i}:abcdef12\n".encode() for i in range(2473))
        report = pixel.compare(original, pixel.P7_HEADER + exact, crc, crc)
        self.assertEqual(report["actual_source_pixels_equal"], 57344)
        self.assertFalse(report["production_HDMA_change_authorized"])
        with self.assertRaisesRegex(ValueError, "512 exact RGB"):
            pixel.compare(original, pixel.P7_HEADER + old, crc, crc)
        with self.assertRaisesRegex(ValueError, "CRC"):
            pixel.compare(original, pixel.P7_HEADER + exact, crc, crc[:-1])
        with self.assertRaisesRegex(ValueError, "source-size"):
            pixel.compare(original, b"not P7", crc, crc)
        with self.assertRaisesRegex(ValueError, "byte count"):
            pixel.compare(original, pixel.P7_HEADER + exact[:-4], crc, crc)


if __name__ == "__main__":
    unittest.main()
