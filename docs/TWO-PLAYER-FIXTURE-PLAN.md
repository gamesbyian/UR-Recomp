# Two-Player Fixture Capability Plan

Status: deterministic VS and ordinary-2P routes are both reproduced. Ordinary 2P is promoted to a durable two-controller fixture with isolated P1-only, P2-only and simultaneous movement checkpoints plus the active-display OAM seam. The former frame-1532 one-unit X-speed seam is resolved as an absolute host-frame anchoring artifact: native, Snes9x and Beetle cut the common race-entry transition on adjacent frame boundaries, while race-relative scheduler and racer semantics align.

## Why this exists

The project has an established engine-neutral player-2 controller transport plus deterministic VS and ordinary-2P routes from clean boot into active split-screen gameplay. `TWO_PLAYER_SELECT = 0x3D`, `VS_SELECT = 0x3E`, two-controller rider selection, deeper setup states, first race entry, paired racer-state assertions, simultaneous input, and the active-display OAM seam now have local evidence. Remaining work is full Mesen runtime promotion, richer split-screen/HUD interaction coverage, multiplayer camera/object activation, and downstream widescreen validation. Do not reopen the closed frame-1532 arithmetic/timing seam unless an event-relative fixture produces a semantic mismatch.

The former frontend reachability blockers are now covered by frozen routes. Remaining promotion work is no longer basic reachability: it is cross-runtime breadth and deeper behavior, especially Mesen execution, split-screen/HUD interaction, multiplayer camera/object activation, and eventual widescreen validation.

This is a tooling dependency, not permission to neglect multiplayer work.

## Known compatibility motivation

Two-player coverage is also an emulator/hardware-fidelity seam, not merely a menu-completeness concern.

A historical MiSTer SNES issue specifically reports a Uniracers 2P/VS problem where the second player's unicycle is vertically displaced/hovering in split-screen play:

https://github.com/MiSTer-devel/SNES_MiSTer/issues/26

The project already tracks broader Uniracers OAM/rendering compatibility history. Shared player-2 input now exists, so the behavioral acceptance route must include a deterministic split-screen framebuffer/OAM checkpoint; a one-player-perfect runtime must not silently retain a player-2-only rendering defect.

## Required capability

The shared neutral controller stream is now the authoritative transport:

```text
start:duration:p1-mask[:p2-mask]
```

The three-field form remains P1-only. The optional fourth field is an independent P2 mask using the same 12-bit SNES layout. Same-player intervals may not overlap; cross-player overlap is allowed so simultaneous input is representable.

Do not add a competing `p2 press ...` dialect to the scene-keyed `.script` grammar merely to unblock the atlas. Keep the neutral stream as the cross-engine controller artifact. State-aware tooling may decide when to emit/freeze that stream and when to record named checkpoints, but it must preserve the shared transport semantics.

## Integration with dual-controller transport PR #31

PR #31 has merged the transport layer this plan was waiting for rather than a competing scene-script grammar.

Its neutral stream format is:

```text
start:duration:p1-mask[:p2-mask]
```

The three-field form remains P1-only. The optional fourth field is an independent P2 mask using the same 12-bit SNES layout. The same stream is wired through native Lua replay, patched `snesref`, and Mesen.

Keep the layers separate by responsibility:

```text
scene-keyed .script fixture
    -> waits on menu/runtime state
    -> names dump checkpoints
    -> useful for P1-only navigation and observation

neutral .input stream
    -> exact per-frame controller transport
    -> independent P1/P2 masks
    -> shared across native, snesref and Mesen
```

Do not invent `p2 press ...` syntax in the existing scene grammar merely to unblock the atlas. For 2P/VS atlas work, either generate/freeze the neutral controller stream from a small state-aware driver or extend the shared runner so scene checkpoints can be synchronized with that stream without changing its controller semantics.

The durable ordinary-2P corpus is now `tests/input/two-player-first-race.input`, paired with `tests/input/two-player-first-race-observe.script`; it proves two-controller selection, the next setup states, race entry, isolated per-player movement, simultaneous movement, and stable split-screen checkpoints.

