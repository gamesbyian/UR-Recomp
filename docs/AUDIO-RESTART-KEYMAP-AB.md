# Modern Restart audio: possible guest Start-key leakage

## Observed problem

In packaged Windows Modern Mode, a real Pause → Restart menu selection
sometimes restores the guest and resumes race frame advancement but outputs
several seconds of literal-zero stereo PCM. The uninterrupted race baseline
continues playing. This remains an **open player-facing audio defect**.
The original Restart evidence was preserved in merged PR #866.

An output-timeline-only fix was tested and **rejected**: PR #880 built a
fresh patched Windows executable, which produced two silent outcomes, one
audible outcome and new post-startup audio underflows across three restarts.
That PR was closed without merging the runtime patch.

## Specific new hypothesis

Pinned SNESRecomp defaults map the keyboard **Return** scancode to **SNES
Start** for player 1. The Modern host also uses Return to activate its
selected Pause item. The real Windows audio probe uses a Win32 Return
keydown/up to confirm Restart. The Modern host has an input suppression and
release latch expressly intended to prevent a host-owned confirm from
reaching stock game input.

An intermittent one-frame leak after snapshot load might nevertheless
deliver **SNES Start** to the newly restored game. Stock Uniracers Start
pause/resume has an independently measured audio attenuation transition,
which is a plausible cause of post-Restart digital silence after an initial
short audible segment. No such leak has been established; resemblance of
waveforms alone is insufficient.

## Matched packaged-Windows discriminator

The specialist `windows-modern-restart-audio-probe.yml` retains its original
hard-failing audio gate and uninterrupted race control. It adds **six separate
fresh-process packaged-Windows trials** (three per condition) using the same
verified main executable and the same canonical original-game race script.
The *only intended intervention* is the disposable framework user-root
`keybinds.ini`:

- `[player1] start = Return` and `[player2] start = Return`: standard guest
  Start mapping; Win32 Return activates the Modern menu.
- `[player1] start = None` and `[player2] start = None`: no guest Start
  binding; **the exact same Win32 Return still activates the Modern menu**.

Each trial must observe actual selected Restart, host unpause, and continued
guest execution; preserve real 44.1 kHz stereo paused/resumed windows and 80
separate 100ms output buckets. Each test records bounded JSON/log metadata
without retaining copyrighted PCM. The reducer reports each arm's audible
recovery count and trailing literal-zero duration; it is **descriptive**, not
statistically significant at n=3. Failure to reach authoritative Restart
markers, missing reports or malformed PCM evidence remains an error, whereas
a valid silent-audio failure is retained rather than stopping the experiment.

**Interpretation:**

- Reliable improvement with Start unbound, matched stock pause-state evidence,
  and no changes to the actual Restart action would implicate a leaky
  host-input ownership seam. A follow-up production fix belongs to the
  input/frontend owner, not an audio-side mute or DSP workaround.
- Identical failure patterns under both bindings argue against leaked
  keyboard Start as the sole cause and prioritize APU/SPC/DSP restore/timing
  investigations. Intermittent results in a small sample remain uncertain.
- A green original Restart gate on one run does not erase older failures.
  No Modern Restart audio-shipping claim is made from this experiment alone.

The source guest script, production emulation timing, game keyboard defaults,
and Modern frontend implementation are unchanged.

## First actual packaged Windows result: decisive direction

[Windows run 37776386839](https://github.com/gamesbyian/UR-Recomp/actions/runs/37776386839)
finished six **interleaved, independent** Restart processes using exactly
the same verified portable game build. All six reached selected Restart,
`paused=0` on the same host surface, and the same restarted guest
checkpoint (`audio-restart-guest` at guest frame 1125). Inspection of all
six archived native logs confirmed a separate user-data-root anchor and
`[Keybinds] Loaded keybinds.ini` for every process.

| Disposable SNES Start mapping | Real Restart stereo recovery | Final left/right RMS | Trailing literal zero-output |
| --- | --- | --- | --- |
| Return (normal default) | **0 / 3** | **0 / 0** all three | 57 × 100 ms = 5.7 s all three |
| None (unbound, menu Return unchanged) | **3 / 3** | about **5602 / 6630** | zero buckets all three |

The unchanged guest/script, real Win32 Down/Return activation and same
verified Windows executable make **leaked SNES Start** by far the best
currently supported working hypothesis. All three default-Start failures
showed the same long digital silence. The uninterrupted original-race
control still had audible playback (RMS ~6048), and the separate original
Restart audio gate failed. This is substantially stronger than the prior
intermittent APU/DSP-or-output-timeline speculation, although a small six-run
diagnostic is not a population-level failure-rate estimate.

**Product disposition:** The audio evidence is complete enough to hand off
the precise implementation seam to the frontend/input owner in
[issue #890](https://github.com/gamesbyian/UR-Recomp/issues/890).
The source of the suspected leak is the transition where a host-owned
Return confirms Restart, restores the game and closes the host pause,
while the framework also maps that same key to guest SNES Start.
The frontend should prove whether its once-suppress and
key-release-latch still suppress the held key on **subsequent** restored
guest frames. Fix the ownership handoff; **do not** change the player's
keyboard default to None, paper over the silence with DSP changes, or
remove the failing acoustic acceptance.

This result does **not** establish that any production input fix is
implemented or that normal Modern Restart audio is reliable. That remains
a shipping blocker until fresh default-keymap Windows source builds
repeatedly recover audible stereo without losing ordinary Start input.
