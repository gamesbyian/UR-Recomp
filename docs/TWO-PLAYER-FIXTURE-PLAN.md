# Two-Player Fixture Capability Plan

Status: deterministic VS and ordinary-2P routes are both reproduced. Ordinary 2P is promoted to a durable two-controller fixture with isolated P1-only, P2-only and simultaneous movement checkpoints plus the active-display OAM seam. Native/reference VS semantics are exact before active movement, with a tiny post-input P2 timing drift preserved as open evidence.

## Why this exists

The project has an established engine-neutral player-2 controller transport plus deterministic VS and ordinary-2P routes from clean boot into active split-screen gameplay. `TWO_PLAYER_SELECT = 0x3D`, `VS_SELECT = 0x3E`, two-controller rider selection, deeper setup states, first race entry, paired racer-state assertions, simultaneous input, and the active-display OAM seam now have local evidence. Remaining work is full Mesen runtime promotion, the small post-input native/reference P2 timing seam, richer split-screen/HUD interaction coverage, and downstream widescreen validation.

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

## Native/reference P2 timing seam

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

The USA race-update routine copies P2 persistent X speed `$04B9` into shared working X speed `$0F9F`, processes the common racer physics path, then copies `$0F9F` back to `$04B9`. The current trace now includes decoded P2 horizontal direction and the shared working speed/rotation fields. The next useful question is whether the first 1-unit delta enters while loading player-specific state, inside a direction-dependent common-physics operation, or from contact/course state. Do not broaden this into a full-physics trace unless those fields fail to discriminate.

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

This closes the recovered **observability + scene reachability** blocker for the famous OAM seam. Ordinary 2P mode and paired P1/P2 state coverage are now also promoted; Mesen runtime parity, the small active-input timing seam, richer multiplayer interaction coverage, and widescreen behavior remain separate obligations.


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
