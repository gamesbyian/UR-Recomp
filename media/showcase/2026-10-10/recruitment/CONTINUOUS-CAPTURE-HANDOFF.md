# Continuous native footage candidate (capture lane)

This is an **unexecuted recording implementation**, not accepted gameplay footage.
Issue [#1223](https://github.com/gamesbyian/UR-Recomp/issues/1223) remains open until an actual bounded native recording has been produced, inspected, validated and merged.

## Native recording

The minimal disposable-SDL2 hook in
`tools/showcase/stage_continuous_native_capture.py` attaches immediately
before the pinned native SDL host's `SDL_RenderPresent`. It reads the actual
drawable with `SDL_RenderReadPixels`, pipes BGRA pixels directly to FFmpeg's
lossless FFV1 encoder, and records an ordinal/guest-frame index. This is a
host drawable, **not** the 342×224 logical raster or guaranteed 4K output.
The actual drawable dimensions are recorded. The hook refuses an unexpected
SDL host source anchor.

Stage only in a temporary upstream Baldosa checkout *after* the existing
Original 342-wide renderer preparation:

```sh
python3 tools/showcase/stage_continuous_native_capture.py --framework baldosa/snesrecomp
# Rebuild the same pinned native Baldosa host already used by QA-08.
# Execute its existing race_2p_split route with identical inputs twice:
# (1) no recording; (2) enable the following in the host process:
export UR_NATIVE_VIDEO_START=2208
export UR_NATIVE_VIDEO_COUNT=600
export UR_NATIVE_VIDEO_OUTPUT=ur-continuous-native-lossless.mkv
# Run the proven route from the same working directory using the existing route wrapper.
# Save the host stderr and BOTH complete fd/crc.txt traces.
```

The start and length above are *targets*, not evidence of a successful
600-frame capture. Route `race_2p_split` previously ran 2,473 guest frames
and reached GO at guest frame 1989, so 2208..2807 needs a longer run.
**Extend only a verified existing deterministic route with unchanged
inputs** or select a different already-pinned post-GO route whose actual
runtime encompasses the target. Do not extrapolate from a 2,473-frame
test. A successful stdout log is insufficient: use the strict validator.

```sh
python3 tools/showcase/validate_continuous_native_capture.py \
  --master ur-continuous-native-lossless.mkv \
  --frames ur-continuous-native-lossless.mkv.frames.tsv \
  --log captured-host-stderr.log \
  --control-crc disabled/fd/crc.txt \
  --recorded-crc enabled/fd/crc.txt \
  --count 600 --rom-sha256 <verified-USA-ROM-SHA256> \
  --git-sha <full-repository-commit> --route <pinned-deterministic-route> \
  --out native-continuous-provenance.json
```

The validator requires every recorded host-presentation identifier to be
consecutive, exactly the specified number of **decoded** FFV1 frames,
consistent SDL drawable dimensions, completed FFmpeg exit status, and
byte-identical full guest WRAM CRC traces against capture-disabled execution.
The stream is labeled a nominal 60-fps encoding; no assertion of exact 60-Hz
guest/display synchronization follows without measuring the host cadence.

**Before public release**, independently verify ROM SHA and native
build pin, record CI run/artifact identifiers, inspect first/middle/last
frames, prove visually active course/racers/HUD, note any defective sprites,
and produce a nearest-neighbor/unmodified clean MP4 from the certified
lossless recording. No current artifact satisfies this requirement.

Known risk: writing 4K BGRA into FFV1 every presentation is expensive.
Prefer native 1280×720 or 1920×1080 physical drawable for an initial
bounded recording while preserving authentic 342-wide guest presentation.
Do not equate a smaller physical drawable with physical 4K evidence.
This observer may reveal missing host presentations; it deliberately does
not fill them, and its temporal cost must be measured.

The existing recruitment teaser remains clearly labeled as sampled
frames until a real continuous capture has passed the gate.
