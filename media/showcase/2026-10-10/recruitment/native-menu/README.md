# Native original title and menu navigation capture

**Capture successful; source frames visually inspected.** This media-lane source is the actual pinned Baldosa Uniracers guest, rendered through its real SDL host, not an animated slideshow or a reconstructed title. The recording shows the stock 1994 title/menu presentation in a 16:9 physical output window; the original 256×224 game image is pillarboxed, rather than falsely extending the title artwork to 342 logical pixels.

[Watch uninterrupted title/menu footage (15 seconds, 1080p)](ur-native-title-menu-900f.mp4)

[Inspect real title poster](ur-native-title-menu-poster.png) · [machine-readable provenance](native-title-menu-provenance.json)

- **900 consecutive host-presented guest frames**, from guest frame 30 through 929 inclusive, at an encoded nominal 60fps.
- Pinned original `race_1p.txt` input script with its **only change** being `turbo on` → `turbo off` for visible real-time menu navigation. Preserves all original gameplay inputs and timing gates.
- Baldosa native game `10b864b9d14a7b7416dd909eb7b054c88faef101`; pinned SNESRecomp host `075fbe4c8e0d97b0013be541795c39cb644a9709`; verified USA retail ROM SHA256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`.
- Actual host SDL readback **960×540**, clean MP4 **1920×1080** nearest-neighbor 2×; stock game logical content **256×224**. Title scene **does not** use the calibrated 342×224 live-racing course-world materializer.
- FFV1 source lossless SHA-256 `345dc41fd5f7a8917bdda5a7cc61701ae28e2c5556483260640a0a8544cbc387`, native host executable SHA-256 `ea8aef42b03328d313225c1248807a6cf705a51fd6420c905a0c60c277956bb6`.
- Complete guest CRC streams are byte-identical across the capture-disabled and capture-enabled full route, SHA256 `3840aaf203972d63d93aaeb0e45a2c2bf64c840bd931afeb3201a28a883bd4d5`; 900 exact chronological presentation frame IDs and full 900-frame FFV1 decode passed.
- Native successful execution [run 38091213101](https://github.com/gamesbyian/UR-Recomp/actions/runs/38091213101), original 14-day lossless CI artifact **11684691069**. Its publishing step stopped after validation because of a wrong route-hash lookup path; media-only artifact recovery [run 38091729776](https://github.com/gamesbyian/UR-Recomp/actions/runs/38091729776) independently checked the retained FFV1 source, index and MP4 counts and published the committed video, poster and provenance without replaying the guest.

Independent actual decoded frames from the committed MP4 are retained under [frames/](frames/) at ordinals 0, 300, 600, 750 and 899 (guest frames 30, 330, 630, 780 and 929). Visual inspection shows startup black at ordinal 0, the authentic title illustration at ordinal 300, **PICK YOUR UNI** at ordinal 600, and **PICK TOUR** with Crawler selected at ordinal 899. This confirms actual menu progression, not just a static title. The first blank video frames are authentic startup and can be trimmed for a later promotional edit without implying extra gameplay frames.\n\nThe original logo/title poster is unmodified genuine game imagery. No commercial original-game soundtrack is attached. This witness supports navigation/intro footage, not a completed Windows Modern frontend or an enhanced title art claim.

## Reproduction

Pin the above exact game/framework and title ROM, stage the existing read-only Original presenter plus `tools/showcase/stage_native_menu_capture.py` into **only a disposable native framework checkout**, and rebuild the same SDL2 host as QA. Execute the pinned `race_1p.txt` with just the first `turbo on` switched to `turbo off`, once without capture and once with:

```sh
export UR_NATIVE_VIDEO_START=30
export UR_NATIVE_VIDEO_COUNT=900
export UR_NATIVE_VIDEO_OUTPUT=ur-native-title-menu-lossless.mkv
```

With the original `run_route.sh`, the FFV1 file and `.frames.tsv` appear in the recording-on route directory. Validate against original full guest CRC traces and the native guest log using:

```sh
python3 tools/showcase/validate_continuous_native_capture.py \
  --master recorded/ur-native-title-menu-lossless.mkv \
  --frames recorded/ur-native-title-menu-lossless.mkv.frames.tsv \
  --log recorded/log.txt \
  --control-crc control/fd/crc.txt \
  --recorded-crc recorded/fd/crc.txt \
  --count 900 --min-start 1 --logical-width 256 \
  --rom-sha256 859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478 \
  --git-sha <the-source-commit> --route media-native-title-1p \
  --out native-title-menu-provenance.json
```

Don't claim a fully widescreen title illustration or Modern menu from this Original-only recording. Those are separate visual/product demonstrations requiring their own actual host evidence.
