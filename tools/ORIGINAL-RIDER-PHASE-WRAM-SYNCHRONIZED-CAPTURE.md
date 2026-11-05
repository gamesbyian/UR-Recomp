# ART-4K: bounded original rider-phase/angle write trace at synchronized graphics composition

**Purpose:** acquire authentic original *executed* rider presentation-state values, keeping their exact CPU call order and pre/post tile-DMA composition relationship. This is a small optional extension of the existing [synchronized original Mesen capture](../.github/workflows/racer-composition-mesen.yml); it creates **no scheduled workflows**, captures no new 3D mesh, and does not change Uniracers gameplay or shipping artwork.

## Previous evidence and why a new trace is warranted

The canonical original USA retail ROM SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478` contains directly byte-verified instructions that wrap a shared `$0F83` rider-phase state modulo **24** and a shared `$0F49` angle index modulo **64** ([#3105](https://github.com/gamesbyian/UR-Recomp/pull/3105)). The game indexes a rider presentation lookup with `phase*64 + offset`. These are **discrete state indices**, with no established 1994 3D degree/angle measurement.

Original no-frame-skip Mesen capture [#3103](https://github.com/gamesbyian/UR-Recomp/pull/3103) preserves authentic **1601–1624** adjacent tick OAM/VRAM/CGRAM/P6 observations, showing source-alpha and interior colour-index changes across **all 23 edges** for both player sprites. That PPU archive contains **no original game WRAM animation-state samples**. The experimental 2026 GLB controls in #3101 used illustrative +24°/tick, but are unsupported as original angle history.

The separately executed [synchronized original composer workflow run #41765654302](https://github.com/gamesbyian/UR-Recomp/actions/runs/41765654302), at source bridge frame **1218**, successfully stopped at source CPU PCs **`83:F129`** and **`83:F292`** and matched every one of **25/25** actual source graphics queue entries and destinations. All 25 effective destinations lie within the red/blue original held-OBJ VRAM ranges (12 / 13). Its original execution receipt has been pinned into #3105. This proves that the existing Mesen bridge's **execution breakpoints and WRAM memory reads work**. A new emulator, broad CPU trace or arbitrary 3D experiment is unnecessary.

## Scope of this optional workflow extension

`tools/capture_racer_composition_mesen.py` still defaults to **`--advance-frames 1218`** and the same existing original F129/F292 breakpoint and 25/25 queue validation. It now also saves before/after state words from the already-held `0x0000–0x17FF` WRAM snapshot. The new opt-in `--trace-rider-state` flag observes writes to seven specifically predeclared 2-byte original WRAM regions; the normal run remains watch-free:

| Original WRAM address | Why observe it |
|---|---|
| `0F83` | Shared 24-state rider graphics/wheel presentation phase |
| `0F49` | Shared 64-value current rider angle index |
| `0F97` | Shared working rider presentation ID |
| `0FE9` and `0FEB` | Persistent player-1/player-2 presentation IDs |
| `04C7` and `04C9` | Persistent player-1/player-2 pitch indices |

Additional pre/post 16-bit snapshots include `0F77` lookup offset, signed `0F8F` spin speed, signed `0F69` motion state, DMA selector `0300`, DMA pending `0306` and phase selector `12EB`. A raw signed 16-bit source value is decoded as an integer, with no conversion to degrees.

The existing `watch.create` / `watch.list` / `watch.delete` bridge methods record the **source byte address, source value, original executed bridge frame, CPU program-counter bank/address and cycle/clock** of each write. The trace has no writes to original ROM or WRAM and stops if the bridge's 2048-event ring could be truncated, or callback metadata is malformed. The source console is held at each breakpoint before reading each WRAM snapshot. Events at F129 and F292 are recorded separately and are not silently conflated.

**Important attribution rule:** working `0F83/0F49/0F97` values are **shared CPU scratch state**, not permanently assigned to player 1. Identify which player is current from contemporaneous player ID transitions and the ordered actual PC/write events before using any value as a pose label. End-of-frame sampled state alone is insufficient, and **every source PC event must be observed at runtime**, not inferred solely from the existing disassembly.

## Bounded manual execution and comparison

The already-existing `racer-composition-mesen.yml` accepts optional `workflow_dispatch` inputs `advance_frames` (0..2500, default 1218) and `trace_rider_state` (default false); the original normal proof remains unchanged if neither is supplied. For an experimental **original bridge transition around tick 1602→1603**, dispatch **one** manual capture at advance 1602 with the opt-in trace, against pinned main or an exact qualified PR branch:

```sh
gh workflow run racer-composition-mesen.yml \
  -R gamesbyian/UR-Recomp --ref <verified-ref> \
  -f advance_frames=1602 -f trace_rider_state=true
