# Modern frontend master design specification

## Racer Studio: independently editable colours and materials (2026-10-08)

**Product decision:** Racer Studio shall ultimately support independent appearance slots for **tire rubber, rim/spokes, frame/body and saddle**, each with its own curated colour choices; preserve the historical original racer/palette combinations as exact one-click presets. This is an extension of modern racer identity, independent of profile/save identity and guest race authority. The large animated hero previews every edit immediately, including during idle rolling, hops, shimmy and stunt poses. Edit/Cancel/Apply must distinguish a temporary draft from durable committed appearance. Changes may not mutate guest SRAM.

**Phase and scope:** (A) reconstruct component boundaries / pose masks, validate original colour-preservation and ship a colourable hero pilot; (B) cover the full supported in-game racer animation family before declaring a colour option generally usable; (C) add curated material variants such as tread patterns, metallic rims and saddle finishes using authored mask/detail maps, only once coverage, layering and clarity are proved. Phase A may be developed alongside core Racer Studio, but do not treat cosmetic *shipping* as a prerequisite for the Windows baseline root/controls work. Phase C remains post-baseline.

**UI:** A colour/material tab with Tire, Rim, Body, Saddle part selection; visible active-part highlight; easily compared swatches; a restore-original-preset action; optional colour presets and a palette-friendly preview background. Live preview should update on navigation without requiring Apply, but Back discards the draft unless explicitly confirmed. When a classic preset is selected, show its faithful exact original combination; changing a part creates a custom derivative, not a modification of the historical preset. Do not allow an in-editor variant unavailable in races to be mistaken for fully equipped in-game cosmetics. Preview motion, orientation and scaling must not hide the edited component.

**Architecture:** Define versioned, bounded host-owned `RacerAppearance` material slots, independent of guest palette state, profile storage and save-game authority. A source image + validated per-pose component masks / authored component layers + per-slot recolour/material configuration drives a composed racer. For Original mode, do not promise arbitrary recolour of every historical SNES palette until the actual palette sharing, overlap, hardware colour math and sprite composition have been audited; preserve literal original display in Authentic. Remastered/Reimagined may use authored part layers if available. Share one appearance interpretation and asset/version identifiers between hero and race renderer, while allowing mode-specific art variants. Explicit unsupported state must fail closed rather than silently reverting to differently coloured stock pixels; a user-facing launch option must be supported at all needed race poses or marked preview-only development work. Guard OAM priority, occlusion, 1P/2P split, Widescreen, high-density fallback, flips and source-palette ambiguity.

**Acceptance:** per-part distinct chosen colour survives Save -> quit -> relaunch -> race -> restart -> replay metadata where appropriate; all supported animation frames/players show the correct material without flashing fallback; original named presets remain identical in reference presentation; changing an arbitrary material leaves authoritative frame/physics/results/replay hashes unchanged; invalid appearance IDs fail closed safely; missing artwork does not corrupt guest rendering; accessibility provides readable part selection without relying on colour alone; preview accurately predicts racing appearance. Capture packaged 4:3/16:9 and Original/Remastered when applicable.


## Racer Studio hero-showroom specification (2026-10-08)

**Primary design requirement:** Racer creation/editing must be dominated by a large animated unicycle hero preview, inspired by racing-game car showrooms but rendered in the authentic side-on Uniracers visual language. The preview is the centerpiece, not a tiny icon next to a form. Changing accepted name, legacy preset, colour, or any supported cosmetic updates the preview immediately without mutating guest simulation or unrelated profile data.

**Animation vocabulary:** continuous gentle racing-in-place/wheel roll, small playful hops, restless lean/shimmy, occasional wheelie or flip/show-off flourish, plus short change-reaction motions. Use a deterministic, bounded frontend-only animation state machine with idle dwell timing, transition priority, event interruption, reduced-motion fallback and freeze/resume policy. On screen entry, play a short flourish if enabled. When the player moves through colour options, apply the visual change without waiting for the current animation to end. Manual directional spin or advance-to-pose is optional after evidence-backed art capability exists.

**Dimensional scope:** baseline is 2D in-plane roll, pitch, flip and lean, with existing/source-inspired authentic racer sprites and optional authored tween/in-between frames. Genuine vertical-axis 360-degree rotation, front/back inspection or free 3D orbit is *not* required; those would need newly drawn multi-angle assets or optional 3D/2.5D rendering, which the existing racer OAM pipeline does not provide. Avoid implying the recovered side-on frames encode unseen three-dimensional surfaces.

