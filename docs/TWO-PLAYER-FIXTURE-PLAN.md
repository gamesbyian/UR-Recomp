# Two-Player Fixture Capability Plan

Status: deterministic VS route and active-display OAM seam locally reproduced; cross-runtime/native promotion and broader 2P coverage remain.

## Why this exists

The project has an established engine-neutral player-2 controller transport and a deterministic VS route from clean boot through P1/P2 rider selection into active split-screen gameplay. `TWO_PLAYER_SELECT = 0x3D`, `VS_SELECT = 0x3E`, the P1->P2 presentation handoff, a genuinely P2-causal rider move/confirm edge, deeper VS setup states, and first VS race entry now have local evidence. Remaining work is broader native/Mesen promotion, ordinary 2P coverage, paired racer-state assertions, and downstream widescreen/gameplay validation.

Until that evidence exists, durable local promotion remains blocked for several known multiplayer frontend states:

- `TWO_PLAYER_SELECT`
- `VS_SELECT` beyond first entry
- `VS_CHALLENGER`
- `VS_CHALLENGE_TRACK`

It also blocks proper two-player coverage of split-screen rendering, OAM behavior, gameplay interaction, and differential validation.

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

The planned first durable atlas corpus is `ui-two-player-handoff.input`, paired with named state checkpoints proving P1 selection, P2 handoff, P2 selection, and the next multiplayer setup state.

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

Do not mark the capability complete until:

- the same fixture syntax is accepted by every engine adapter that claims shared-fixture support;
- a two-player route produces stable named checkpoints;
- controller assignment is proven, not inferred from a visually similar frame;
- simultaneous P1/P2 input is covered by a small semantics test;
- `tests/fixtures.json` contains at least one durable 2P fixture;
- `analysis/ui-state-map.yml`, `analysis/ui-menu-index.json`, and the UI atlas are updated from local evidence.

## Downstream obligations

With the grammar now available, implement and verify:

1. P2-only causality/confirmation in the initial 2P/VS selectors, building from the verified `0x3D` 2P anchor and verified `0x3E` VS P1→P2 presentation handoff;
2. VS challenger and challenge-track capture after the P2 confirm;
3. first 2P race entry;
4. split-screen/HUD atlas states;
5. two-player OAM compatibility coverage;
6. at least one cross-runtime deterministic multiplayer checkpoint;
7. two-player effects on camera, object activation, and later Widescreen behavior.

Do not allow completion of general fidelity work to imply multiplayer fidelity if these items remain open.

## Ownership / scheduling rule

Any agent modifying the shared fixture grammar, native scripted-input harness, `snesref` input adapter, Mesen fixture adapter, or multiplayer UI code should check this plan and either advance this capability or explicitly preserve its requirements.

Conversely, UI-atlas work should continue on single-controller-reachable states while behavioral multiplayer verification remains open rather than waiting idle.


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

This closes the recovered **observability + scene reachability** blocker for the famous OAM seam. It does not close all multiplayer work: ordinary 2P mode, native/Mesen parity, paired P1/P2 physics/state fields, and widescreen behavior remain separate obligations.


The active-display writes are driven by a stable WRAM HDMA table at `7E:206C`: `70 A5 70 5A 00`. HDMA channel 1 runs mode 0 to `$2104`, producing the observed 112-line split. Future OAM archaeology can therefore start from a tiny deterministic source table instead of rediscovering the raster schedule.