## Acceptance fixture

The first acceptance test should be intentionally tiny and UI-driven:

```text
MAIN_MENU
 -> choose 2P
 -> TWO_PLAYER_SELECT
 -> P1 confirms a rider
 -> P2 visibly becomes the active selector
 -> P2 confirms a rider
 -> reach the next multiplayer setup state
```

Capture at minimum:

- framebuffer;
- `7E:009F currentMenu`;
- `7E:009B selectedOption`;
- `7E:000E menuSelectedRow`;
- `7E:0C63 menuSelectedCol`;
- recovered `playerInput` field where applicable.

The recovered bot places `playerInput` at `0x70:0743`, with historical values `5=P1`, `3=P2`, `1=both`, and gates menu input using `playerInput == 7 - controller * 2`. This bank maps into the dumped SRAM surface, not the ordinary `7E` WRAM fields. A harvested native VS route now gives a local raw discriminator at physical SRAM offset `0x0743`: `0x04` while the screen says PICK PLAYER ONE, then `0x02` after P1 confirms and the screen says PICK PLAYER TWO. A subsequent P1 X leaves both the P2 screen and raw byte unchanged. The numeric mismatch against the historical 5/3/1 comment is intentionally unresolved; retain both observations until the mapping/emulator semantic is explained.

`tools/build_ui_atlas.py` therefore supports SRAM-backed field specs and the capture manifest exposes this byte as `participant_owner_raw`. The reset-free `ui-vs-handoff` probe makes `0x3E + owner raw 0x04/0x02` a regression target without pretending the old labels and raw dump are already reconciled.

Then add the corresponding VS acceptance route through `VS_SELECT -> VS_CHALLENGER -> VS_CHALLENGE_TRACK`.

## Promotion gates

Current promotion-gate status:

- [x] a two-player route produces stable named checkpoints;
- [x] controller assignment is behaviorally proven rather than inferred from a similar frame;
- [x] simultaneous P1/P2 input is covered by a small semantics test;
- [x] `tests/fixtures.json` contains a durable ordinary-2P fixture;
- [x] `analysis/ui-state-map.yml` reflects the reproduced ordinary-2P handoff;
- [x] native and Snes9x share the neutral input stream plus named checkpoint schedule;
- [x] the Mesen adapter can synchronize that same neutral stream with named checkpoint scripts, with ROM-free two-pad timing coverage;
- [ ] run the promoted ordinary-2P fixture against a compatible Mesen/MesenCE binary and compare the named semantic checkpoints;
- [x] `analysis/ui-menu-index.json` now points `0x3D` at the durable ordinary-2P fixture and promotes two-player `0x91` from historical to verified;
- [ ] harvest any richer framebuffer/HUD atlas evidence that materially benefits from the promoted route.

## Multiplayer camera / viewport observability

The promoted ordinary-2P fixture now exposes the recovered dual-camera and split-screen projection state through `tools/summarize_paired_player_slots.py`.

Recovered multiplayer mode/culling state:

- `$0DDB`: raw split-screen/multiplayer camera-path enable. It is set from the setup flag at `83:C9C0..C9C6` and gates camera-2 updates, dual-window course sampling, split-screen OAM/HDMA setup, and alternate race paths;
- `$121B/$121D`: per-racer off-screen flags used alongside the screen-relative OAM staging.

Recovered camera state:

- camera 1 position: `$0419/$041D`;
- camera 2 position: `$041B/$041F`;
- camera 1 velocity: `$04F5/$04F9`;
- camera 2 velocity: `$04F7/$04FB`.

The bank-81 camera-control structural island confirms these are active per-frame state, not duplicate annotations. `81:A52F` updates camera 1 from `$04F5/$04F9`; when `$0DDB != 0`, the same wrapper updates camera 2 from `$04F7/$04FB`.

Recovered split-screen/OAM staging:

