# Modern Restart audio: guest Start key-leak discriminator

## Why this experiment exists

Actual packaged-Windows Modern Pause -> Restart has produced both audible
recovery and prolonged **literal digital silence**. The guest continues
simulating in the failing captures, the SPC/DSP audio source ring continues
producing samples and the SDL consumer remains active. A separate candidate
which cleared the host output ring and SDL stream after visible rollback
was tested in a newly built Windows executable and **rejected**: two of
three trials still went silent and the attempted fix introduced output
underflow episodes (see closed PR #880).

There is a narrower, audio-specific alternative to an SPC/DSP fault.
The pinned SNESRecomp input source `runner/src/keybinds.c` maps the
default **Return** key to the original SNES **Start** button in both P1
and P2. Modern host Pause's Restart menu also uses **Return** to confirm
Restart. The live product has a host-input suppression and release latch
intended to prevent this key from reaching the original guest. If the
release timing occasionally allows a Start edge through, the guest could
enter its own stock pause *after* Modern Resume has reported paused=0.

This fits the *shape* of the failed PCM: a brief restart burst followed
by ~0.7–0.8 seconds of attenuation to exact zero, resembling the
original game Start-pause acoustic envelope. Similar shapes are only
circumstantial evidence; **no Start-key leak has been proven** and the
host may already suppress it correctly.

## Matched packaged Windows A/B

The audio-only specialist workflow
`.github/workflows/windows-modern-restart-audio-probe.yml` now runs
**six independent fresh-process Restart probes on the exact same
verified main Windows portable package**, after its original Restart
gate and independent normal-race control:

- Three trials with the framework's ordinary P1/P2 `Start = Return`.
- Three trials with P1/P2 `Start = None` *in disposable user-data
  `keybinds.ini` files only*.

The six runs all use the same unmodified canonical first-race script,
same stock ROM, original Modern host Pause/Restart menu and real SDL
Win32 **Down/Enter** events. The menu still receives Return in both
groups. No game/UI/controls/source code or player keymap is changed.
The game's own script never requires Start to reach its confirmed race.

Each trial requires real Restart selection, host Resume, continued
original guest and a full eight seconds of genuine SDL3 stereo output
envelope. `tools/summarize_audio_restart_keymap_ab.py` produces
per-cohort audible stereo restoration counts, final left/right RMS and
the number of trailing literally silent 100 ms buckets. Because silent
Restart is the phenomenon under investigation, the experimental arm
does not fail solely because one or more samples are silent. Missing
or ambiguous guest/host evidence and incomplete captures still fail.
The original strict player-facing Restart sound gate stays red if it
fails; **no acceptance threshold is weakened**.

Only JSON and logs are retained. Temporary raw SNES PCM is removed.
The comparison is exploratory, with just three runs per group:
consistent recovery only when Start is unbound would strongly motivate
a targeted frontend/input-ownership fix **in coordination with the
frontend owner**. Similar silent rates in both groups would argue
against keyboard Start leakage and redirect attention to rollback
scheduling or DSP state. Any observed outcome requires further
repeats to estimate its stability; don't interpret three trials as
a statistically decisive reliability result.