```

The capture tool's frame counter at the F129/F292 breakpoints counts the **previous completed frames**, so the selected 1602 advance means an upcoming original execution overlapping the separately archived PPU source around tick1603. Do **not** assert one-to-one phase-to-pixel alignment until exact bridge/frame marker semantics and PPU overlap checks confirm it. Use original input fixture `tests/input/two-player-first-race.input` and exact original ROM SHA. The workflow still uses the single pinned MesenCE build, original input replay, no external writes and the same synchronous mask/queue agreement gate. Existing artifacts expire quickly, so preserve meaningful source evidence with exact SHA before expiry.

**Decision rule:** first obtain actual source phase/angle/ID write chronology and match a synchronized per-player graphics transfer against the already observed changing original 2D source. Only then should the single experimental five-parent 2026 GLB be tested against **actual source frame-state transitions** under a fixed camera and identical material/geometry. If shared-player attribution, callback timing or the original source-to-2D frame alignment cannot be established, label it **unresolved**; do not guess missing angles, fit a per-frame camera or generate a new unapproved mesh. No owner-approved 4K likeness, shipping art, prospective 1994 3D pose source or Windows release credit follows.

## Qualification

The optional state-extraction, signed decoding, callback normalization and default/manual workflow contract are checked by `tests/unit/test_original_rider_phase_trace_capture.py` (four small ROM-free tests). The actual one-shot Mesen job must independently pass its existing 25/25 source queue/mask checks and a source-level review before merging the instrumentation. The captured observation itself is not present merely because source code was committed.

## Actual original CPU writer/producer execution (November 4, 2026)

The previously unexecuted optional research trace has now been **observed in the original source-built Mesen**, in one bounded PR-only qualification run [#41943233739](https://github.com/gamesbyian/UR-Recomp/actions/runs/41943233739). Actual original emulator [artifact #13378090515](https://github.com/gamesbyian/UR-Recomp/actions/runs/41943233739/artifacts/13378090515) ZIP SHA256 `8f57c2bdbf0f7d12c7df592a9b209b0b6b065d011af21636f041f56c90ebc09a`, original runtime JSON SHA256 `b361c2aec1779a0d88d6db80686169c71b7d039b28fa998b361596315a3e5809`, are summarized without ROM pixels at `analysis/data/racer-original-synchronized-phase-composer-1602-20261104.json`. This is an executed source witness, not merely synthetic CI.

The *same original Mesen bridge frame 1602* stopped at CPU `83:F129` and `83:F292`, preserving 32 bounded selected WRAM write callback events by the former stop and the same 32 by the latter. Fourteen original CPU program-counter locations appeared across those watched fields. Both stopped raw WRAM snapshots showed **shared phase 11, shared orientation 60, selected graphics ID 764**, exactly `64×11+60`, with persistent P1 ID 441, P2 ID 764, signed wheel speed 3 and shared motion 8. The current selected graphics ID equalled P2's persistent ID at that execution point, not a universal P2-only workspace contract. The original synchronized composer independently matched **28/28 occupied staging destination/source pairs**, plus both 5-row source mask categories, at that frame. This meaningfully strengthens producer-boundary timing evidence beyond post-PPU sampling. The two stopped snapshots were unchanged for these selected words, but exact writer-to-held-P6 scanout phase still is **not** independently aligned.

**Repository CI policy:** the temporary path-scoped PR trigger used for this one original no-skip proof was explicitly removed after successful execution. The existing synchronized Mesen workflow is manual-only again (default frame advance1218 and writer trace OFF) to satisfy the repository's no-dormant-research-trigger rule; the derived original evidence is pinned and does not require further reruns. No extra emulator, workflow file, art geometry or physical 1994 degree mapping was added. Source/owner art and Windows ART release acceptance are unchanged.