- screen-2 racer coordinates: `$1501/$1502` and `$1505/$1506`;
- screen-1 racer coordinates: `$1509/$150A` and `$150D/$150E`;
- raw visibility/culling bits: `$1599`.

Bank 82 computes these bytes from racer positions and camera state, substitutes off-screen sentinel coordinates on rejection paths, updates visibility bits in `$1599`, and then `82:D2D8..` streams `$1501..$1510` directly to OAMDATA. This is therefore a concrete camera → screen-relative projection/culling → sprite-emission bridge.

Run 79 supplies the first event-relative camera evidence from the promoted fixture. At the 1470 baseline both cameras sit at X=984 with zero X velocity. After the P1-only interval, both runtimes report camera 1 at X=1455 with positive velocity 15 while camera 2 remains at X=984 with zero velocity. During the following P2-only interval, camera 2 begins following the second racer (native X=1082/vx=11; Snes9x X=1089/vx=10). During simultaneous P1-right/P2-left input, camera 2 reverses left in both runtimes while camera 1 continues right.

The same fixture exposes the split-screen culling sentinels produced by bank 82. Once P1 has pulled away, screen 1 represents P2 as `0x70/0x70` and screen 2 represents P1 as `0x30/0x30`, matching the recovered off-screen branches that write those exact coordinate pairs.

These relationships are durable event-relative assertions in the ordinary-2P workflow. They deliberately assert ownership/direction/culling behavior rather than exact post-input cross-runtime coordinates: the closed frame-origin investigation already proved that libretro cores and the native host can cut a vblank-shaped transition on adjacent absolute frame ordinals.

The same camera-control path also exposes raw world-window state used before render-update construction: `$0505/$0507` are per-camera movement-derived edge values, `$052B/$052D` are associated update spans, and `$0509/$050B` are fine/index components. Immediately before DMA/update descriptors are built, `81:AA40..AB87` filters two compact 16-entry structures against those moving edge bands. Their counts are `$0DCD/$0DCF`, byte flags `$0D6D/$0D7D`, and encoded coordinate words `$0D8D/$0DAD`. Bank 82 consumes them as VRAM update commands at `82:D383..D3C4`: encoded words become `$2116` VRAM addresses and flag-selected values are written through `$2118`.

This explicitly **does not close gameplay object activation**. The recovered RAM notes currently provide only racer collision-state hints (`$0E95`, `$0F09`) and no authoritative object-enable table. Keep the remaining object-activation obligation separate: trace entity/object state from the bank-81 object/collision dispatcher or from a fixture where a world object enters/leaves the active region, rather than reusing these render-side VRAM lists.

## Downstream obligations

With the grammar now available, implement and verify:

1. [x] P2-only causality/confirmation in the initial ordinary-2P route;
2. [x] VS challenger and challenge-track reachability after P2 confirm;
3. [x] first ordinary-2P race entry;
4. [ ] richer split-screen/HUD atlas states;
5. [x] two-player OAM compatibility coverage for the canonical scanline split and high-OAM routing;
6. [x] native/Snes9x deterministic multiplayer checkpoints, with exact stable pre-intervention parity and bounded post-input drift;
7. [ ] promoted Mesen/MesenCE runtime parity using the synchronized neutral-stream + named-checkpoint adapter;
8. [ ] two-player effects on camera, object activation, and later widescreen behavior.

Do not allow completion of general fidelity work to imply multiplayer fidelity if these items remain open.

## Ownership / scheduling rule

Any agent modifying the shared fixture grammar, native scripted-input harness, `snesref` input adapter, Mesen fixture adapter, or multiplayer UI code should check this plan and either advance this capability or explicitly preserve its requirements.

Conversely, UI-atlas work should continue on single-controller-reachable states while behavioral multiplayer verification remains open rather than waiting idle.


## Ordinary 2P route result

The first bounded ordinary-2P probe succeeded without a search sweep. Reusing the verified VS two-pad timing while changing only the Main Menu selection from VS to 2P reaches:

