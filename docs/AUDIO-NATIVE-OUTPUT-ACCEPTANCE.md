# Native Windows audio-output acceptance

Status: SDL3 disk-backend PCM capture and fail-closed metrics tooling available;
**native music/SFX fidelity is not yet closed**. This is a playback-device
evidence lane, not a replacement for ROM-derived SPC/DSP reference rendering.

## Source and ownership

The pinned SNESRecomp desktop host renders the original SNES audio via
RtlRenderAudio and pushes it into an SDL3 audio stream. The stock APU/DSP
and game-authored sound triggers remain authoritative. The framework's desktop
host selects signed-16 stereo source audio; SDL's device stream may resample to
the output device. A device-opening success or dummy callback proves no audible
content. The previously accepted Snes9x/Beetle reference evidence instead
establishes non-silent, distinct frontend/first-race PCM windows:
references/notes/audio-startup-seam.md.

For a **real native device-output signal**, SDL3 3.4.10 contains a built-in
disk audio backend. It writes the final playback stream as headerless PCM.
Use it in acceptance only. It neither reinterprets guest timing nor injects
an artificial APU output into the consumer build.

## Capture procedure

On a Windows x64 package or native executable, launch an existing deterministic
script through the *normal* executable with these environment variables set
before SDL initialization:

- SDL_AUDIO_DRIVER=disk
- SDL_AUDIO_DISK_OUTPUT_FILE=<absolute Windows path to a temporary .raw>
- SDL_AUDIO_FORMAT=S16LE
- SDL_AUDIO_CHANNELS=2
- SDL_AUDIO_FREQUENCY=44100
- SDL_AUDIO_DISK_TIMESCALE=1.0

The backend prints its negotiated device format as a diagnostic line, for
example: Writing to file [...], format=S16LE channels=2 freq=44100.
Do not infer raw-PCM sample format or sample rate from file size or assume
the SPC engine's native 32040 Hz source rate equals the SDL device rate.
On Windows, capture stderr/stdout into a text log and run:

    python tools/analyze_sdl_disk_audio.py native.log audio.raw --json-out metrics.json

The analyzer requires exactly one SDL playback-format announcement, signed-16
little-endian stereo at an explicitly reported sane device rate, complete PCM
frames, at least one second of output by default, and a conservative non-silent
RMS/nonzero floor. It reports output length, full-file SHA-256, aggregate and
per-channel amplitude, peak/clipping rates and negotiated device format. It
does not emit or commit proprietary PCM. A missing, empty, malformed, silently
open, wrong-destination or unsupported-format capture fails closed.

## Acceptance claims and next gate

This is a **host-output continuity prerequisite**, not proof of exact SNES
composition, note timing, DSP echo or uninterrupted real-speaker playback.
SDL disk time/guest-frame alignment is not presently established and must not
be guessed from source sample counts or a wall-clock delay. Actual Windows
acceptance should use named deterministic frontend and race routes, preserve
the existing Snes9x/Beetle reference windows and add explicit audio phase
markers where the host can observe them. Introduce timestamp-to-guest-frame
correlation only when measured, then test menu/race changes, pause/resume,
Restart Race, Exit to Frontend, device reinit and queue underruns. Do not
compare cross-emulator PCM hashes as equality requirements.

Stock SPC/APU audio remains the shipping fallback. Any later restored audio
must follow docs/ASSET-RESTORATION-PIPELINE.md, with BRR/sample provenance,
original sequence/timing, and Authentic mode preserved.

## Automatic main-branch acceptance

The `.github/workflows/windows-native-audio-output.yml` workflow listens for a
**successful** `Windows native build and boot smoke` workflow run on the same
repository's `main` branch. It downloads that run's verified portable package
and measures SDL disk playback plus Release audio queue counters, without
recompiling. It rejects non-main and unsuccessful `workflow_run` events and
retains the explicit manual `workflow_dispatch` input for reproducing a
specific source build. The automatic trigger does not run on every PR or every
ordinary push: it follows only a completed Windows-package gate.

This gives Windows audio a continuous **packaged-output integrity** check.
Even an accepted run is not yet exact music/SFX reference parity, device
latency certification or pause/restart transient fidelity. Those remain
separate evidence requirements and cannot be inferred from aggregate PCM RMS.

## First-race audible-tail discriminator

The stock `tests/input/reach-first-race.script` ends after 60 guest frames
have elapsed in active racing. A whole-file non-silence measurement alone
could be satisfied by menu music even if native music vanished before race
entry. Accordingly, the Windows package capture also requires its final
0.5 seconds of **SDL device-output PCM** to exceed an intentionally low RMS
and nonzero-sample floor (`--tail-seconds 0.5 --min-tail-rms 50`). The
corresponding result records the tail window size, RMS, peak, and nonzero
fraction separately from full-file statistics. This proves sound reaches the
SDL device towards the end of the scripted first-race route. It does not
prove exactly which guest samples correspond to those output frames, that
the effect/music arrangement matches the reference, or that hardware speaker
latency is acceptable. More precise claims still require actual aligned
reference PCM evidence.

## Three named native audio checkpoints

