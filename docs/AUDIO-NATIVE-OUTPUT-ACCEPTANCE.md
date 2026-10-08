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
reference/notes/audio-startup-seam.md.

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

## First fully passing three-phase Windows result, 2026-10-08

Automated audio-only acceptance
[run 37720294029](https://github.com/gamesbyian/UR-Recomp/actions/runs/37720294029)
passed using the already verified Windows portable ZIP from
[run 37718859318](https://github.com/gamesbyian/UR-Recomp/actions/runs/37718859318).
It independently launched the *shipping* executable for each canonical
checkpoint, verified both authoritative WRAM dump files, confirmed the exact
30 post-checkpoint simulated frames in each native log, captured SDL3
S16LE/44.1 kHz stereo output, applied the post-startup queue continuity
limits and compared the normalized one-second audio tails with the two
independent reference-core measurements.

| Native checkpoint | Guest boundary/post frames | Native tail RMS / menu-tail ratio | New underflows after first interval | Audible source drops |
| --- | --- | --- | --- | --- |
| Main Menu | 506 / 536 | reference baseline, 1.000× | 0 | 0 |
| Now Playing | 829 / 859 | 1.763× | 0 | 0 |
| Race Entry | 1044 / 1074 | 2.762× | 0 | 0 |

The Snes9x **Now Playing/Race Entry** to Main Menu RMS ratios in the
independent reference windows were **1.663× / 2.871×**; Beetle/bsnes was
**1.711× / 2.909×**. All three engines independently order their observed
checkpoint RMS levels **Main Menu < Now Playing < Race Entry**. Differences
in PCM window placement, backend processing, gain and resampler output mean
this is a meaningful coarse comparison, **not** a requirement for equal
amplitude, musical notes or waveform hashes.

The 9-, 15- and 18-snapshot native runs each recorded eight underflow
episodes and about 4,041–4,042 missing output-rate frames *only in the first
observed one-second stats interval*, followed by **zero** new underflows or
missing frames. Across all three runs there were zero audible native-ring
sample drops. Stereo channel-tail metadata and source-provenance checks
passed. The first `workflow_run` attempt of this expanded gate
([37719278900](https://github.com/gamesbyian/UR-Recomp/actions/runs/37719278900))
reached its guest-observed menu checkpoint but failed on a direct-file Python
module import; the module invocation was corrected and pinned by a CLI unit
test. A separate skipped-source-event concurrency cancellation was resolved
before the first full pass.

**New bounded status:** native Windows first-race frontend-to-race audio
output *presence, coarse phase dynamics and post-startup queue continuity*
are demonstrated end to end. **Still open:** exactly aligned reference/native
PCM and DSP/notes/SFX equivalence, actual speaker/device latency,
pause/resume/Restart/Exit-to-Frontend transition acoustics, and device
loss/recovery. Do not amend authoritative guest cadence or replace original
SPC sounds to address unmeasured fidelity differences.

## Stock guest Start pause/resume audio envelope (diagnostic)

The next real-output discriminator derives three fresh-process Windows routes
from the existing accepted `tests/input/ui-pause-route.script`. They
stop at the guest-observed `ui-pause-before`,
`ui-pause-after-start` and
`ui-pause-after-resume` WRAM dumps, then add exactly 30 passive guest
frames and a second checked dump to bracket each checkpoint. The derived
routes require respectively **zero, one, and two** literal stock
`press start 2` commands and an observed in-race flag; no
synthetic guest state or newly guessed pause input is permitted.

The separate process for each checkpoint writes signed-16 stereo SDL3 disk
output plus production queue counters. The 1-second device tail's left/right
RMS and nonzero fraction are retained in
`audio-stock-pause-phases.json` alongside relative phase ratios and
startup-versus-later underflow counts. Silence in the observed pause phase
is **permitted and reported**, not treated as an automatic failure; no
pause-specific missing-output-frame threshold is imposed until the native
captures establish normal stock behaviour. The report fails closed on
incomplete/unsupported capture provenance, missing or mistimed guest
checkpoints and impossible counters; raw music/audio bytes are deleted
locally and are never uploaded as artifacts.

**Ownership limitation:** these are original *guest Start* pause edges from
the accepted stock scripting path. They do **not** yet exercise the
Modern **host-owned frozen guest** pause menu, which can stop scripted guest
frames while it is open. That product-specific acoustic test needs an
independent host-input/host-presentation harness and must avoid interfering
with active Modern pause/Restart PRs. Neither capture proves precise
guest-to-SDL-sample latency or exact DSP content.

## First Windows stock Start pause/resume envelope, 2026-10-08

The first six-phase packaged Windows output acceptance
[37721804984](https://github.com/gamesbyian/UR-Recomp/actions/runs/37721804984)
**passed**, reusing verified source build
[37721010318](https://github.com/gamesbyian/UR-Recomp/actions/runs/37721010318).
The original three first-race checkpoints stayed green, then the new stock
guest Start route passed at the three native guest-frame checkpoints:

| Stock guest phase | Observed guest frame / post frame | SDL device tail RMS | New post-startup underflows / missing frames | Audible source drops |
| --- | --- | ---: | ---: | ---: |
| Before Start | 985 / 1015 | 6350.51 | 0 / 0 | 0 |
| After first Start | 1048 / 1078 | 53.42 | 0 / 0 | 0 |
| After second Start | 1111 / 1141 | 5811.22 | 0 / 0 | 0 |

The observed **pause-to-before RMS ratio is about 0.0084** and the
**resume-to-before ratio about 0.915**; this suggests the stock pause sharply
attenuates device output and resume restores it. The early callback underflow
counter remained concentrated in the first stats interval for each separate
process, with no new underflows or missing frames thereafter. This is real
packaged-Windows output evidence, not an assumption about the game.

`tools/analyze_audio_pause_phases.py` now accepts opt-in
`--max-paused-to-before` and
`--min-resumed-to-before` ratios and guards against nonfinite
limits or a silent pre-pause baseline. **These ratio limits are not
automatically enforced yet**. Repeat the packaged-Windows capture to ensure
the attenuation and recovery remain stable across fresh process and runner
scheduling before selecting conservative acceptance thresholds. Keep the
stock Start probe separate from Modern host-owned pause, Restart Race and
Exit-to-Frontend acoustics.

## Repeated stock Start pause gate, 2026-10-08

The second independent fresh-process capture
[37722175343](https://github.com/gamesbyian/UR-Recomp/actions/runs/37722175343)
also passed the full six-phase packaged Windows test:

| Stock guest phase | First tail RMS | Repeat tail RMS |
| --- | ---: | ---: |
| Before pause | 6350.51 | 6348.71 |
| After Start | 53.42 | 72.94 |
| After resume | 5811.22 | 5803.53 |

Both captures used the existing verified Windows package from
[37721010318](https://github.com/gamesbyian/UR-Recomp/actions/runs/37721010318),
but **separate fresh processes** and independent SDL file output. Across
both runs, the guest Start input counts and 30-frame post markers matched
all three canonical named checkpoints. Production queue snapshots showed
zero audible dropped native samples and zero post-startup underflows and
missing frames in every phase.

These repeats justify conservative **relative, not absolute** acceptance
requirements for the original stock guest Start path:

- paused-to-before one-second tail RMS ratio **at most 0.05**;
- resumed-to-before one-second tail RMS ratio **at least 0.50**;
- zero audible source-ring drops and zero post-startup underflows/missing
  output frames across all three independent processes.

The measured paused ratios were about 0.0084 and 0.0115, and resume
about 0.915 in both runs. The chosen thresholds allow much wider runner
variation than observed, while detecting an unexpectedly loud paused guest,
a failure to restore game sound, or sustained playback starvation. This
does **not** assert exact sample timing, measure clicks/transition acoustics
at frame precision or validate the Modern host-owned pause menu. Device
disconnection and frontend/restart audio transitions remain separate.

The machine-readable pause-phase reducer also emits **relative decibels**
against the measured pre-pause RMS for each fresh-process case. A literally
silent interval uses a JSON `null` dB value rather than a
fabricated measurement or nonfinite infinity; raw RMS and channel data remain
available. This provides a useful common scale for later pause fade and
transition-acoustic tests without treating absolute SDL amplitude as fixed.

## Mandatory Windows stock pause gate acceptance

The first mandatory-gate execution
[37722644607](https://github.com/gamesbyian/UR-Recomp/actions/runs/37722644607)
**passed** after conservative pause attenuation and recovery limits were
enabled. Real packaged Windows SDL3 device-output RMS was:

- Before guest pause: **6350.51**
- After stock guest Start pause: **26.37** (**−47.6349 dB** relative)
- After stock guest Start resume: **5803.53** (**−0.7823 dB** relative)

This independently satisfies the paused/pre ≤0.05 and resumed/pre ≥0.50
rules. Each of the three pause-phase processes verified both guest-frame
dumps with exactly 30 post-boundary frames. All measured phases had zero
audible dropped source samples and zero new underflows or missing output
frames after their initial startup interval. The existing Main Menu,
Now Playing and Race Entry phase acceptance passed in the same Windows run.

These accepted claims belong strictly to the **stock guest Start** path.
They do not establish exact waveform identity, hardware latency, or the
Modern host-owned frozen pause/Restart/Exit-to-Frontend acoustic lifecycle.


## Bounded device-output transition-envelope diagnostics

The six-checkpoint Windows audio job now records **three seconds of SDL3
device output preceding each stock guest Start pause checkpoint**, divided
into 100 ms buckets. Each bucket contains left/right RMS, peak sample,
fraction of literal zero samples, and the maximum absolute difference
between consecutive sample values (including transitions between buckets).
The capture also retains device-rate sample counts and times relative to
the *end of the device file*. The evidence is written as three small
`audio-envelope-ui-pause-*.json` summaries; the raw stereo
PCM remains disposable and is deleted before artifact upload.

These data can distinguish a fade into silence from a sudden level change,
identify candidate clipping or discontinuities, and describe audio recovery
after the stock guest Start press without imposing an arbitrary click or
latency threshold. **They are not aligned to exact guest-frame timestamps.**
SDL queueing, resampling and file-flush timing may shift the apparent onset
of a pause or resume. The peak adjacent-sample step is a numerical transient
candidate, not proof of an audible defect. The well-established one-second
relative-RMS attenuation/recovery and zero-steady-starvation gates continue
to enforce the shipping stock-pause contract unchanged. Modern host-owned
frozen pause still requires its own acoustic evidence.


## Real stereo envelope shape from the first native capture

The first live Windows envelope run
[37731532014](https://github.com/gamesbyian/UR-Recomp/actions/runs/37731532014)
passed all six original checkpoints and emitted three additional 30-bucket
100 ms SDL3 device-output envelopes. The stock guest Start **paused** phase
contained 0.9 seconds of *literal digital silence* in its final nine buckets.
In the preceding adjacent buckets, combined RMS declined from approximately
2234 to 959 to 130 before the silent stretch. The **resumed** capture
contained an interior five-bucket (0.5-second) literal silence stretch,
then output rose through RMS approximately 88, 945, 2615, 3419, 4399
and 7878 across consecutive 100 ms windows. This establishes a real
transition *shape* visible in host output, rather than only comparing
one-second pre/post RMS. These are observations relative to the end of
independently captured device streams, **not** calibrated guest-frame onset
times or a proven sound fade algorithm.

The diagnostic reducer
`tools/summarize_sdl_pause_envelopes.py` now emits a
cross-phase machine-readable report of the 30 per-bucket RMS levels, exact
digital-silence positions, leading/trailing silence duration, channel peaks
and maximum adjacent-sample steps. It checks that the three input envelopes
are SDL3 stereo 100 ms data from a full three-second tail, with consecutive
end-relative offsets, physically valid samples and consistent RMS values.
Literal silence is measured rather than approximated by a guessed
noise floor. **No new click, fade-duration or absolute onset threshold is
enforced.** Such a threshold would require stronger guest/device offset
calibration and repeated real output evidence. The original stock Start
attenuation/recovery and zero-post-startup-starvation gates remain required.

The Modern host-owned pause path may stop simulation and continue host
presentation; this original guest Start envelope cannot substitute for
that separate acceptance.


## Packaged Windows Modern Volume output effectiveness

The existing Modern Options Volume row delegates to SNESRecomp's original
`[Sound] Volume` mechanism; Linux native acceptance proves a
real UI selection changes the framework configuration and survives process
exit, with no second Modern host-owned volume store. That does not, by
itself, prove the chosen volume actually affects the signed-16 stereo
stream arriving at the Windows SDL3 device.

The Windows specialist audio workflow now stages three additional
independent processes over one disposable **shared framework user-data
root**, using the existing production `UR_VOLUME_OPTIONS_ACCEPTANCE`
hook and canonical `modern-focus-pause.script` route:

1. **before / verify:** reach a real 1P race and record both device PCM and
   the framework's loaded Volume percentage, then quit;
2. **adjust:** traverse the actual host pause menu, Options and Volume row,
   using the existing two Left presses plus Enter; require the three
   framework Volume observations, then quit;
3. **after / verify:** start a fresh process with the same user data and
   observe the selected Volume percentage loaded from the framework's
   persistence layer, again recording real SDL3 device output.

The `tools/analyze_windows_volume_output.py` reducer fails
closed unless the framework's initial value, UI-selected value and
fresh-process loaded value agree with the established **minus-five-point**
UI acceptance contract. It also verifies that both non-synthetic Windows
capture summaries represent audible stereo SDL3 S16 output at 44.1 kHz,
then reports relative whole-capture and final-one-second stereo RMS
amplitudes **within that one Windows route**. Raw PCM remains disposable;
only logs and bounded metrics are uploaded.

**No acoustic gain threshold is yet imposed:** a change in a nominal
framework Volume percentage does not establish an exact linear amplitude
law across all music/SFX, startup/exit timing or SDL queue phases. First
measure paired fresh-process output and its run-to-run repeatability.
This volume test does not modify the framework mixer, route, sound assets,
pause/Restart lifecycle or user-facing Options behaviour.


## First Windows Modern Volume PCM outcome and same-setting control

[Windows audio acceptance 37732652603](https://github.com/gamesbyian/UR-Recomp/actions/runs/37732652603)
passed the real Modern host pause → Options → Volume UI and fresh-process
persistence check. The framework Volume value started at **100**, was
selected through **95 → 90 → 95**, and a new process loaded **95**.
Both the pre-adjustment and post-adjustment runs produced audible SDL3
S16LE/44.1 kHz stereo PCM with zero clipped samples.

However, the first paired *device-output* captures were not sufficiently
well aligned to imply a linear gain law. Whole-file RMS was
**3325.62** before and **2575.81** after (ratio **0.775**), while
last-one-second RMS was **6876.54** before and **3046.94** after (ratio
**0.443**). Output duration differed by approximately **46 ms** and
the tail's nonzero-sample fractions were approximately **1.00** and
**0.74**. The differing nonzero fractions are especially important:
pure scalar attenuation of the same nonzero samples should not generally
turn that many samples into exact zeros. Differences could reflect
different device capture phase, original soundtrack timing/content,
quantized gain or a combination. Do not claim the observed 0.443 ratio
is the framework's exact response to one nominal 5-point adjustment.

The Windows acceptance now runs a fourth **after-repeat** process,
loading **the same selected 95% value** but capturing a fresh SDL3 device
stream again. This A/A control compares whole-recording and last-second
RMS and nonzero fractions between independent processes without a
second adjustment. It distinguishes ordinary same-setting output
variability from the A/B comparison. The required checks remain
correct real UI navigation, single framework Volume authority, persistent
fresh-process selection, and authentic device-output provenance; a
hard acoustic ratio is **not** justified until the A/A variance and
time-aligned signal differences are measured.


## Same-setting control reveals unaligned Volume audio windows

The A/A Windows Volume control
[37733295930](https://github.com/gamesbyian/UR-Recomp/actions/runs/37733295930)
passed all existing checkpoints, verified **100 → 95** through the real
Modern Options row, and independently loaded the persisted **95%** value
in both later processes. Its 95%-to-95% output nonetheless had a
**3.5995× last-second RMS ratio** and **1.6505× whole-file RMS ratio**.
In the first 95% capture, tail nonzero fraction was about **0.7346**;
in the repeat it was essentially **1.0**, confirming the compared device
tails sampled substantially different audio content or timing despite an
identical framework volume setting.

The canonical input logs demonstrate that the processes were not at
exactly the same guest frame: the two 95% runs observed `race-entered`
at guest frames **1041 and 1043**, and requested desktop quit after
**1100 and 1102** simulated frames. Even the same-menu startup boundaries
can differ by several frames under native scheduling. These differences
alone do **not** prove what caused the large amplitude variation; they
prove that an unqualified same-tail-window amplitude comparison is an
unsound exact-gain measurement.

`tools/analyze_windows_volume_output.py` now requires the
original three authoritative named guest checkpoint dump markers and
desktop simulation totals for each fresh-process capture. It publishes
guest-frame deltas separately for A/B and A/A, and states explicitly
that audio sample-clock alignment is unknown. Missing, duplicated or
out-of-order route markers fail closed rather than silently accepting
unrelated PCM. Relative RMS remains **diagnostic only**.

**Shipping interpretation:** the Volume menu, original framework config
authority, persistence and real SDL3 device-output presence are proven.
The exact amplitude response to a five-point Volume adjustment is
**not** proven. Further work must compare a guest/sound-state-aligned
window or instrument mixer gain at its ownership seam; do not tune the
stock audio DSP, timing or Volume control based on these aggregate
captured-race-tail ratios.


## First native Modern host-owned frozen pause audio probe

Unlike the stock guest Start route, the Modern pause is owned by the host
session. A successful pause **stops guest frame advancement** but preserves
host event pumping and presentation. The canonical guest `wait`
script therefore cannot advance to another stop/dump instruction after
Modern pause opens. Applying the stock-Start 30-guest-frame post-marker
contract here would be incorrect.

The Windows specialist audio acceptance now launches the **actual packaged
Modern product** and uses its already existing
`UR_PAUSE_OPEN_ACCEPTANCE` native hook. The hook waits for a
real guest-observed active race, then opens the real Modern host pause on
an emulated-frame boundary. A bounded external native-Windows supervisor
waits for **both** `UR_PAUSE_STATE paused=1` and
`UR_PAUSE_ACCEPTANCE OPENED` diagnostic evidence after the
authoritative `race-entered` script dump. It holds the paused
host running for **four seconds of wall time**, then intentionally terminates
the whole launched Windows process tree. Unexpected early exit, absent or
duplicated pause markers, an observed resume, or a timeout fails closed.

During that held frozen-guest interval the same process continues writing
real signed-16/44.1 kHz stereo output through SDL3's disk playback driver.
The existing production PCM analyzer records a one-second tail and the
3-second, 100 ms per-channel envelope analyzer describes silence/levels,
peaks and adjacent-sample steps. This **first diagnostic probe does not
assume** Modern host pause should have the same attenuation ratio as the
stock guest Start path, nor does it reject ordinary buffer draining as a
failure without measured native evidence. Killed-process output is
explicitly **not** a graceful close/flush or playback latency test.
Guest-frame and wall-time clocks remain distinct, and only small JSON
metrics/native diagnostics are published; no raw audio is retained.

Once the actual Windows output is measured, compare that envelope against
the stock guest pause and separately test host resume/Restart/Exit
acoustics. Do not force the guest to simulate frames while frozen, alter
SNES APU state, or change the Modern pause menu merely to satisfy the
capture.


## First real Modern frozen-pause output and bounded silence gate

Native Windows audio acceptance
[37734723303](https://github.com/gamesbyian/UR-Recomp/actions/runs/37734723303)
passed the host-owned pause hook against a verified packaged executable.
After the **real guest race checkpoint at f1044**, the product reported
`UR_PAUSE_STATE paused=1 surface=1` and
`UR_PAUSE_ACCEPTANCE OPENED`. The external supervisor then
held the guest-frozen host active for **four seconds wall time** and
intentionally terminated the Windows process tree. It recorded
**22.384 seconds** of real SDL3 S16LE 44.1 kHz stereo device output, with
whole-capture RMS **3009.72** and nonzero-sample fraction **0.6362**,
demonstrating the game's soundtrack had actually played.

**The final one-second tail contained literal zero samples in both
channels (RMS 0.0)**. More strongly, every one of the final **30 consecutive
100-ms stereo buckets** covering three full seconds had combined and
per-channel RMS **0**, sample peaks **0** and both channel zero fractions
**1.0**. This shows output fell to complete digital silence while the
Modern host was still alive and the guest was frozen. It is a separate
mechanism from original guest Start pause, which was measured fading
down under continuing guest simulation.

A focused `tools/check_modern_host_pause_audio.py` reducer now
enforces the **audible before → fully silent frozen host** contract in
the specialist Windows audio gate. It requires original native race,
host-paused and pause-open diagnostics; genuine device-output provenance,
audible stereo signal earlier in the same process, a full one-second zero
PCM tail, and 30 complete zero-energy stereo buckets in the final
three seconds. This is deliberately strict about *literal digital silence*
and deliberately does **not** infer a precise guest/SDL onset time,
hardware latency, smooth fade shape or successful subsequent resume.

The gate must pass on a second independent fresh-process Windows run
before treating it as repeatably proven. Original stock audio, guest
cadence, framework mixer and Modern pause implementation are unchanged.