- `0x3D` ordinary two-player rider selection at frames 560 and 640;
- `0x6D` at frame 720;
- `0x91` at frame 820;
- `0x16` at frame 920;
- transition state by frames 1020/1120;
- stable `inRace=1`, `currentMenu=0x00` by frame 1220 and thereafter.

Evidence run: `36817685308`.

The promoted fixture is `tests/input/two-player-first-race.input` with `tests/input/two-player-first-race-observe.script`. Run 36819833356 confirms the isolated Snes9x semantics: P1-only Right moves slot1 while slot2 remains at baseline; P2-only input then moves slot2; simultaneous input leaves P1 with positive X velocity and P2 with negative X velocity. The same run reproduces the canonical active-display OAM seam, HDMA `$2104` writes `V=0->$A5` and `V=112->$5A`, at every sampled stable race checkpoint. The disposable probe and its guessed offsets were removed after promotion; canonical racer fields come only from `tools/summarize_paired_player_slots.py`.

## Resolved native/reference P2 timing seam

The ordinary-2P fixture now localizes the remaining native/Snes9x kinematic disagreement to the P2-only movement window rather than route timing or controller ownership.

Run `36821645246` uses a common one-frame observation schedule from frames 1528 through 1554. P2 Left begins at guest frame 1530.

- 1528-1531: tracked state matches.
- 1532: first difference, only `Player2_XSpeed`: native `-47`, Snes9x `-48`.
- 1533-1535: tracked state reconverges.
- 1536: P2 X differs by one and the candidate P2 camera-X speed differs by one.
- 1538-1544: tracked state reconverges again.
- 1545: P2 Y differs by one.
- 1548: X speed differs by one again.
- 1550: the small drift crosses a contact threshold: native has `vy=19, air=1` while Snes9x remains `vy=0, air=0`.
- 1551-1552: the one-frame contact difference amplifies into materially different X position/speed, rotation and camera speed.

The controller-snapshot bytes remain equal at the first velocity divergence, so the earlier hypothesis that native's no-multitap live `$4218-$421B` behavior was exposing the P2 input edge early is not supported by this trace. The game-side race path consumes P2 from the NMI-copied `$030E/$0310` word and decodes horizontal direction into `$0317`; future diagnostics should therefore start after that decode, in the shared racer working block.

The USA race-update routine copies P2 persistent X speed `$04B9` into shared working X speed `$0F9F`, processes the common racer physics path, then copies `$0F9F` back to `$04B9`. The trace now includes decoded P2 horizontal direction and the shared working speed/rotation fields.

Run `36822486597` originally appeared to make the seam direction-specific, but retained artifact inspection later showed that sequential native launches were sharing persisted generated-host SRAM. That made the directional matrix non-repeatable before intervention and invalidated the leftward-only interpretation.

The clean-SRAM rerun `36827520546` now deletes the generated native save directory before every native oracle launch and gates full WRAM plus full SRAM identity at frames 1528-1529 across every generated variant. Under that controlled state:

- P1 Left: first difference at frame 1532, X speed only, native `-48` vs Snes9x `-47`;
- P1 Right: first difference at frame 1532, X speed only, native `+48` vs Snes9x `+47`;
- P2 Right: first difference at frame 1532, X speed only, native `+47` vs Snes9x `+48`;
- canonical P2 Left remains first-different at frame 1532, with persistent and shared working X speed native `-47` vs Snes9x `-48`.

This rules out player-slot routing, input direction, and persisted fixture state as the primary cause. The earliest seam is a **one-unit small-speed update difference** in the common racer physics path. Its polarity changes with the exact incoming state rather than with a single controller or direction.

The recovered bank-82 code narrows the relevant update to `82:A5F3..A617`, which nudges a small nonzero shared working X speed `$0F9F` one unit toward zero when its neutral-angle conditions hold. It is reached from the alternating P1/P2 update paths; the scheduler phase fields therefore remain relevant, but the clean rerun shows the effect is not a stale-save artifact. The left helper at `82:AA09` is no longer the leading arithmetic suspect.

