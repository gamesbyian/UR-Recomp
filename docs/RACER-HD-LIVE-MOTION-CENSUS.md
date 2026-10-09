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

## First exact moving native census (2026-10-09)

The original full-process native acceptance artifact is retained and
hash-bound in
[`analysis/generated/racer-hd-native-live-race-window-2026-10-09.json`](../analysis/generated/racer-hd-native-live-race-window-2026-10-09.json).
Workflow `37871889030`, artifact `11591057403`, candidate
`6f6076f7fd3857f24efb54cdeaf37732ac346f35`, HD log
SHA256 `091a42e815e4d94e4140052c9145f73e7800a36f2bfef5492a2497f7e83aeab3`.

The native process reported **103/1,620** HD-presented guest frames,
but that fraction includes loading and setup. The **actual race-observation
window, guest frames 1180–1620**, contains:

| Exact live native 2P measurement | Result |
| --- | ---: |
| Guest frames with a host present | **441/441** |
| Real full-pair HD presentations | **87** (19.73%) |
| Real Original presentations | **354** (80.27%) |
| HD motion runs / one-frame runs | **16 / 5** |
| Original→HD / HD→Original edges | **16 / 16** |
| Longest HD run | 16 frames |
| Longest uninterrupted Original span | 150 frames, `1471–1620` |
| Original fallback reasons | P1 composition/art 342; P2 pair gate 12 |
| Capture armed but no HD draw | **0** in this route |

The contiguous `1205–1220` shipping-art strip is **16/16 genuinely
HD-drawn frames**, and `1261–1267` is **7/7**, but the remaining
moving race is mostly Original. This is a measured *draw availability*
result, not just semantic selection. Fast alternation remains a
visual-coherence concern: 32 genuine HD/Original callback switches
during those 441 consecutive frames, with five one-frame HD bursts.
These edges are a strong candidate for a visible resolution pop but
must still be checked using aligned moving screenshots.

**Non-interchangeable inputs:** this 441-frame *native* census uses
`tests/input/two-player-first-race.input` and
`tests/input/two-player-first-race-observe.script`. The older
2,641-frame *Snes9x* reference census uses
`tests/input/two-player-p1-win.input`. Do not describe the two
percentages as if they sample the same full route. The native P1-only
acceptance already executes that longer reference input and now
retains its own 1180–3820 native actual-draw census separately.

The workflow additionally runs a native **full-density** frame-1220
stock/HD confinement check: two independent Original captures must
match exactly, and all HD changes must stay inside the four actual
OAM bounding footprints. This is one explicit compositing check,
not foreground-occlusion correctness.

## Native 2,641-frame P1-only comparison, same input fixture

The previously proposed long native comparator now has accepted exact
native PPU/host evidence. Run `37873082202` / artifact
`11591785951`, using `two-player-p1-win.input` and
`UR_RACER_HD_P1_ONLY=1`, produced **169 full-pair HD frames**,
**902 HD-P1/stock-P2 frames**, and **1,570 all-Original frames**.
Every guest frame 1180–3820 was presented, zero armed captures missed
their HD draw, and actual HD player-frame coverage is
**1,240/5,282 = 23.48%**. Frame-level *any-HD* availability
is 1,071/2,641 = 40.55%, a different statistic. The production
default remains pair-only (169/2,641 both-HD native frames in this
same run).

The diagnostic also produces 179 HD episodes, 24 one-frame episodes
and **358 actual HD/Original switches**, which require meaningful
moving-scene visual review before P1-only is ever player-facing.
The existing original-stock P2 pixel preservation acceptance passed
but independent foreground BG priority is still open.

The Snes9x reference and native host use the **same input file** but
are *not frame-exact state-aligned*. The nominal Snes9x figures
170 full-pair selected and 984 P1-only candidates cannot be
subtracted from native 169/902 as a 1-frame/82-frame capture
failure count. Native and reference disagree about **59 native
pair-draw omissions and 58 native pair-draw additions at identical
absolute guest-frame IDs**. Compare event-relative WRAM composition
to qualify differences. See
[`RACER-HD-PAIR-GATE-COVERAGE.md`](RACER-HD-PAIR-GATE-COVERAGE.md)
and the hash-bound
[`racer-hd-p1-only-native-coverage-2026-10-09.json`](../analysis/generated/racer-hd-p1-only-native-coverage-2026-10-09.json).

## 1P and VS actual native moving-scene census

The same graphics-only native acceptance now exercises two pre-existing
ROM-authoritative entry routes with `UR_RACER_HD=1
UR_RACER_HD_CENSUS=1`, without memory pokes or guest-state injection:

- **1P:** `tests/input/qa08-one-player-racer-motion.script`
  follows the proven first-race menu route, waits for active race
  `7E:0313 == 01`, then drives right and samples the final 120
  consecutive host-presented guest frames.
- **VS:** `tests/input/vs-first-race.input` and
  `tests/input/qa08-vs-racer-motion.script` wait for the
  actual active-race byte and take the final 120 consecutive host
  presentations after a moving interval.

`tools/measure_racer_hd_scene_tail.py` uses the existing gate+present
witnesses but analyzes **only those bounded race tails**. It refuses
missing guest frames, missing host presents, an armed capture that
fell through to stock, inconsistent 1P/VS trace states and duplicate
gate entries. The HD count is allowed to be zero: the current 2P
split-OBJ presenter may appropriately reject a 1P or VS frame and
preserve Original, but the test must observe that honestly.
Results and original logs are retained separately as
`racer-hd-one-player-scene-tail.json` and
`racer-hd-vs-scene-tail.json`.

These are **scene-specific admission/fallback safety measurements**,
not 1P/VS original pixel parity, widescreen HD coverage, or complete
mode visuals. Passing the probes never promotes QA-08 to L4.
Native same-frame screenshot and foreground-depth comparisons still
need to be expanded to these modes.

## Accepted 1P and VS native results

The newly accepted [PR #1022](https://github.com/gamesbyian/UR-Recomp/pull/1022)
captured the actual native 120-guest-frame tails after each mode's
ROM-gated active-race entry. Native graphics workflow `37875965496`,
artifact `11592851071`, candidate
`c52c2a6f581cb159a31c7e2c84a464b11922ec2a`.
Source JSON hashes, exact windows, fixture names and quality limitations
are retained in
[`analysis/generated/racer-hd-native-1p-vs-tail-2026-10-09.json`](../analysis/generated/racer-hd-native-1p-vs-tail-2026-10-09.json).

| Native first-race guest-frame tail | One-player | VS |
| --- | ---: | ---: |
| Actual full-pair HD host draws | **42/120 (35.0%)** | **39/120 (32.5%)** |
| Actual Original fallback draws | 78/120 (65.0%) | 81/120 (67.5%) |
| HD runs | 7 | 9 |
| One-frame HD bursts | 0 | 1 |
| HD↔Original mode switches | **14** | **16** |
| Missing host presents | 0 | 0 |
| Capture armed but HD never drawn | **0** | **0** |
| Last 120 guest frames | 1068–1187 | 1235–1354 |

All Original fallback frames in these tails were attributed to the
P1 selection/art gate. There were real full-pair HD presenter returns
in both modes, but **successful draws do not prove authentic
composition or racer identity**. Neither mode has a same-frame
Original-vs-HD raster priority witness, nor demonstrated complete
4:3/16:9 composition, moving camera/occlusion behavior or HD coverage
over an entire race.

The separate ordinary-2P 441-frame and 2,641-frame reference routes
are **different observations** and must keep their own denominators.
In particular, do not average these scene rates or promote QA-08 to
a passed release gate based on bounded admissions.

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
