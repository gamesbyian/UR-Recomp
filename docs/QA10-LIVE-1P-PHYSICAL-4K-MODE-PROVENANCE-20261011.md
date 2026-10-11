# QA-10: prevent 2P/texture substitution for genuine live 1P 4K

**Status:** read-only provenance follow-on to native physical 4K
[#1348](https://github.com/gamesbyian/UR-Recomp/pull/1348).
Exact native physical 1P output remains pending until that
separately running AOT produces and accepts its full screenshot.
This module does not rerender physical pixels, change the emulator,
approve character art or alter Modern output settings.

## Distinguish three independent concepts

At authentic native USA guest frame **2208**, the game can render
both 1P and 2P, with DIFFERENT full 342×224 original pixel data.
Earlier successfully accepted independent sources establish:

| Exact native source at guest2208 | Unmodified original RGBA SHA256 |
| --- | --- |
| **Live 1P 342×224 Original** | `8e81014ae6b7285b8d4a79985cc6ba146b309e913fc0e7e3cb8800730f3f0f05` |
| **Live 1P 4× Original 1368×896** | `b8257c7f94a4b97b343626f773be912b8967a9a1849ef3574fd8d755ef3bab7a` |
| **Genuine 2P 342×224 at same guest index** | `f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a` |

These are actual raw RGBA payload SHA256 digests, not
file-container/checksum-of-PAM-header values. Exact 1P
source/4× pixels were previously accepted with unchanged
whole-guest CRC and multiple source-image controls in AOT
[38115756178](https://github.com/gamesbyian/UR-Recomp/actions/runs/38115756178).
Independent 2P physical 4K at2208 has accepted SHA
`29f6ef1f9b5965d32818228182922e337a0570433b5929c89e285af2969a0fac`,
also **not** a valid 1P physical screenshot.

The existing
`tools/check_baldosa_physical_4k_capture.py`
already compares every one of **8,294,400 actual SDL2 physical
pixels** to the correct 1× Original source and its 4×
texture, including alpha, 7:6 PAR, viewport and real
software-SDL 16.16 nearest sampling. That pixel oracle
does not explicitly know whether the supplied same-frame
Original raster is **1P or 2P**. A trio of incorrectly
swapped 2P source/density/physical images could pass
a geometric pixel test.

## Independent strict mode/provenance binding

`tools/check_baldosa_1p_physical_4k_mode_binding.py`
is **only a follow-on** to the accepted native all-pixel
report. It requires:

- Exact successful Original all-pixel oracle report for
  guest2208; original **342×224**, source density
  **1368×896** and actual SDL drawable **3840×2160**,
  full 16:9 viewport, Original 7:6 PAR, whole 224
  logical height, opaque SDL output alpha and pinned
  SDL 16.16 nearest.
- Exact *previously accepted genuine live 1P*
  source and internal 4× SHA values. The independently
  accepted same-frame 2P source and physical 4K digest
  are explicitly not accepted.
- Exactly one actual native
  `UR_BALDOSA_PHYSICAL_4K_CAPTURE frame=2208
  output=3840x2160 source=SDL_RenderReadPixels status=saved`
  marker and one Original live-1P 4×
  `UR_BALDOSA_WS342_PRESENT` source screenshot marker.
- Exactly one `UR_BALDOSA_WS342_LIVE_MODE mode=1`
  transition **before** guest2208, from the same
  native physical capture log. A 2P/fixed screenshot
  masquerading as 1P is rejected.
- No native physical-SDL capture rejection and a
  well-formed distinct physical output digest.

The *parent* AOT workflow enforces full guest-CRC equality,
actual physical pixel identity and real 1P/density-source
recording. This follow-on deliberately does not claim
to replay those checks; it binds their already accepted
report to independently authenticated **1P mode and
image identity**, without a second expensive guest run.

When #1348 is native green and the report/log is present:

```sh
python3 tools/check_baldosa_1p_physical_4k_mode_binding.py \
  --physical-report native/baldosa-evidence/ws342_live_1p_physical_4k_frame2208.json \
  --native-log native/baldosa-evidence/race_1p_ur_ws342_live_physical_4k/log.txt \
  --out native/qa10-live-1p-physical-4k-mode.json
python3 -m unittest tests.unit.test_check_baldosa_1p_physical_4k_mode_binding
```

Thirteen adversarial synthetic regressions reject a fake 2P
source/physical output, same-size but wrong source/4×
density, omitted SDL readback, repeated capture markers,
missing/wrong 1P mode, wrong frame/centered viewport,
malformed SHA, and native rejection warnings.

## Non-claims

Even if both parent pixel oracle and this mode identity
checker pass, the conclusion remains bounded to the
**exact pinned 1P native SDL software guest2208**.
It does not validate hardware GPU behaviour,
user-controlled display-mode changes, physical monitor
resolution or refresh, character-likeness approval,
widescreen renderer completeness, game/release quality,
or future Remastered sprite composition. Retain the
original PPU fallback and separate independent QA
release authority.