A disposable trace-enabled writer workflow was attempted and retired because its generated trace target hits an unrelated unresolved `80:C3C8 -> 00:FFFF` dispatch at frame 445, before multiplayer. The generic trace client retains the useful bounded `--continue-until` option, but repairing trace-target generation is not a prerequisite for this lane.

Static control-flow recovery now explains the frame-1532 discriminator more tightly. The two racer update paths gate the same `82:A5F3` small-speed nudge on opposite values of scheduler byte `$0302`:

- P1 path `82:8C3B..8C4F`: call `A5F3` only when `$0302 != 0`;
- P2 path `82:9122..9136`: call `A5F3` only when `$0302 == 0`;
- frame scheduler `83:CC94..CC9A`: replace `$0302` with `1 - $0302` every frame.

The already-observed race-entry phase seam therefore predicts the clean directional matrix exactly. On a frame where native has `$0302=0` and Snes9x has `$0302=1`, Snes9x alone nudges P1 one unit toward zero while native alone nudges P2 one unit toward zero. That is precisely the observed frame-1532 polarity: P1 Left/Right are one unit closer to zero in Snes9x, while P2 Left/Right are one unit closer to zero in native.

PR #145 dynamically confirmed this static explanation before retiring the exploratory matrix: opposite `$0302` eligibility predicted the one-unit toward-zero nudge for P1 Left, P1 Right and P2 Right exactly. Signed-arithmetic differences inside `A5F3` were therefore retired as an explanation.

That result moved the investigation upstream to the race-entry phase origin. The later three-runtime and race-relative tests below close that question as a host-frame-boundary/absolute-input anchoring effect rather than an event-relative gameplay divergence.

Static main-loop ordering further narrows that root question. In bank 83, the per-frame loop updates scheduler state at `83:CC87..CC9A` before it dispatches into race logic via `83:CD32..CD3A`. The ordinary-2P race routine then writes `inRace` at `83:E070..E073` (and the sibling path at `83:E3FB..E3FE`) without resetting `$0300/$0302/$0304`. Therefore race entry inherits the scheduler parity that already existed on that guest-frame pass; it does not create a fresh phase.

The dense one-frame probe resolves that ambiguity. Frames 1128-1133 match exactly. At frame 1134, Snes9x has already entered race state while native has not:

- native: `inRace=0`, `race_tick=0`, scheduler bytes `0/0/0`;
- Snes9x: `inRace=1`, `race_tick=1`, scheduler bytes `1/1/1`.

At frame 1135 both runtimes report `inRace=1`, but Snes9x remains exactly one race update ahead: native `race_tick=1`, Snes9x `race_tick=2`, with the corresponding one-step scheduler rotation. The offset then persists.

This also rules out the tempting `$1281` scheduler-skip hypothesis for this seam. `$1281`, its nearby countdown/reload state, and both recovered producer selectors remain zero in both runtimes throughout frames 1128-1140. The phase difference is therefore downstream of **one-runtime-earlier race entry**, not a scheduler update skipped after entry.

The same green run dynamically confirms the `A5F3` mechanism at frame 1532 for P1 Left, P1 Right, and P2 Right: opposite `$0302` eligibility predicts which runtime receives the one-unit toward-zero speed nudge exactly. Signed arithmetic inside `A5F3` is no longer a live leading explanation.

The root-cause boundary now moves to the race-entry handshake. `83:C9C8..C9CB` can set `$0C67`; `83:CBA4..CBB2` can clear it; and `83:CD3A -> 83:E066` consumes it before `E070` writes `inRace=1`. The next microtrace captures `$0C67`, `$0DDB`, and `$7E212C` around 1128-1140. Follow whichever handshake byte first differs before investigating later racer physics.

The same probe now also emits the complete cross-runtime WRAM delta at frames 1133 and 1134, plus SRAM deltas when the dump surface provides them. This is deliberately broader than the hand-picked handshake fields: if frame 1133 is globally identical but frame 1134 introduces an earlier state difference outside `$0C67/$0DDB/$212C`, treat that earliest memory delta as the new causal boundary rather than overfitting to the known race-entry code.

