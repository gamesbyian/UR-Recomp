# QA-08: three genuine moving single-player Windows PPU frames match original Snes9x

**Source-qualified experimental 1P raster result, 2026-10-15.** The actual
Windows executable from graphics draft #1641, already compiled in Actions
[38697704517](https://github.com/gamesbyian/UR-Recomp/actions/runs/38697704517),
generated three independent moving, logical **256×224 Original PPU frames**.
All three match independently booted Snes9x callbacks at **every pixel**
after the established Snes9x 6-bit-green → original RGB5 conversion.
This is real Windows game graphics evidence, *not* continuous game/event
acceptance or an endorsement of the authored Remastered racer identity.

## Immutable, independent sources

One original emulator plus one actual Windows executable completed separate
executions in [run 38701112952](https://github.com/gamesbyian/UR-Recomp/actions/runs/38701112952):

- Windows captured from **exact existing ROM-free executable SHA256**
  `7431889698913feadab76261caf3b00b82d1d9a1466a8260d9b7512d8328324e`,
  not another build, using the read-only `end_sim_frame` observer already
  in #1641. The genuine 1P route executed 5,447 frames. Artifact **11956707539**,
  downloaded archive SHA256 `2cc4643cdb8dc3d3b77d44f31646893eea8d070c593453ba40c5931e05fd0c57`.
- Independently compiled pinned original Snes9x/snesref, real USA ROM,
  same original action route, only removing `turbo on` for the Snes9x script.
  Original produced **65/65 distinct full BGRX callbacks 2176–2240**,
  with 26,657 changing source RGB pixels between window endpoints.
  Artifact **11956168307**, ZIP SHA256
  `9b6f32bd00b89e5fda72bb82ea9d535ebd90baf62a4600a2fb0fd598b4ee648d`.
- The Windows Git checkout uses **CRLF**, while the Ubuntu original route
  uses LF. Both are authenticated **literal encodings of the same source**:
  `d33bbe48bd6488d08688abb1ae58e2928941bb6319fd38f42553cf1d837ac699`
  (canonical LF) and
  `65567dd5629bc71d544d58a4ac31b51de6c0b382d070aaf06ec1a2be952a5cd1`
  (Windows CRLF). The compare gate allows only these two encodings, not
  changed buttons, timers, spacing, commands or other input normalization.

The first comparator run was red due to a **test's undefined constant**,
and its first corrected rerun exposed the LF/CRLF script-byte distinction
before attempting pixel comparison. Both were repaired without changing
either source capture. Rather than rebuild both emulators for each
pure-comparator patch, the CI workflow now runs its expensive source
producers **manual-only** and automatically compares the archived accepted
source artifacts when the comparator or its unit tests change.

## Independently executed result

[Offline archived-artifact recheck run 38702318119](https://github.com/gamesbyian/UR-Recomp/actions/runs/38702318119)
**passed**, with both expensive emulator jobs skipped, and a real
comparison artifact **11956318779**, downloaded ZIP SHA256
`cc1d4a37b75ed891504ab97d20c827b73ad7ca441cba4ee9fb5e7a2f13d6fc76`.
The checker compared all 57,344 RGB5 pixels from **every one of the
65 original callbacks** to **each** of the three Windows moving source frames.

| Actual Windows guest | Best original Snes9x callback | Wrong RGB5 pixels | Next best original wrong pixels |
| ---: | ---: | ---: | ---: |
| 2192 | 2191 | **0 / 57,344** | 23,039 |
| 2208 | 2207 | **0 / 57,344** | 20,855 |
| 2224 | 2223 | **0 / 57,344** | 16,449 |

All three actual original 1P source frames are different and correspond
to **different** Windows frames. No player/carriage/window region was
masked, cropped to 216 pixels, shifted or synthetically aligned.
The bounded result agrees with the previously source-verified three
moving 2P frames under this same candidate correction, where the original
2P brightness split had changed by 512 pixels per scene.

Complete source/result SHA and negative release assertions:
`analysis/data/qa08-actual-windows-original-moving-oneplayer-source-exact-20261015.json`.
Reproducer: `tools/qa08_compare_original_windows_oneplayer.py` and
`tests/unit/test_qa08_original_windows_oneplayer.py`, retrieving the
two archived producer artifacts with the read-only workflow at
`.github/workflows/qa08-original-windows-oneplayer.yml`.
Original Snes9x frame provenance remains independent of native host timing.
The zero error is exact **source framebuffer parity at three selected scene
registrations**; it does not prove guest CPU/camera/input phase throughout
an entire event.

## Remaining original graphics release gates

1. Source-verified original/native **1P and 2P race transitions**, finish,
   result panels and post-result return, including repeated moving frames.
2. Effective per-scanline BG/OBJ/OAM/HBlank/window ownership rather than
   source-alpha-only inspection, especially split-screen.
3. An actual source-pinned packaged Windows frame presentation audit at
   authentic **256×224, 7:6 PAR**, 4× Original, upscaled fallback, and the
   project's genuine extra-world widescreen materializer. A 216-high crop
   remains forbidden.
4. Human assessment of recognizably correct wheel/fork/saddle/rider silhouette,
   animation and gameplay-scale legibility. The old procedural 4× racer art
   remains **aesthetically rejected**, never implicitly approved by Original
   source parity.
5. Full original/native event gameplay acceptance, controller/display hardware
   and authoritative release ledger are separately owned and **unaccepted**.

**Release policy:** Neither this successful research PR nor #1641 may be
merged solely on bounded exact frames. No CPU/APU timing, input, persistence,
Modern UI, original gameplay logic or full source-rendering implementation
is modified by this research experiment. Agent 1 can consume the authentic
frame and CRC timestamps as evidence, while Agent 6 owns reconciliation
with the active Windows source path.
