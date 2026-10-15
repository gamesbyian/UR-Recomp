"""Fail-closed proof for the title-only Uniracers first-line PPU candidate."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_uniracers_hdma_firstline_patch as candidate  # noqa: E402
import qa08_patch_hdma_prime_counterfactual as trial  # noqa: E402


# The relevant literal pinned dma.c block, not a fabricated replacement
# function: retain both A-bus source paths and the OAM pin hook.
PINNED = """static void dma_hdmaLoadDescriptor(Dma* dma, DmaChannel* ch) {
}
void dma_initHdma(Dma* dma) {
}
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

void dma_doHdma(Dma* dma) {
}
"""


class CandidateSourceTest(unittest.TestCase):
    def test_identical_executed_global_experiment_semantics(self):
        changed = candidate.patch_source(PINNED)
        experimental = trial.patch_source(PINNED)
        self.assertEqual(
            changed.replace(candidate.REPLACEMENT, trial.NEW_ADVANCE, 1),
            experimental,
        )
        self.assertEqual(candidate.patch_source(changed), changed)
        self.assertEqual(changed.count(candidate.MARK), 1)
        self.assertNotIn("DmaChannel save = *ch", changed)
        self.assertIn("ch->repCount--;", changed)
        self.assertEqual(changed.count("void dma_doHdma(Dma* dma) {"), 1)

    def test_rejects_changed_source_or_incomplete_patch(self):
        changed = candidate.patch_source(PINNED)
        cases = [
            "",
            PINNED.replace("hdma_pin_oam_address(dma, ch);", ""),
            PINNED.replace("dma_transferByte(dma, ch->size++", "dma_transferByte(dma, ch->size"),
            PINNED + PINNED,
            changed.replace("ch->repCount--;", "ch->repCount -= 2;"),
            changed.replace("ch->doTransfer = (ch->repCount & 0x80) != 0;",
                            "ch->doTransfer = false;"),
            changed.replace(candidate.MARK, "UNREVIEWED_PPU_CHANGE"),
            changed + candidate.MARK,
            trial.patch_source(PINNED),
        ]
        for code in cases:
            with self.subTest(case=code[:64]):
                with self.assertRaises(ValueError):
                    candidate.patch_source(code)

    def test_refuses_other_title_even_when_code_is_same(self):
        with tempfile.TemporaryDirectory() as temp:
            game = Path(temp)
            (game / "src/gen").mkdir(parents=True)
            (game / "src/gen/dispatch_v2.c").write_text("generated", encoding="utf-8")
            (game / candidate.RELATIVE).parent.mkdir(parents=True)
            (game / candidate.RELATIVE).write_text(PINNED, encoding="utf-8")
            with mock.patch.object(candidate, "pinned_revision",
                                   side_effect=["unrecognized", candidate.CORE_REV]):
                with self.assertRaisesRegex(ValueError, "Uniracers game"):
                    candidate.apply_game_candidate(game, write=True)
            self.assertEqual((game / candidate.RELATIVE).read_text(), PINNED)

    def test_refuses_alternate_framework_and_does_not_write_on_dry_run(self):
        with tempfile.TemporaryDirectory() as temp:
            game = Path(temp)
            (game / "src/gen").mkdir(parents=True)
            (game / "src/gen/dispatch_v2.c").write_text("generated", encoding="utf-8")
            (game / candidate.RELATIVE).parent.mkdir(parents=True)
            file = game / candidate.RELATIVE
            file.write_text(PINNED, encoding="utf-8")
            with mock.patch.object(candidate, "pinned_revision",
                                   side_effect=[candidate.GAME_REV, "other-core"]):
                with self.assertRaisesRegex(ValueError, "framework"):
                    candidate.apply_game_candidate(game, write=True)
            with mock.patch.object(candidate, "pinned_revision",
                                   side_effect=[candidate.GAME_REV, candidate.CORE_REV]):
                candidate.apply_game_candidate(game, write=False)
            self.assertEqual(file.read_text(), PINNED)
            with mock.patch.object(candidate, "pinned_revision",
                                   side_effect=[candidate.GAME_REV, candidate.CORE_REV]):
                candidate.apply_game_candidate(game, write=True)
            self.assertEqual(candidate.patch_source(file.read_text()), file.read_text())

    def test_original_2p_scores_stay_source_bound_and_not_release_approval(self):
        evidence = json.loads((
            ROOT / "analysis/data/qa08-real-original-native-postgo-3frame-rgb5-parity-20261014.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(evidence["native_guest_CRC_entries_all_four"], 2473)
        self.assertTrue(evidence["native_guest_CRC_all_four_identical"])
        self.assertEqual([x["native_guest"] for x in evidence["verified_frame_pairs"]],
                         [2192, 2208, 2224])
        for row in evidence["verified_frame_pairs"]:
            self.assertEqual(row["wrong_normalized_original_RGB5_pixels"]["stock"], 512)
            self.assertEqual(row["wrong_normalized_original_RGB5_pixels"]["global"], 0)
        self.assertEqual(evidence["contrast_countdown_native1856_original1855_wrong"]["stock"], 971)
        self.assertEqual(evidence["contrast_countdown_native1856_original1855_wrong"]["global"], 0)
        self.assertFalse(evidence["production_renderer_correction_authorized"])
        self.assertFalse(evidence["full_moving_event_1P_transitions_results_achieved"])


class CandidateWindowsWiringTest(unittest.TestCase):
    def test_candidate_staged_only_after_game_core_pins_before_compile(self):
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        unit = "python tests/unit/test_baldosa_uniracers_hdma_firstline_patch.py"
        stage = ("python tools/baldosa_uniracers_hdma_firstline_patch.py "
                 "--game baldosa --apply-candidate")
        self.assertEqual(workflow.count(unit), 1)
        self.assertEqual(workflow.count(stage), 1)
        self.assertLess(workflow.index("test \"$(git -C baldosa/snesrecomp rev-parse HEAD)\""),
                        workflow.index(stage))
        self.assertLess(workflow.index("python tools/baldosa_dram_refresh_beam_rate_patch.py"),
                        workflow.index(stage))
        self.assertLess(workflow.index(stage), workflow.index("cmake -S baldosa -B baldosa/build-ur-win"))
        # A game-scoped Windows candidate, never global framework/bootstrap.
        for other in (
            "tools/bootstrap_toolchain.py", "tools/qa08_patch_hdma_prime_counterfactual.py",
        ):
            self.assertNotIn("--apply-candidate", (ROOT / other).read_text())


if __name__ == "__main__":
    unittest.main()