Static frontend recovery moves that boundary one step earlier. Entry point `80:99A4` sets SRAM `$77074D = $FFFF`, runs common setup, and then directly calls `83:C8E0` at `80:9A2B`. The sibling `80:999F` entry skips the `$77074D` sentinel write but joins the same setup body. Multiple frontend branches call `99A4`, with SRAM `$7710AD` distinguishing the surrounding setup mode.

The phase-origin probe therefore also reports raw 8 KiB SRAM offsets `$0742/$074B/$074D/$0750/$10AD`. If Snes9x reaches `$074D=FF` one frame before native, the root seam moves out of bank 83 entirely and into the frontend branch that reaches `99A4`; if those SRAM fields already match, continue inside the common setup body.

The five statically recovered `99A4` callers can be distinguished mechanically by the `$7710AD` value established in their surrounding branch:

| `$7710AD` | `99A4` callsite |
| ---: | --- |
| 1 | `80:BC41` |
| 2 | `80:BD68` |
| 3 | `80:BFF5` |
| 4 | `80:BEFA` |
| 5 | `80:94C7` |

Do not attach player-facing mode names to these values until runtime evidence or another recovered source proves them. The purpose of the table is only to turn the SRAM discriminator into an exact frontend callsite.

Run 59 resolves that ambiguity for the ordinary-2P fixture. Both runtimes report `$7710AD=2` and `$77074D=FF` continuously through frames 1128-1134. Combined with the literal `PICK A PLAYER` / `PICK ANOTHER` strings in the `80:BDxx` neighborhood, this identifies the exercised route as `80:BD68 -> 80:99A4 -> 83:C8E0`. Branch selection and the `$074D` ready sentinel are therefore already synchronized before the later race-entry seam.

The same run also shows why a raw whole-WRAM equality test is too coarse here. Frames 1128-1132 already contain a stable 19-byte native/reference difference entirely in low WRAM / stack-scratch territory. At frame 1133, one frame before `inRace` differs, the raw delta expands sharply (82 bytes), again beginning with direct-page and stack-page values. The selected durable race fields remain equal through frame 1133. Treat this as evidence that the runtimes may occupy different control-flow positions inside the transition frame, not yet as proof of divergent persistent game state. The follow-up probe therefore partitions newly appearing deltas into scratch/stack (`<$0200`) and semantic WRAM (`>=$0200`).

Run 67 resolves the remaining phase-origin ambiguity with an independent three-way observation. The same dense 1128-1140 schedule reports first race entry at three adjacent absolute frame numbers:

- Beetle/bsnes: frame 1133;
- Snes9x: frame 1134;
- native: frame 1135.

This is not three different race-state trajectories. At each runtime's own first `inRace=1` frame, `race_tick=1` and scheduler tuple `$0300/$0302/$0304 = 1/1/1`; the following relative frames rotate through the same scheduler/race-tick sequence. The frame-1133 native/Snes9x WRAM growth also lands directly in recovered race-setup staging (`$1359`, `$121F`, `$1277` under `83:CAxx..CCxx`), which is exactly what is expected when one runtime is earlier inside the same transition rather than in a different gameplay state.

The project therefore must not treat boot-relative frame ordinal as a universal SNES time coordinate across libretro cores and the native host. Snes9x, Beetle and the recomp host cut this vblank-shaped transition at different frame boundaries. The shared script grammar is not off by one: all runners define `dump` as the state of the frame just completed. The disagreement is where each runtime's frame boundary lands.

The decisive follow-up aligns controller input to race-relative time. Native enters this route one host frame after Snes9x, so all post-entry native controller events are shifted by +1 frame and native frame `N+1` is compared with Snes9x frame `N` across the P2-only seam. The exact comparison covers scheduler phase, `inRace`, race tick, both racers' X/Y positions, signed X/Y velocities, air state, rotation, and shared working X speed. That assertion passes across every sampled frame 1528-1540.