**Layout:** at 16:9, reserve the largest visual region for the hero, with name/preset on one side and colour/cosmetic choices on the other, adaptable to 4:3 by stacking or compacting the choice panels around the hero. Use shared original-derived type, colour, cursor animation, input legend and SFX. Selection focus must remain clear while the unicycle moves. Show the currently committed identity separately from unsaved edited preview; Cancel returns without changing it. A classic original-art preview toggle is useful when multiple render modes exist, but a fake 'Authentic sprite preview' should never claim unavailable fidelity.

**Engineering:** create frontend-only `RacerShowroomPreviewModel` / `RacerShowroomAnimator` (conceptual names) consuming a copy of selected racer appearance and a read-only pose/anchor registry. Start with a simple composited 2D wheel/body hero using verified motion frames; add measured head/seat/wheel anchors for each exposed cosmetic animation pose; fail closed to stock unadorned pose when unsupported. Keep the preview separate from gameplay's authoritative racer snapshot and host HD/OAM replacement; reusing asset identifiers or geometric evidence must not convert showroom motion into guest animation authority. Never require a new 3D runtime. Keep cosmetic categories capability-gated until real renderer/persistence consumers ship. Honorary crown remains name-derived, not saved authority.

**Milestones:** (1) verified stock-asset hero + idle rolling + colour/preset preview, (2) hop/shimmy/stunt loops with cancel/interrupt/reduced-motion and 4:3/16:9 acceptance, (3) validated accessory anchors and instantaneous cosmetic preview as cosmetic feature lands, (4) optional authored higher-resolution preview skins or extra poses. Validate visually in packaged Windows executable, including 1x/4x density, immediate option switching, no input bleed, changes discarded on Cancel, no profile cross-contamination, and Authentic guest/runtime inertness.


Status: proposed unified product/design contract, 2026-10-08. This is a forward-looking design specification, not evidence that every screen is currently integrated. Preserve existing implementation ownership. Cross-check `MODERN-FRONTEND-SHIPPING-STATUS.md`, `MODERN-PRODUCT-LAYER.md`, `MODERN-UI-VISUAL-FIDELITY.md`, `MODERN-RESULTS-NAVIGATION.md`, `MODERN-RACER-COSMETICS.md` and acceptance before declaring shipping completeness.

## North star and non-negotiables

Create a modern frontend that feels like an authentic expansion of Uniracers/Unirally: recovered title identity, memorable type and colour relationships, energetic dimensional highlight, snappy sound cues, playful motion, recognizable results and original indicators. Reject generic translucent dark dashboards, arbitrary new branding, vertical lists of debug commands, and 1994 administrative inconvenience.

The settled top-level destinations remain **Play / Practice / Multiplayer / Records / Options** in precisely that order. Options contains settings, not profile management. Profile/racer switching is a globally accessible identity action at the menu shell, not a sixth destination. Root presentation is separate from existing authoritative guest/host route controllers. Authentic execution is untouched. The current shipped F-key and settled-stock shortcuts remain valid until a tested root replaces them as the primary discoverable path.

## Universal player flows

Launch: publisher/legal where required -> brief title animation -> stock-faithful attract/Press Start -> auto-select last valid profile or first-run racer setup -> root. Skip animated opening with Confirm/Start. Never require a profile picker at every boot. First-run user gets a short playable or skip-able onboarding pathway, reachable later under Help, with the stunt-to-speed link explained accurately from verified guest mechanics.

Returning player: title -> root defaults to the last appropriate Play task/Continue context where available; Confirm begins in no more than three meaningful actions. Escape/back from root returns to title only on deliberate choice, not accidental repeat input.

Race: pre-race context/entry -> stock race -> host pause overlay -> authoritative stock results ritual -> contextual Modern results actions -> next race, retry, track/tour select, or frontend. Result actions are only offered if their current existing authority is valid; Quick Practice never acquires progression authority. Do not invent a universal save/continue checkpoint in arbitrary guest contexts.

Modern and Authentic modes must be explicitly named on a discoverable startup/settings surface; do not silently switch modes mid-race or imply hot swapping of guest semantics. A mode change that requires restart should explain and confirm it.

## Screen IA and action contracts

### Title / Attract

