# Experimental Modern host Resume audio output (Windows x64)

The shipping packaged-Windows audio checks already cover the stock guest
Start pause/resume and Modern host-owned *held-pause silence*. What remains
unproven is restoring audible output after **actual Modern host Resume**.

An opt-in native test is available in tools/capture_modern_resume_audio.py.
It runs the unchanged packaged Windows executable with the canonical
tests/input/modern-focus-pause.script, reuses the existing
UR_PAUSE_OPEN_ACCEPTANCE hook to freeze the real guest from the race,
then sends a Win32 Escape key message to the uniquely identified, visible
game window belonging to the launched process tree. It does not poke guest
state, edit audio DSP, or change the frontend.

## How to run on an interactive Windows desktop

From the repository root, set these environment variables before launch:

- SDL_VIDEODRIVER=windows (requires a visible game window; no offscreen)
- SDL_AUDIO_DRIVER=disk
- SDL_AUDIO_DISK_OUTPUT_FILE=<absolute temporary .raw path>
- SDL_AUDIO_FORMAT=S16LE
- SDL_AUDIO_CHANNELS=2
- SDL_AUDIO_FREQUENCY=44100
- SDL_AUDIO_DISK_TIMESCALE=1.0
- UR_PRODUCT_DIAGNOSTICS=1
- UR_PAUSE_OPEN_ACCEPTANCE=1
- UR_RECOMP_USER_DATA_ROOT=<fresh disposable directory>

Run the probe using the package's real run-uniracers.cmd launcher and
the existing canonical first-race script:

    python -m tools.capture_modern_resume_audio <launcher.cmd> <modern-focus-pause.script> <native.log> <device.raw> --json-out <report.json>

The probe requires exactly one real race, one host pause, one host Resume
acknowledgement on the same product surface, one second of *literal
digital silence* before Escape, and a full later second of non-silent
left/right SDL S16LE output. While the game runs, it bookmarks those two
SDL file-size boundaries instead of attempting to open the raw file, which
Windows SDL holds exclusively. It terminates the process tree intentionally,
reads both one-second windows after the SDL handle is closed, and writes only
reduced JSON. Delete temporary raw PCM after inspection.

The first packaged-Windows audio proof (run 37755041540) reached the
host-held pause and identified the actual game window. Its initial live PCM
read failed with Windows PermissionError because SDL holds the device file
exclusively; the bounded post-close bookmark procedure addresses that native
capture limitation. Resume/output recovery is **not certified until the
corrected native proof passes**. The existing mandatory offscreen pause-
silence acceptance remains unchanged.

A successful run would prove audible-to-silent-to-audible playback in
one real Windows game process, but not exact note/SFX/DSP parity, latency,
click-free transitions, or speaker-level output. Pure reducer/order
regressions live in tests/unit/test_capture_modern_resume_audio.py.