Therefore the former frame-1532 one-unit X-speed seam is **closed as an absolute-frame anchoring artifact**, not a racer-physics defect. The previously proven `82:A5F3` phase gate remains the local mechanism that makes the artifact visible when the same absolute input frame lands on opposite scheduler parity. There is no evidence here for bad signed arithmetic, player-slot logic, stale saves, or divergent event-relative gameplay evolution.

Do not tune the shared `$4212` virtual-hardware model merely to make native match one emulator's absolute boot-frame count. `80:FAC9` and the `80:BD65 -> 80:9885` fade remain useful explanations for why this transition is vblank-sensitive, but the three-way staircase means neither Snes9x nor Beetle supplies a unique absolute-frame oracle. If exact hardware timing of this frontend transition becomes important later, use a cycle-accurate Mesen/MesenCE run or direct cycle-visible evidence.

The exploratory phase-origin probes and directional A5F3 matrix have been removed from persistent CI. The durable regression is now the compact race-relative ordinary-2P parity check; the causal archaeology remains here as evidence rather than recurring compute cost.

A related community-memory note should remain explicitly qualified: Dessyreqt's 2014 bot reads a word at `7E:11BA` and labels it `countdownTimer`, but the recovered game code initializes, compares, and decrements a 16-bit countdown at `$11BB` (`82:D88F..D895`, `83:E59B..`, `83:E721/E737/E76D`). The bot watch is useful historical corroboration of countdown progress, not an authoritative exact address label. The countdown is downstream of race entry and therefore not a candidate cause of the 1134 entry seam.

## VS active-movement parity refinement

Current-main replay reconfirms exact native/Snes9x paired-racer semantics at stable pre-intervention checkpoints 1240, 1340 and 1440. After the P1-only, P2-only and simultaneous movement sequence, P1 still matches while P2 ends with a very small difference: native `x=1137, vx=-263`; Snes9x `x=1141, vx=-266`.

Do not hide this with a numeric tolerance or call it exact parity. The durable gate requires exact pre-intervention slot state and race-progress parity, then causal agreement after movement: both racer slots must move, P1 Right must produce positive X velocity, P2 Left must produce negative X velocity, and race-progress fields must agree. The small P2 final-state drift remains a bounded fidelity lead for later event-relative timing localization if it persists under the ordinary-2P fixture.

## OAM seam instrumentation

Detailed Snes9x reference capture is now available through the project-pinned debug-export patch:

- OAM: 544-byte snapshot per named dump;
- PPU register state: decoded JSON;
- PPU write journal: frame/V/H/address/value/source;
- ordinary VS-selector capture is proven and shows only vblank-era OAM DMA, so it is not the target seam.

The active-display compatibility fixture should therefore:

1. use the shared four-field neutral controller stream and the existing project-owned dual-controller `snesref` patch;
2. prove P2-only causality after the verified P1->P2 handoff;
3. continue until the first actual 2P/VS race frame;
4. dump OAM/PPU evidence around that transition and search specifically for active-display `$2102-$2104` behavior, especially the historically reported scanline-0/112 split;
5. compare stable gameplay state against the independent Beetle oracle, using patched Snes9x only for the richer PPU/OAM instrumentation surface.

Do not promote the historical OAM workaround itself as expected behavior; the captured game/hardware-facing behavior is the oracle.


### VS handoff controller-causality result

A four-way controller matrix was run at the first proven `PICK PLAYER TWO` state (menu `0x3E`, raw SRAM ownership discriminator `0x02`) using the patched two-pad `snesref` path:

- P1 A
- P2 A
- P1 Down
- P2 Down

Each pulse began at guest frame 660 after the deterministic P1 -> P2 handoff. All four variants remained at menu `0x3E`, selected option `0x00`, raw ownership `0x02`, and the same non-race state through the +190-frame checkpoint. No active-display OAM writes appeared.

