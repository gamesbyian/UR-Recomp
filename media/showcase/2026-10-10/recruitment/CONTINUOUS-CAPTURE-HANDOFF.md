# Continuous native gameplay capture: accepted first 600-frame witness

The initial capture described in the earlier handoff **succeeded** in [native CI run 38089655141](https://github.com/gamesbyian/UR-Recomp/actions/runs/38089655141), which passed and committed a clean MP4, lossless-source poster and exact provenance to [the permanent recording directory](continuous/README.md).

- **600 genuinely consecutive native host-presented guest frames**, from frame 2100 through 2699 inclusive, following the scripted GO at frame 1989.
- Two-player native Original source-backed 342×224 logical widescreen; real SDL drawable **960×540**; clean delivery **1920×1080** nearest-neighbor 2×. Not real physical 4K.
- One input-equivalent recording-off run and one recording-on run produced byte-identical complete guest WRAM CRC sequences. The lossless FFV1 stream independently decoded to exactly 600 frames and had complete, exact, unique chronological frame IDs; no synthetic frames or interpolation.
- Original lossless master and full CI diagnostics remain in temporary GitHub artifact 11683697184. Clean MP4 and machine-readable manifest are committed under `continuous/`.
- Pinned upstream game, framework, ROM and built executable identities, video hashes, exact scripts and route SHA are retained in `continuous/native-continuous-provenance.json`.

## Reproduce it

The media-specific route generator `tools/showcase/extend_native_2p_route.py` takes the pinned upstream `race_2p_split.txt`, preserving all character, menu, gate and input events through GO, switching **turbo off** and extending rightward travel. This deliberately reduces skipped native host presentations. Use the same established Baldosa Original-wide native build from the existing QA-08 workflow. Stage **only into its disposable framework checkout**:

```sh
python3 tools/showcase/stage_continuous_native_capture.py --framework baldosa/snesrecomp
# rebuild exactly the existing native guest + SDL host
# execute the SAME extended route twice:
#   once without UR_NATIVE_VIDEO_* environment variables,
#   once with the explicit variables below
export UR_NATIVE_VIDEO_START=2100
export UR_NATIVE_VIDEO_COUNT=600
export UR_NATIVE_VIDEO_OUTPUT=ur-continuous-native-lossless.mkv
```

The `run_route.sh` wrapper works in its output directory, so FFV1 and the `.frames.tsv` index appear in the recording-on route directory. Then run `tools/showcase/validate_continuous_native_capture.py` against the exact MKV/index/native log, full capture-off and capture-on `fd/crc.txt` files, input route identity, ROM and Git SHAs, as done in the accepted one-shot run.

Actual capture callback: pinned SDL2 `SdlRenderer_EndDraw` between texture presentation composition and `SDL_RenderPresent`, using `SDL_RenderReadPixels`. It records actual drawable pixels, not synthetic reprojected fields. FFmpeg reads a raw BGRA stream and encodes FFV1 losslessly. The host recorder stops after 600 frames and fails closed on discontinuity; the separate validator checks FFprobe's fully decoded count and CRC equality.

## Remaining media work

- Inspect multiple points along the actual sequence, flag OBJ/HUD visual defects, and select the most compelling honest interval, without changing gameplay.
- Produce validated horizontal and vertical recruitment edits. The existing October 10 teasers remain accurately labeled **sampled original frames** and are valid editorial material, not additional continuous gameplay.
- Retire the temporary one-shot workflow after recording; it is not part of the long-term CI matrix.
- Pursue a separate actual 3840×2160 continuous host recording only after the bounded 960×540 success, explicitly attributing both physical readback and logical 342×224 world.
