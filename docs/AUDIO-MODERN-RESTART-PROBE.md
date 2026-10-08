# Real Windows Modern Restart stereo playback proof

## Player-facing contract

A player entering Modern pause during a 1P race and selecting **Restart**
should hear the restarted race again. A paused SDL device can produce literal
silence even if the guest is healthy, so the acceptance must prove both
that the guest resumed and that the *real Windows audio output* becomes audible.

`tools/capture_modern_restart_audio.py` drives the packaged
`run-uniracers.cmd` with the established first-race script
`tests/input/modern-focus-pause.script`. The audio-specific
`tests/input/audio-modern-restart.script` keeps that canonical input
route up to its paused long wait; its only change is a deterministic
post-Restart guest checkpoint and extended observation wait. No guest
memory is poked and no live product frontend or SNES audio code is modified.

The production acceptance hook `UR_PAUSE_OPEN_ACCEPTANCE=1` opens the
real Modern pause only after an active race. The native Windows supervisor
finds the sole visible packaged game window belonging to its own process
tree, holds the actual paused SDL output four wall-clock seconds, and
bookmarks the stereo PCM byte boundary. It then sends normal Win32
Down/Enter key messages to select/activate the production **Restart**
row. The session must acknowledge Restart as available/selected, then
return to `paused=0` on the same surface; the original guest script
must advance and produce its post-Restart checkpoint. Four seconds after
resumption, the supervisor bookmarks the returned output, terminates
the full process tree and decodes both stereo windows from the closed
SDL disk file (Windows locks this file exclusively while running).

The accepted sound contract requires a complete second of *literal
digital silence* at the held pause boundary and a complete later
one-second window of audible **left and right** 44.1-kHz S16LE output.
The specialist `windows-modern-restart-audio-probe.yml` job uses
an already verified first-party `main` Windows portable package
without rebuilding or altering shipping packaging. Temporary raw PCM
is discarded, retaining only bounded log/JSON. Unit tests cover
synthetic or wrong-order host events, missing restarted guest progress,
and script provenance.

## Evidence limits

Await the first real Windows run before claiming Restart audio restoration.
Even a pass is a device-output and guest-progress claim, not proof that
individual music voices/SFX, DSP waveforms, sample-level transient shaping,
acoustic click or speaker hardware latency match original SNES behavior.