This means the raw `0x02` discriminator identifies the UI's Player Two subject/phase but does not, by itself, establish that controller 2 is immediately live. The next discriminator is a bounded timing sweep of P2 inputs after the handoff. If no delayed pulse is accepted, instrument/reference-check whether the libretro core is polling port 1 before inferring game semantics.


## Verified VS first-race and OAM result

The recovered sequence has now been frozen as:

- `tests/input/vs-first-race.input`
- `tests/input/vs-first-race-observe.script`

The route is deterministic from clean boot. P1 enters VS and confirms the first rider; P2 Right selects an unclaimed rider and P2 A confirms; subsequent setup advances reach active split-screen gameplay. Snes9x checkpoints show:

- `vs-challenger`: menu `0x6D`
- `vs-challenge-track`: menu `0x91`
- `vs-pre-race`: menu `0x16`
- `vs-race-1140` onward: `inRace = 0x01`

Most importantly, the patched Snes9x PPU journal reproduces the historical active-display OAM seam in every sampled stable race frame:

```text
V=0    $2104 <- $A5  source=HDMA
V=112  $2104 <- $5A  source=HDMA
```

This repeats at checkpoints 1140, 1240, 1340, 1440 and 1620. The selector-screen negative control had only vblank-era OAM DMA, so the scanline-0/112 pattern is specifically associated with active split-screen gameplay rather than generic menu OAM upload.

`tools/assert_uniracers_vs_oam_seam.py` encodes the two active-display writes as a durable regression assertion. The persistent VS reference workflow also runs the same frozen controller stream through the independent Beetle/bsnes core to verify that the route itself reaches stable split-screen gameplay without relying solely on Snes9x's title-specific compatibility behavior.

This closes the recovered **observability + scene reachability** blocker for the famous OAM seam. Ordinary 2P mode and paired P1/P2 state coverage are now also promoted; the former active-input timing seam is closed by the race-relative parity result above. Mesen runtime parity, richer multiplayer interaction coverage, and widescreen behavior remain separate obligations.


The active-display writes are driven by a stable WRAM HDMA table at `7E:206C`: `70 A5 70 5A 00`. HDMA channel 1 runs mode 0 to `$2104`, producing the observed 112-line split. Future OAM archaeology can therefore start from a tiny deterministic source table instead of rediscovering the raster schedule.

## Controller replay boundary result

The deterministic fixture contract is now bounded tightly enough for project use.

Both project adapters apply the neutral input-file mask from the current zero-based guest-frame counter immediately before executing exactly one guest frame, then increment that counter afterward. Native does this in the desktop host before `RtlRunFrame`; `snesref` does it immediately before `retro_run`. Therefore an event beginning at fixture frame `N` is presented to guest frame `N` in both paths.

On the game side, the ordinary interrupt paths snapshot the SNES auto-joypad result registers `$4218-$421B` into `$030D-$0310`. The currently mapped long-vector target has alternate handlers at `80:85A5` and `80:8610`; both use a full controller snapshot on their applicable path. The separate helper at `80:D1DB` reads `$4218/$421A` directly and is heavily used by blocking frontend/setup loops. Those reads do not consume the hardware latch.

For deterministic fixtures, the required invariant is therefore small:

- keep each controller mask constant for the whole guest frame;
- index events by guest frame, not presentation frame or wall time;
- advance the fixture clock only when a guest frame actually executes;
- do not attempt to model individual reads of `$4218-$421B` inside a frame.

The dense VS race-entry microtrace additionally showed exact native/Snes9x agreement at every sampled 10-frame checkpoint from 1040 through 1240 when both were observed with the same schedule. A mismatch seen only at the sparse `vs-race-1140` observation schedule is therefore treated as observation-cadence sensitivity at the race-entry seam, not evidence that the input adapters disagree by one frame. Stable post-entry checkpoints are the parity gate.

This closes the controller-poll/replay-boundary task for the current deterministic harness. Reopen it only if a future fixture demonstrates a reproducible mismatch that depends on intra-frame input changes, lag-frame semantics, or a host path that advances its event clock without executing a guest frame.
