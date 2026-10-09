# QA-08: Native moving Racer HD availability and temporal coherence

Status: **instrumented native evidence path, not a release gate pass**.

## Why the retained reference census is insufficient

The reference 2P trace in
`analysis/generated/racer-hd-pair-temporal-eligibility-2026-10-08.json`
has 2,641 consecutive guest frames and 5,282 racer player-frame slots.
The default both-player gate permits at most **170 guest frames** (340
player-frames, 6.44%). These are 49 short registration-eligible bursts,
20 of them exactly one frame. A 759-frame and 661-frame interval have no
eligible pair at all. The independent selector tally (1,380/5,282,
26.13%) **does not** equal the renderer's actual coverage.

Each nominally eligible frame can still fail at logical width, OAM size,
split-small-sprite visibility, priority, asset or PPU capture. The previous
`UR_RACER_HD_DRAW PASS` log was limited to the first 32 changes of
registration identity, and may miss repeated renders or entire stretches
of fallback. It cannot provide an actual moving-scene denominator.

## New production read-only diagnostic

Set `UR_RACER_HD=1 UR_RACER_HD_CENSUS=1` for a fixed 256×224 native 2P
race. The diagnostic is opt-in, writes **only to stderr**, and never
changes WRAM, OAM, guest timing, course state or art policy. It records:

- `phase=gate` **once per simulated guest frame**. Status
  `original` includes a reason such as
  `unsupported-geometry`, `p1-selection-or-art`,
  `p2-pair-gate`, `missing-oam-placement`,
  `oam-size-mismatch`, `full-pair-split-obj`, or
  `ppu-capture-failed`. Status `armed` records a
  successful PPU RemoveFromGame admission and whether it intends
  `full-pair` or diagnostic `p1-only` replacement.
- `phase=present` for each actual host draw callback. Status `hd`
  confirms the renderer wrote an authored replacement. Status
  `original` records an unarmed Original fallback or an output refusal.

A gate that was **armed** but later presents `original` is an error,
not a successful fail-closed fallback: stock OBJ pixels may have been
removed already. The analyzer refuses to report a successful census for
this combination. Similarly, it rejects mismatched gate/render mode,
duplicate guest-frame gates, impossible statuses, and mixed HD/Original
outputs of one guest frame.

## Measurement command and interpretation

```sh
python3 tools/measure_racer_hd_live_draws.py path/to/native-HD.log \
  --json-out path/to/live-hd-census.json
```

`hd_presented_fraction` counts guest frames that actually received an HD
present among guest frames with a host present. `hd_player_frame_fraction`
uses **two players per presented guest frame** and counts a full-pair
render as two HD players, but a diagnostic P1-only render as just one.
The report also records actual Original frames and fallback reasons,
present-call duplication, unpresented guest frames, continuous HD runs,
one-frame HD bursts and Original-to-HD/HD-to-Original transitions at
*consecutive observed* guest frames only. It does not bridge dropped
or unobserved frames.

The native Racer HD acceptance workflow enables this diagnostic on its
existing ordinary-2P HD route and retains the JSON alongside native logs
and original versus HD screenshots. It requires both genuinely rendered
HD frames and genuine fallback frames. Quantitative results should always
name exact candidate SHA, ROM, route, sampled frame window, graphics
mode, logical width and host output density. Never compare a 441-frame
native sample against the 2,641-frame reference denominator as though
they were the same observation campaign.

## What this still cannot prove

- A successful `hd` callback **does not** establish correct occlusion
  against BG1/BG2 foregrounds, other OBJ, color math, HUD or ghost
  overlays. The pinned SNESRecomp
  `docs/HOST_OVERLAY_EXTRACTION.md` says foreground occluders need
  priority-aware planes or an intermediate composition seam.
- The fixed 256×224 renderer **rejects the 342×224 widescreen view**.
  Its correct full-frame Original fallback proves safety of the wide
  composition but gives no widescreen HD coverage. Test 1P, 2P and VS
  independently. Do not silently count a 16:9 Original scene as HD.
- A switching count is a risk indicator, **not observed human-visible
  flicker**. Verify output pixels and motion at 1× and 4×, abrupt camera
  reversals, Y-wrap, sprite crossings, split seams, fullscreen resizes,
  and course vertical transitions.
- An authoritative original-rendered reference or fresh native same-frame
  stock comparison must establish foreground depth and sprite ordering
  before QA-08 reaches L4. Hardware and real-player acceptance remain L5.

This work owns graphics diagnostics only. It does not change gameplay,
controller input, profile saves, tournaments, frontend, audio, package
policy or CI scheduling.
