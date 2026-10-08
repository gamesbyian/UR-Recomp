# Production audio queue continuity evidence

The pinned SNESRecomp framework already records always-on APU/ring/callback
counters in Release builds (runner/src/audio_trace.c). They are available
without rebuilding the game with diagnostic tracing. Set the environment
variable SNESRECOMP_AUDIO_STATS to a fresh, writable absolute filename before
launching the Windows x64 executable. The framework writes one snapshot line
approximately every second, including a header naming every counter.

Run after a deterministic session:

    python tools/analyze_snesrecomp_audio_stats.py audio-stats.txt --json-out audio-queue.json

The reducer checks a strict named schema, unsigned integers, cumulative-counter
monotonicity, plausible dropped-audible attribution, and at least two snapshots.
It reports **interval deltas from first to last retained sample**, not process
totals, so loading/initialization losses are not silently conflated with
later gameplay. It also reports observed wall milliseconds and ring occupancy.
The default command measures and reports. Once phase-specific baselines exist,
explicit thresholds can turn those measurements into gates:

    --max-new-audible-drops 0
    --max-new-underflows 0
    --max-new-missing-frames 0

These thresholds are independent and opt-in. Early startup, pauses, SDL device
scheduling and fast script execution may generate benign missing frames.
Therefore **do not set all three limits to zero by assumption**. In particular,
the framework distinguishes native-sample ring overflow from audible ring
overflow (|L| or |R| above 256 in the dropped sample), and distinguishes
output underflow episodes from total missing device-rate frames. Absolute
first-sample counters may already be nonzero when the first snapshot appears.

This tool does not inspect audio content. A callback can consume silent samples
without recording a missing frame. Pair queue stats with real playback-device
samples from docs/AUDIO-NATIVE-OUTPUT-ACCEPTANCE.md (SDL3 disk backend) and the
independent named Snes9x/Beetle reference captures before making fidelity
claims. Once capture timelines have a proven guest-frame correlation, measure
steady-state race, pause/resume, Restart Race, frontend reboot and device
loss/recovery independently. Preserve the existing host audio ring and guest
cadence; investigate nonzero audible loss rather than masking it by stretching
the game clock.

Do not commit extracted PCM, proprietary source assets, or device-unique paths.