Preserve region-specific Uniracers/Unirally name and original title character. Stock-compatible attract is default. Prompt: Press Start / Enter. If user idle, attract/demo begins; any input restores title without inadvertent double-activation of menu. Optional local showcase later, never replacing stock reference by default. Visible small version/build information may live in a footer, not interrupt title spectacle.

### Root shell

Five prominent entries: **Play / Practice / Multiplayer / Records / Options**. Each entry has a selected-state motion treatment and concise contextual right-side preview, not a permanent menu of all subfeatures. A persistent compact identity strip shows current racer name, color/preset and active profile; selecting it opens Racer & Profiles (global drawer). A contextual last-race/continuation hint is permitted only when authoritative and current. Menu controls and Back legend anchored consistently. Root should never require F-keys to discover core tasks. No disabled mystery destination as a fake complete feature.

### Play

First destination: **Continue Tour** when a valid existing continuation exists (contextual), otherwise **Start Tour**. Secondary: **Choose Tour**, **Racer & Profiles** via identity shortcut, **Tour Progress**, and **How to Play**. Continue route displays selected tier/tour/current event and is omitted when the underlying continuation is absent. Restart Tour is a separate destructive-ish action with a confirmation spelling out what is being replaced; only the existing transactionally validated continuation contract may retire state. Never auto-restart a valid tour. Preserve Bronze/Silver/Gold original indicator/presentation and proven stock tier rules, while Modern copy makes progression understandable.

### Practice

**Quick Race** default, **Choose Course**, **Recent Course** when valid, **Personal Best / Previous Ghost** selection, **Help / Controls** secondary. Picker uses existing stock-unlock-filtered course roster, with course family, event type, personal best/target when known, and legible owned preview. Do not display locked-course secrets. Record/ghost flags use current profile and validated eligibility; Practice remains isolated from tour progression. Post-result: Repeat Practice and optional Choose Course / Records, never Next Event.

### Multiplayer

**Local Race** and **Local Tournament** are two high-visibility choices with separate entry points; no need to traverse cartridge league administration. Screen prominently shows P1/P2 seats, controller identity, joined/ready state and controller conflict/unplug warnings. Tournament submenu: New Tournament / Continue Tournament when existing durable coordinator authorizes it / Standings & Fixtures / History. Use the implemented coordinator and real seated fixture arm; never fabricate tournament standings or multi-session completion. P2 must be able to join without stealing P1 navigation. A disconnected P2 should be offered reconnect, reassign or cancel choices appropriate to actual host capability.

### Records

Overview scoped to current profile. Primary tabs: **Personal Bests**, **Completed Runs**, **Tour Medals**, and **Local Tournament Results** when valid. These are views onto existing sources, not a merged replacement records database. Selected run detail shows course, mode, date, exact time, result provenance, ghost availability, and validated Replay/Practice This Course actions where admitted. Distinguish personal best from most recent; malformed/unavailable artifacts have meaningful non-destructive error messages. No fictional online leaderboards. Maintain stock results/record aesthetic and original indicators alongside optional extra timing data.

### Options

Category pages: **Video**, **Audio**, **Controls**, **Gameplay & Accessibility**, **Storage / Data**, **Help & Credits**. Only expose settings with real consumers; label unsupported planned entries in documentation, not as functioning shell rows. Video includes present shipped display mode, VSync, presentation FPS, output resolution, Widescreen View, Internal Render Scale; eventual art mode Original/Remastered/Reimagined should be capability-gated to real coverage. Keep display geometry (Authentic 4:3 vs Raw Pixels vs modern square-pixel) conceptually separate from logical viewport width (Original vs Widescreen) and asset style. A live mode-change preview must be reversible and rollback on host failure; do not promise a timed auto-revert without a working timer/persistence contract. Presentation FPS never controls simulation. Audio options await implemented consumer. Controls reuse existing remap authority, not a second input schema. Text-size, reduced flashing, haptics, focus pause and other accessibility rows appear only when working and persisted.

### Racer & Profiles

