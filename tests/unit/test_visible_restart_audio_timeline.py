import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class VisibleRestartAudioTimelineTests(unittest.TestCase):
    def test_pinned_offline_framework_patch_is_sound_and_last_in_audio_stack(self):
        patch = ROOT / "tools/patches/snesrecomp-visible-restart-audio.patch"
        payload = patch.read_bytes()
        toolchain = json.loads((ROOT / "tools/toolchain-entries/snesrecomp.json").read_text())
        specs = toolchain["patches"]
        matches = [i for i, spec in enumerate(specs)
                   if spec["path"] == "tools/patches/snesrecomp-visible-restart-audio.patch"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(specs[matches[0]]["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertGreater(matches[0], next(
            i for i, spec in enumerate(specs)
            if spec["path"] == "tools/patches/snesrecomp-rewind-audio-timing-lock.patch"
        ))
        source = payload.decode("utf-8")
        self.assertIn("void RtlAudioInvalidateVisibleTimeline(void)", source)
        self.assertIn("dsp_trimSamples(g_snes->apu->dsp, 0u)", source)
        self.assertIn("rtl_reset_audio_delivery();", source)
        self.assertIn("++s_state_generation;", source)
        self.assertIn("RtlApuUnlock();", source)
        self.assertNotIn("apu_runToGuestCycle", source)

    def test_live_restart_hook_is_audio_only_not_a_replacement_for_rollback(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text()
        source = host[
            host.index("void reconcile_presentation() {"):
            host.index("bool exit_to_frontend();")
        ]
        self.assertIn("RtlAudioInvalidateVisibleTimeline();", source)
        self.assertNotIn("RtlAudioSetFastForward(", source)
        restore = host[
            host.index("bool load_snapshot("):
            host.index("void set_timing_lock(")
        ]
        self.assertIn("&RtlRollbackLoadFromMemory", restore)
        self.assertNotIn("RtlAudioInvalidateVisibleTimeline", restore)
        self.assertIn("&reconcile_presentation", host)

    def test_visible_timeline_reset_does_not_rewrite_invisible_rollback_body(self):
        patch = (ROOT / "tools/patches/snesrecomp-visible-restart-audio.patch").read_text()
        lines = patch.splitlines()
        # Restrict all additions to a new wrapper AFTER the rollback return
        # and an API declaration. No netplay or runahead hooks are changed.
        self.assertIn("   return ok;", lines)
        self.assertIn(" void RtlAudioProducerCursor(void) {", patch.replace(
            "uint32_t RtlAudioProducerCursor(void) {",
            "void RtlAudioProducerCursor(void) {"))
        self.assertEqual(patch.count("--- a/runner/src/"), 2)


if __name__ == "__main__":
    unittest.main()
