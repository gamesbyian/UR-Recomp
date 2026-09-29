# Two-Player Fixture Capability Plan

Status: required supporting capability for UI-state coverage, multiplayer fidelity, and split-screen/emulator-sensitive validation.

## Why this exists

The current project-owned input-fixture grammar is sufficient for the one-player frontend and gameplay routes, but the repository does not yet expose an established, engine-neutral way to express player-2 controller input.

That blocks durable local promotion of several known multiplayer frontend states:

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

The project already tracks broader Uniracers OAM/rendering compatibility history. Once shared player-2 input exists, include a deterministic split-screen framebuffer/OAM checkpoint so a one-player-perfect runtime cannot silently retain a player-2-only rendering defect.

## Required capability

Extend the shared deterministic fixture model so one script can address at least controller ports 1 and 2 without becoming engine-specific.

The surface should satisfy these requirements:

1. **Explicit controller identity.** A script action must say which SNES controller receives the input.
2. **Backward compatibility.** Existing one-player scripts retain their current meaning without edits.
3. **Cross-engine semantics.** Native recompilation, `snesref`/libretro routes, and Mesen adapters must interpret the same controller actions equivalently.
4. **Simultaneous input.** It must be possible to hold buttons on P1 and P2 during the same guest frames.
5. **Deterministic duration.** Controller-specific presses/holds use the same frame-count semantics as current `press` commands.
6. **No hidden mode assumptions.** The fixture should express controller input, not special-case Uniracers menus.
7. **Observable checkpoints.** Existing `until`, `wait`, `dump`, reset, and turbo behavior must remain usable around multiplayer actions.

A reasonable grammar shape could be either:

```text
press p1:a 2
press p2:right+a 2
```

or:

```text
p1 press a 2
p2 press right+a 2
```

The exact syntax is not yet authoritative. Choose the smallest extension that fits all engines and preserves old scripts.

## Integration with dual-controller transport PR #31

PR #31 supplies the transport layer this plan was waiting for rather than a competing scene-script grammar.

Its neutral stream format is:

```text
start:duration:p1-mask[:p2-mask]
```

The three-field form remains P1-only. The optional fourth field is an independent P2 mask using the same 12-bit SNES layout. The same stream is being wired through native Lua replay, patched `snesref`, and Mesen.

Once #31 lands, keep the layers separate by responsibility:

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

Once the grammar is available, immediately schedule/implement:

1. 2P rider-selection handoff and back-stack capture;
2. VS challenger and challenge-track capture;
3. first 2P race entry;
4. split-screen/HUD atlas states;
5. two-player OAM compatibility coverage;
6. at least one cross-runtime deterministic multiplayer checkpoint;
7. two-player effects on camera, object activation, and later Widescreen behavior.

Do not allow completion of general fidelity work to imply multiplayer fidelity if these items remain open.

## Ownership / scheduling rule

Any agent modifying the shared fixture grammar, native scripted-input harness, `snesref` input adapter, Mesen fixture adapter, or multiplayer UI code should check this plan and either advance this capability or explicitly preserve its requirements.

Conversely, UI-atlas work should continue on single-controller-reachable states while this dependency is open rather than waiting idle.
