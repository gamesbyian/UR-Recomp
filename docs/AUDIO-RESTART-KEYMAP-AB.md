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