Global shell action (not sixth root destination). Profiles are independent save namespaces and selected racers are independent identity/presets. Primary action switch profile, followed by New Profile, Rename, Select Racer, Edit Racer, Reset Progress (high-friction confirm with profile named). Racer creator: classic named/color presets, modern name editor, body color selection; preserve existing forbidden-name COOL NAME! acknowledgment. Cosmetics tab is post-baseline and should only appear once supported: hat/scarf/wheel/aura/trail; contributor-derived honorary tilted gold crown is automatic for accepted names containing halamantariel/dessyreqt/nitrodon (ASCII case-insensitive) and independent from ordinary headwear. Do not persist a crown unlock or confuse it with original name-trigger rules. Show unsupported cosmetic poses without false previews or guest mutation.

### Pause

Host-owned freeze of authoritative frames, with legible frozen scene and recognizable game styling: **Resume**, **Restart Race**, **Run Data**, **Options**, **Controls**, **Records** when valid, **Exit to Frontend**, **Quit Desktop**. Resume default; Back resumes only if no nested/modal/dirty operation. Restart/Exit/Quit confirmation depends on genuine loss risk; do not put a modal on every harmless action. Use already established pause hold and input-release suppression, not another guest timer.

### Results

Always show and respect original scoring/result ritual first. Once authoritative result stable, additive ribbon presents context-authorized actions. Tour: uniquely derivable **Next Event**, **Retry**, **Track Select**, **Tour Select**, **Records**. Practice: **Repeat Practice**, optionally Choose Course / Records. Tournament results: fixture and standings authority only. Keep default action stable across row-settling; selection becomes sticky after explicit player movement as existing contract. No fake Next Event when ambiguous.

### Dialogs, loading, failures

Dialog types: confirmation, consequential/destructive confirmation, information/achievement, input capture, recoverable error, unrecoverable error. Consistent Yes/No and Cancel focus, named subject/consequence, reliable Back behavior. Fatal errors should explain what was preserved and where logs are when known. Saving indicator appears only on actual writes, never indefinite. Failed saves never claim success. Do not allow confirmation input to bleed through and trigger the underlying stock menu.

## Visual system

Measure and inventory reference screens using `UI-STATE-MAP.md`, `analysis/generated/menu-visual-language.json`, `analysis/generated/menu-sfx-ids.json`, and emulator-native screenshots before final art. Define named visual tokens from measured original rather than invented arbitrary hex codes. Preserve regional title identity. Proposed component grammar: distinct original-inspired background field; large bright dimensional title; diagonal/slanted emphasis motifs where justified by source; animated selected racer/wheel marker; colorful expressive item labels; concise bottom legend; contextual secondary panels only when extra information earns the space. Selected state must be perceivable without color, with non-flashing movement and strong glyph contrast. UI sound vocabulary must be mapped to genuine source IDs after evidence review. Avoid unbounded looping animations on modal surfaces.

At 4:3 use predominantly stacked composition and reveal details contextually. At 16:9 use an intentional two-region composition: stable primary decisions left/center, detail/preview to right; do not simply stretch the 4:3 raster. Allow 21:9 only after evidence-backed viewport contracts. Respect full 224 logical-height policy and accepted PAR/display geometry; use safe margins for TV overscan and desktop scaling. Preserve minimum legibility at 1080p and 4K TV viewing distances without overwriting original gameplay indications. Use 1x–4x density-compliant text and sprites; density is not an accessibility text-size substitute. Reduced-motion/reduced-flash accommodations need real compositor semantics before shipping as options.

## Input/focus/navigation laws

Controller-first; keyboard parity; P1 controls shell outside explicitly joined multiplayer seat actions. Use semantic Confirm, Back, Up/Down, Left/Right, tabs, and optional Help. Root wraps as existing model permits; option lists should not wrap if that obscures endpoints unless deliberately documented. Show remapped controller labels for mapped actions, physical-button prompts only for literal physical bindings. Capture rebind input with timeout/cancel/duplicate-resolution that cannot strand the user. Hotplug must not silently reassign seats or cause phantom Confirm. Debounce/release-suppress entry and exit, including hold-at-close and double-trigger. One surface owns input at a time: nested dialog > modal > root > guest, and frame hold follows existing `frontend_modal_hold_wanted()` / pause architecture. Restore previous logical focus on Back, unless action invalidated it, when choose deterministic nearest safe element. Root and all submenus must be entirely playable without undocumented F-key shortcuts.

## State and serialization

