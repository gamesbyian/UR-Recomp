# First genuine uninterrupted Baldosa two-player gameplay

**Status:** accepted bounded capture; gameplay fidelity and beta QA remain separately gated. Recorded 2026-10-10 in one successful native CI execution.

[Watch clean continuous gameplay (10 seconds, 1080p MP4)](ur-native-2p-clean-600f.mp4)

[View actual lossless-source poster](ur-native-2p-poster-source.png) · [machine-readable provenance](native-continuous-provenance.json)

This MP4 shows **600 consecutive, chronological SDL host presentations** from the running Baldosa native Uniracers implementation. The recording is from guest frames **2100 through 2699 inclusive**, during genuine two-player split-screen play after the scripted GO gate (frame 1989). No temporal interpolation, rebuilt rider motion, invented scenery or editor-generated gameplay frames are present.

## Exact source and delivery identities

| Property | Evidence |
| --- | --- |
| UR-Recomp capture source commit | `4748ae337f38d801039260ca6ed849fd2ca1d7a3` |
| Baldosa native guest commit | `10b864b9d14a7b7416dd909eb7b054c88faef101` |
| SNESRecomp framework commit | `075fbe4c8e0d97b0013be541795c39cb644a9709` |
| Native executable SHA-256 | `04a0656e3c0f84c3ec6f0b0c263c386bc21971bce712f57aba38499fad0252f9` |
| Input | Pin-derived 2P route, same pre-GO input/waits; normal pace after GO; see `tools/showcase/extend_native_2p_route.py` |
| US retail ROM SHA-256 | `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478` |
| Internal race-world raster | Original fallback, 342×224 logical columns, 43 new-world source columns per side |
| Actual SDL drawable readback | **960×540** physical pixels |
| MP4 delivery | **1920×1080**, nearest-neighbor 2×, 60-fps nominal timing |
| Lossless master | FFV1, FFmpeg, SHA-256 `1e327be73d137b5b298b042cc666709c94a7f89036a4a83142bd29eceea8d468` |
| MP4 SHA-256 | `182ef43ccf34f501dea4051312e71bf4d974a53dc6634cd98a5cbf3fae8ac130` |
| Original game soundtrack used | **None** |

**Independent capture-off vs capture-on CRC evidence:** Both complete guest WRAM CRC streams have SHA-256 `cfbdc874fea24dead879b8eb83b63376c8be1ad432ba8f2a1f99cfdb887d9b68`. The validator required the two original streams to be byte-identical, a successfully terminated recorder, exact guest IDs in chronological order, and 600 successfully decoded lossless frames. There were zero dropped, repeated or skipped recorded frame **IDs**.

**Guest versus host:** The FFV1 and MP4 use nominal 60-fps video time. Native IDs prove a consecutive presentation for each of the 600 observed guest frames; they do not independently establish wall-clock-perfect 60-Hz external scanout.

**Not a 4K capture.** The verified 3840×2160 witness from the earlier QA suite is a separate *single-frame* physical-output observation. This clip demonstrates the genuine 342×224 widened world, presented through a real 960×540 SDL window. It is not a demonstration of complete-event QA, Remastered HD art coverage, finished menus or Windows beta readiness.

## Reproduction and retention

The [native CI run](https://github.com/gamesbyian/UR-Recomp/actions/runs/38089655141) built the pinned Baldosa C guest/SDL host with an opt-in read-only recorder staged into a disposable checkout. It executed the exact same extended two-player route once with video disabled and once with video enabled, then compared full guest traces. The final executable and route identities are bound into [the manifest](native-continuous-provenance.json). The original lossless FFV1 recording, native logs, frame-index TSV, pinned route and output witnesses live in temporary CI artifact `ur-native-continuous-2p-one-shot-38089655141`, artifact ID **11683697184**. This artifact has a bounded 14-day retention; the clean MP4, poster and manifest are committed permanently.

The staging script `tools/showcase/stage_continuous_native_capture.py` is inert without three explicit capture variables and refuses unknown host source anchors. The validator `tools/showcase/validate_continuous_native_capture.py` fails closed on discontinuity, incomplete video or guest CRC differences.

The screenshot poster is a real frame decoded from the lossless native master, not an AI illustration. Inspect other frames, current wide-OBJ occlusion, and moving-scene HUD independently before using promotional claims about pixel-perfect parity.

Source provenance and reproducible technical evidence are established for this bounded clip. They do **not** change the project's official gameplay-fidelity or Windows beta-release status.