The cross-core Snes9x/Beetle startup reference is kept in
`reference/notes/audio-startup-seam.md` and
`analysis/generated/audio-startup-reference-summary.json`. Its essential
semantic observations are audible main-menu, Now Playing and first-race
windows, each keyed to that emulator's own guest-frame checkpoint. Native
Windows acceptance now uses `tools/build_audio_checkpoint_route.py` to stop
the **same canonical first-race input script** at each of those three named
`dump` commands. Each phase runs in an independent fresh process with its own
SDL3 disk output, production audio counters and disposable user-data root.
A missing checkpoint, silent final half-second, malformed disk format or
invalid audio stats fails closed for that phase.

The workflow reports three tail RMS/peak/nonzero measurements and per-phase
queue counters. Their relative behavior can be inspected against the two
independent emulators, but hashes of different-length, different-timing PCM
files cannot demonstrate a sound-track transition. Soundfont provenance,
exact notes, SFX triggers, DSP envelope/echo, and frame-accurate playback
still require a stronger state-aligned native/reference oracle.

## Checkpoint-centered audio windows

The historical independent Snes9x/Beetle evidence uses a roughly one-second
PCM window centered on each named semantic checkpoint (±30 guest frames).
The initial native Windows three-route implementation instead stopped each
process *at* the dump and used the preceding 0.5 seconds of device output;
that would put the native and reference phase windows on different sides of
the checkpoint.

`tools/build_audio_checkpoint_route.py` now retains an ordinary
`wait 30` after each named checkpoint and a second observed dump named
`<checkpoint>-audio-post`. The Windows acceptance checks **both**
WRAM dumps and `tools/check_native_audio_checkpoint_timing.py` independently
reads the production process log to confirm exactly 30 simulated frames
separate the two markers. The final **1 second of SDL3 device PCM** is then
measured, approximately bracketing 30 guest frames before and after the
checkpoint at 60 Hz. The core run is not re-clocked.

This is substantially more comparable to the independent reference *window
placement*, but the SDL resampler, queue delay, startup priming and end-of-run
draining have not been mapped exactly to guest-frame boundaries. Do not
reinterpret this as proven sample-exact phase alignment, DSP equivalence or
device latency validation. Those still require causal phase/queue calibration.

## Relative native/reference phase matrix

The first three-checkpoint Windows capture also produces
`audio-phase-matrix.json` from `tools/analyze_audio_phase_matrix.py`.
For each of the same named checkpoints, it reports:

- Native SDL3 output one-second-tail RMS and peak amplitude.
- Existing independent Snes9x and Beetle guest-centered-window RMS.
- Ratios of Now Playing and Race Entry RMS to Main Menu RMS **within each
  engine**, and each engine's observed RMS phase ordering.
- Whether the independent references agree on that ordering and whether
  native output shares it.

This comparison is deliberately descriptive at first. It rejects missing or
synthetic native metadata, nonfinite or nonpositive amplitudes, invalid native
window durations, ambiguous reference identities and missing reference
checkpoints. It does **not** demand equal raw PCM hashes, absolute amplitudes
or ratios across different emulators. A native phase-order mismatch is recorded
for investigation rather than automatically "corrected" by changing APU or
playback timing. The matrix remains useful even before actual sample-to-guest
phase and SDL latency are measured.

The source of truth for this reference comparison remains
`analysis/generated/audio-startup-reference-summary.json`,
created from independent captures; no new music assets are inferred.

## Audio-only change validation without native recompilation

The specialist audio workflow also triggers for **main-branch changes to
the audio reducers, checkpoint route and canonical input fixture**. This does *not* run the expensive native Windows build again.
Instead, GitHub Actions selects the latest successful first-party
`Windows native build and boot smoke` run on main and downloads its
named, already verified portable package. A missing successful package or
missing artifact fails closed. It then launches the normal packaged executable
under SDL3 disk playback and captures the three audio checkpoints, production
stats, window alignment evidence and the normalized reference phase matrix.

The separate `workflow_run` trigger continues to test any newly successful
Windows product build automatically. Thus changes to *audio analysis tools and input fixtures*
can be validated immediately against an existing package, while *game code
changes* are validated against their newly built package. Neither requires
building a second native executable in the audio lane. Workflow-YAML-only
changes do not self-trigger, per repository CI policy; the successful-build
follow-on and manual source-run dispatch remain available.

## Isolated audio acceptance concurrency

The first self-contained audio-tool push run
([37719929546](https://github.com/gamesbyian/UR-Recomp/actions/runs/37719929546))
was canceled by a separate **skipped** `workflow_run` generated when
an unrelated Windows source build ended without success. The top-level
concurrency key had treated these unrelated events as equivalent.

The workflow now distinguishes event type **and source build outcome** in its
concurrency group. A skipped failed/cancelled source-run event can no longer
cancel a live main-push audio acceptance. Successful source-build captures
still coalesce with each other, as do repeated audio-tool push captures, so
outdated redundant jobs do not accumulate.

The native/reference phase matrix also retains both left/right device-output
tail RMS values for every named checkpoint. This fails closed if either channel
is wholly silent or the native analyzer failed to supply independent stereo
evidence, while avoiding an unsupported channel-loudness equivalence to the
independent emulators.