Treat UI selection/scroll as ephemeral session state; profile/racer identity and options use existing versioned bounded stores; guest tour/SRAM remains authoritative for its own semantics; records/replays/ghosts use established profile-scoped artifacts. Do not persist menu stack or stale guest contexts as playable authority. Fresh-process load must reconcile stale, missing and corrupt contexts and offer benign fallback without destroying source evidence. All external file choices and failure responses have bounded decoding and safe traversal rules. Changes to graphics/output settings are transactional and roll back on application or persistence failure. Profile switch is blocked or confirmed when a race or unsaved operation has exclusive ownership.

## Bounded root-route implementation gate (QA-of-QA 2026-10-08)

The first increment is **one functioning, player-visible, pad-operated Modern root** over the existing typed model. Use existing host/stock destinations and a single focus/hold policy, then expand to all five destinations before adding elaborate animations or new menus. A mockup, isolated root unit test, keyboard F-key path, or newly built shadow router does not meet this implementation gate. Capture cold ZIP → root → practice/race → result → Records → Quit, then validate P2 join and pause/held-input transitions. Route production work belongs to frontend; independent QA-09 measures uncoached discovery on that completed implementation. Timebox the first minimal vertical slice to 12 productive hours for a demonstrable path or a specific blocker and re-estimate wider visual art separately; see [QA-AUDIT-OF-AUDIT-20261008.md](QA-AUDIT-OF-AUDIT-20261008.md). The planned Racer Studio hero/material customizer remains deliberately outside this first critical path.

## Priority implementation slices

P0-A: render a real five-destination root over settled Modern title flow using existing typed root model and router guards; preserve F-key convenience; end-to-end packaged controller-only journey.
P0-B: shared menu layout/rendering component library, reference-derived art tokens, sound hooks, responsive 4:3/16:9 shell; retire provisional black rectangles surface by surface.
P0-C: Play/Practice/Multiplayer/Records/Options routing to **existing** authorities; integrated Racer & Profiles global strip. Validate every path with fresh process and first-time user journey, without new duplicate models.
P0-D: contextual results/pause consistency, focus and hold ownership, controller seat/hotplug, error/recovery, safe prompt system.
P1-A: actual visually cohesive Tour Progress, Records/run detail, Controls, Local Tournament and Help/Onboarding.
P1-B: persistent accessible text size, safe-area and flash/motion controls only with actual presentational consumers.
P1-C: consumer-complete audio, advanced graphics-mode picker and optional cosmetic presentation when dependencies land.
P2: richer contextual course previews, elaborate racer studio, advanced replay controls, local showcase, additional personalization.

Parallel ownership: one agent can own shared visual primitives/asset extraction; one root routing/interaction integration; one player journey QA/screenshot review. Avoid concurrent edits in title routing/product state while a frontend owner is active. No shadow navigation coordinator, no shadow records/progression schema, no new guest-memory write surface.

## Concrete acceptance matrix (each major surface)

- Authentic unchanged; Modern route backed by valid guest/host authority.
- Controller-only start-to-finish navigation, keyboard parity, remapped prompts, held-input closure, nested Back, P2 seat handling if applicable.
- Stock original look reference review and packaged executable captures at 4:3, 16:9, default/high internal density, desktop and TV-safe legibility.
- Screens: empty profile/no run, populated profile/records, fresh tour/unfinished tour, missing/corrupt record, disconnected controller, save failure, display-mode apply failure, focus loss while modal open, restart/exit confirmation, race result settling, no stale action after profile switch.
- Mouse support where naturally available on desktop may be additive but must not be necessary to use any menu.
- Surface visual approval requires before/after reference snapshots, one selected-state/motion capture, and real source-aligned feedback sound evidence. Functional smoke alone is insufficient.
- Release-gate uncoached first-time player: title -> create/select racer -> Play or Practice -> race -> results -> repeat/continue -> Records -> exit. Verify on candidate Windows ZIP, not a mock or pure unit model.

## Open design decisions and evidence tasks

Before final art lock: measure original font proportions, menu object animations, selected-state shapes, color swatches, UI SFX timing, background motion and region differences. Before shipping root: establish the exact title/menu state where P1 input handoff may safely occur; make a route/state matrix. Before shipping any new setting: identify owning consumer, persistence and rollback. Before claiming local multiplayer complete: validate actual 2P admission, controller hotplug and full multileg resume on real hardware. Before accepting visual signoff: compare recorded packaged screenshots against original title/menu reference and check readability with eyes off keyboard.

This design is additive to existing contracts and should be refined through implementation evidence, not treated as proof of a finished frontend.
