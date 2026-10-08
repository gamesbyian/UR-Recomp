# Player-visible Restart audio timeline reconciliation

The ordinary Windows audio gates prove working title/race playback, stock
Start pause/resume, Modern frozen pause/Resume, and real Exit-to-Frontend.
The remaining Modern pause **Restart Race** output has produced both
passing and failing packaged-Windows captures.

## Evidence from independent real Windows processes

- Failed audio probe [37765901676](https://github.com/gamesbyian/UR-Recomp/actions/runs/37765901676) and repeated [37766242163](https://github.com/gamesbyian/UR-Recomp/actions/runs/37766242163): authoritative host selected Restart, returned paused=0, original guest progressed through a later race checkpoint, but actual final stereo device samples were literal zeros.
- The second failure's bounded 8s envelope had ~0.8s of stereo output and then **57 consecutive 100ms silent buckets**. The production APU counters recorded over 775,000 generated frames, near-matching consumption, no dropped audible samples and zero post-startup missing output-rate frames or callback underflow episodes. This is not evidence of an SDL device starvation.
- A subsequent [37766680588](https://github.com/gamesbyian/UR-Recomp/actions/runs/37766680588) **passed** actual packaged Windows Restart: both channels were audible after restart and the device final one-second window was RMS ~6174, with 65/80 final 100ms buckets audible. Its independent *uninterrupted race* control had all 80/80 final buckets audible and final RMS ~6016. These are nondeterministic real-output outcomes, not a license to remove the failing audio gate.

The two failing captures used main Windows package 37760448303; the
passing capture reused main package 37765790483. The intervening changes
were non-audio graphics/physics-evidence work. The remaining run-to-run
variation needs repeated identical-package comparisons before ruling
out unrelated runtime scheduling.

## Ownership mismatch in pinned framework

The pinned SNESRecomp `RtlRollbackLoadFromMemory` is engineered for
**invisible** netplay/runahead rollback: it preserves the live DSP output
ring and deliberately suppresses the generation-change signal. In a
player-visible Modern Restart, the snapshot also restores the guest
APU/SPC/DSP state, but output from the abandoned attempt must be retired
and the SDL stream must not present the old timeline. Existing Modern
`reconcile_presentation()` simply toggled fast-forward and its
sample-retention cushion; this does not tell SDL to clear its queued
presentation.

## Bounded candidate fix

`tools/patches/snesrecomp-visible-restart-audio.patch` adds a new
`RtlAudioInvalidateVisibleTimeline()` function called **only** after a
successful player-visible Restart restore through
`native/product/uniracers_modern_host.cpp`'s existing reconciliation
callback. Under the normal APU mutex it discards only queued **host
output** samples, resets the resampling/priming/recovery state and
increments `RtlStateGeneration()`, which prompts the framework's desktop
main loop to clear buffered SDL audio via `ResetAudioTimeline()`.
It does not touch guest SPC instructions, DSP synthesis register state,
scheduling timestamps, music/SFX assets or guest cadence. The ordinary
rollback loader is unchanged; netplay, speculative runahead and replay
rollback never call this hook.

This is a **candidate targeted audio fix**, not proven shipping closure.
It must pass pinned patch application, existing native compilation and
restart-state parity tests. To promote it as a real Windows fix, build a
new *verified* Windows portable package containing the patch, run the
full mandatory audio matrix and **repeat the real Restart captured
output** several times on that exact executable; preserve nonzero
stereo recovery, guest/WRAM restore invariants, post-startup ring
continuity, and existing confirmed Resume and Exit-to-Frontend output.
Never infer success from tests that reuse an older main portable ZIP.
