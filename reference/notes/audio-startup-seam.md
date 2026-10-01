# Audio startup compatibility seam

Recovered-work execution note, 2026-09-29.

## Historical motivation

The preserved emulator-compatibility matrix records minor sound errors in multiple historical emulators and no sound in Super Sleuth 1.03. That symptom is intentionally treated as a separate fidelity seam from the now-resolved unused-song archaeology.

The local question is narrower:

> Does the original retail game establish audible output during the normal frontend route and transition into a materially different first-race audio state at the same deterministic gameplay boundary?

This does not assume a historical emulator diagnosis. A failure could arise from SPC700 bootstrap/upload, DSP state, timing, CPU/APU handshake, or an emulator audio-output defect.

## Existing observability

The pinned `snesref` frontend already writes all core PCM from guest frame 0 through `SNESREF_WAV`. The deterministic `reach-first-race.script` also prints exact guest frames for named checkpoints.

`tools/analyze_reference_audio_windows.py` therefore reduces coarse stereo PCM windows around:

- `main-menu-ready`;
- `now-playing-ready`;
- `race-entered`.

For each window it records RMS, peak amplitude, non-zero sample fraction and an exact window SHA-256. Exact hashes are evidence, not a cross-core equality requirement.

## First discriminator

Run the identical state-driven route through:

1. pinned patched Snes9x;
2. repository-owned Beetle/bsnes-derived reference core.

Require each engine to:

- reach the named first-race checkpoint;
- produce non-empty PCM at all three named windows;
- produce a race window distinguishable from the frontend window.

If both independent cores satisfy those coarse invariants, promote them as the minimum audio-startup regression. Any future native/recompiled audio path can then be compared against the same state boundaries without depending on emulator-specific PCM identity.

Further SPC/DSP/APU-memory tracing is justified only if a later mismatch needs reduction.

## First cross-core result

Run `36659692449` passed on both reference cores.

| checkpoint | Snes9x RMS / peak | Beetle RMS / peak |
| --- | --- | --- |
| Main Menu | 2409.89 / 11644 | 2193.50 / 11154 |
| Now Playing | 4007.58 / 18543 | 3753.57 / 18525 |
| Race entered | 6919.59 / 30691 | 6381.53 / 28832 |

Both cores are effectively continuously non-zero in all three 60-guest-frame windows (99.1%-99.99% non-zero samples). Both also produce distinct exact window hashes across frontend and race.

The independent route timing stays close but is not forced equal: Snes9x reaches `now-playing-ready` / `race-entered` at frames 821 / 1035, Beetle at 824 / 1038. The reducer keys audio windows to each engine's own named checkpoint frame, so the regression tests state-aligned audio rather than assuming identical emulator timing or sample rate.

This closes the minimum historical audio-startup seam: a conforming implementation must establish audible frontend output and transition into a materially different audible first-race state. Exact PCM remains a stronger per-engine reference artifact, not a cross-engine equality contract.

Durable measurements: `analysis/generated/audio-startup-reference-summary.json`.
