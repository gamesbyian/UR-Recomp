# Windows 48 kHz SDL device-output acceptance

Windows consumer audio cannot assume every playback device operates at the
original SNES DSP rate or even at the 44.1 kHz SDL rate exercised by the
initial native acceptance. A 48,000 Hz stereo device is a common Windows
output path, and a fixed 44,100 Hz diagnostic cannot by itself establish
resampling, continuity and audible channels at that alternate device rate.

The existing specialist `.github/workflows/windows-native-audio-output.yml`
now runs an additional **actual packaged executable** in a fresh user-data
root, on the unchanged stock `tests/input/reach-first-race.script`. It
chooses the SDL3 disk audio output driver with `SDL_AUDIO_FREQUENCY=48000`,
signed-16 stereo, and checks that the real guest reaches its `race-entered`
WRAM dump. SDL must announce an actual *negotiated* 48,000 Hz playback
stream; setting the environment variable alone is insufficient.

`tools/analyze_sdl_disk_audio.py` validates the full PCM file, source
path, sample format, stereo amplitudes, and audible one-second race tail.
The Release audio-queue reducer independently requires no dropped audible
samples or underflow/missing device-rate frames **after** the measured first
startup interval, while retaining that interval's original counters.
`tools/check_native_audio_device_rate.py` combines the source-provenance
reports, explicitly verifies 48,000 frames in the final one-second
window, both audible channels, and the correct real-device rate. It rejects
an unexpected fallback to 44,100 Hz and a test that passed using only
loud frontend samples before a silent race.

The raw PCM remains disposable and is deleted before uploading only JSON
and native diagnostics. This source-rate/device-rate test must be
interpreted as **audible output and steady delivery**, not proof of exact
musical pitch, individual SFX, DSP echo or subjective hardware latency.

The 48 kHz gate runs in the *existing* packaged-Windows specialist audio
workflow after its original 44.1 kHz three-phase checkpoint gate; no
separate game recompilation or new automatic Actions workflow is needed.
Run-time sample-rate decisions remain the existing SDL3/framework authority.
