> **2026-10-09 live integration qualifier:** The legacy Windows Modern state models and typed five-destination root are reusable, but **controller-only root on a completed Baldosa Modern product has not yet been admitted**. Open #1056 owns visible root/Restart Return guest-input release on the established host; the Baldosa C ABI/lifecycle lane must *consume* that work, not fork a new frontend. Merged #1085 proves native Win32 2P/pause behavior, not the complete Modern root or packaged record journey. [WORK-QUEUE.md](WORK-QUEUE.md) owns the current feature/QA join.

# Windows x64 Modern frontend: shipped surfaces and remaining integration

## Material-colour customization status (2026-10-08)

The Racer Studio design now calls for an animated 2D hero and independently editable **tire, rim, frame/body and saddle** colours, with future curated textures. This is **planned only**: the current game does not have a verified four-part mask atlas, complete showroom/race recolour pipeline, or claimed player-facing persistence. Track implementation against [`MODERN-FRONTEND-MASTER-DESIGN.md`](MODERN-FRONTEND-MASTER-DESIGN.md) and [`MODERN-RACER-COSMETICS.md`](MODERN-RACER-COSMETICS.md); do not promote an attractive preview without complete race-pose parity and original-preset fidelity.


## QA-of-QA implementation dependency (2026-10-08 local)

[QA-AUDIT-OF-AUDIT-20261008.md](QA-AUDIT-OF-AUDIT-20261008.md) confirms that **unimplemented real five-destination root routing is a feature-completion job** (tracked as [#1053](https://github.com/gamesbyian/UR-Recomp/issues/1053)), not merely a QA-09 evidence gap. Treat the master design P0-A/P0-C visible root and Play/Practice/Multiplayer/Records/Options wiring as one bounded frontend implementation slice using the existing typed root, product state, and stock/host route authorities. First demonstrate controller-only cold launch → visible root → Play or Practice → authentic result → Records/Repeat → Quit without F-key hints. Then improve stock-inspired presentation, accessibility and TV legibility on the same route. Start with the smallest end-to-end vertical slice; after 12 productive agent-hours without a usable controller-only root route or confirmed blocker, stop and re-estimate instead of erecting another menu framework. Full visual art/content effort is separately costed; never silently count it as QA validation.

A distinct confirmed defect, [#890](https://github.com/gamesbyian/UR-Recomp/issues/890), links Modern Restart's Return confirmation to guest Start and subsequent silence. Frontend/input owns the host/guest release correction and first resumed guest-word witness; QA-06 reuses its **audible tail** as a co-oracle. Do not redirect this to original SPC/DSP archaeology or accept `Start=None` as the consumer fix.

## QA-05/09 pending implementation candidate (2026-10-08, unmerged)

Branch `qa05-modern-root-and-restart-ownership-20261008` adds a rendered five-destination host shell and controller/keyboard focus handoffs to the **existing** stock 1P/2P, Quick Practice, Records, Options and Racer/Profiles authorities. It introduces a physical-key-release barrier for default Return-as-guest-Start after Restart and targeted guest-word diagnostics. `tests/native/run_modern_root_acceptance.sh` and `tests/native/modern_restart_key_release_test.cpp` provide fresh-process root smoke and pure edge-policy coverage. Details and independent evidence requirements: [QA05-QA09-FRONTEND-INTEGRATION-EVIDENCE.md](QA05-QA09-FRONTEND-INTEGRATION-EVIDENCE.md).

**Status: under review, not shipped.** Local pure restart filter assertions pass, but native integrated build, packaged Windows pad-only journey, 5/5 audible default-Return Restart tails, and approved visual fidelity are **unverified**. The table and main-branch assertions below remain unchanged until a reviewed merge. Do not close #890 or #1053 on source-only evidence.

## Target design and current-status boundary

The cross-screen proposed information architecture, detailed screen behavior, input/focus invariants and priority implementation sequence are specified in [`MODERN-FRONTEND-MASTER-DESIGN.md`](MODERN-FRONTEND-MASTER-DESIGN.md). Treat it as the design target **only**: no unchecked design row, future Options category, racer studio, or responsive art treatment counts as shipped. Retain this file as the verified route/source-of-authority index, reconcile each newly landed screen against native acceptance, and keep stock menu fidelity and first-time controller discoverability as separate release conditions.

Status snapshot: **2026-10-08 UTC**, reviewed through `main` `7d2a75312`. This is a routing/readiness index, not a new frontend specification. The source of truth for behavior remains the implementation and native acceptance; update this index when the corresponding merge changes a shipping claim.

## Player-facing surfaces already on main

| User entry | Required title/host context | Existing authority | Evidence |
| --- | --- | --- | --- |
| Quick Practice **F5 / physical pad X** | Modern, settled one-player main menu | Stock-unlock-filtered course picker and target-aware stock route. Cancel restores session, Practice isolation preserved. | Merged #734; `run_modern_practice_picker_acceptance.sh` |
| Resume / Restart Tour **F3 / physical pad Y** | Modern, settled main with authoritative unfinished tour | Existing tour continuation, confirmed Restart, Next Event where uniquely derivable | `run_modern_tour_entry_acceptance.sh`, `run_modern_next_event_acceptance.sh` |
| Recent Course **F6 / physical pad R** | Modern, settled main with profile-owned recent course | Existing isolated Practice launch (Y may belong to Tour) | `run_modern_recent_course_persistence_acceptance.sh` |
| Tour medal overview **F7 / mapped P1 L** | Modern, settled main, valid stock rider/medal/unlock projection | Read-only stock SRAM; secret progression not disclosed | Merged #740; `run_modern_tour_overview_acceptance.sh` |
| Frontend Options **F10 / mapped P1 Select** | Modern, settled main with no conflicting host surface | Same live/persisted Options panel as pause, without issuing a guest pause | Merged #746; `run_modern_frontend_options_acceptance.sh` |
| Frontend Controls **F9**, or **mapped P1 X** while frontend Options is open | Modern, settled main, nested Options context | Same SNESRecomp P1 keybinding capture/save authority as pause; Back returns to Options | Merged #752; `run_modern_frontend_controls_acceptance.sh` |
| Racers / Profiles **F2 / physical pad X** | Modern, stock `0x3C` rider-select screen | Existing profile catalog/racer identity, isolated SRAM and confirmed Reset Progress | Profile UI fresh-process acceptance |
| Results Rematch / Repeat Practice, Track/Tour Select, Next Event, Records | Supported Modern results surface, as narrowed by current route guard | Existing results navigation / Quick Practice / tour / paused Records authorities | `run_modern_results_navigation_acceptance.sh` and Shared Modern native acceptance |
| Records (read-only) **F8**, or **F8 / physical pad X** from Tour Progress | Modern, settled main with no conflicting host surface or route | Same profile-wide Records browser as pause, unpaused with host input ownership and frame hold; no Local Runs/replay handoff | `completed-run-replay-acceptance.yml` main-menu Records step |
| Local Tournament **F4 / mapped P1 L** | Modern, stock 2P select (`0x3D`) after both join seats are confirmed | Existing tournament coordinator: create (OS-minted IDs), standings, fixtures, history, arm seated fixture | `run_modern_local_tournament_panel_acceptance.sh` (`docs/MODERN-LOCAL-TOURNAMENT-PANEL.md`) |
| In-race Pause, Options, Controls, Run Data, Records, Exit to Frontend, Quit | Modern race/results pause authority | Host session pause + real paused-frame presentation, not guest simulation while frozen | `docs/PAUSE-CONTROLLER-NAVIGATION.md` and Native UI evidence |

The entries above are **shortcuts and existing stock frontend flow**, not proof that the eventual five-destination Modern top-level menu exists as a rendered and routed player-facing root. `native/product/modern_root_menu.hpp` is currently a pure typed model (Play / Practice / Multiplayer / Records / Options); its labels and localization boundary are implemented, but the full live root router is not. Play and Multiplayer still follow stock title administration; the Records browser is now also admitted read-only from the settled main menu, but no rendered root routes to it. Do not declare a fully integrated Modern root, and do not invent a second route, records model, progression model or paused-session policy to make the root appear complete.

## Additional whole-player acceptance (release level)

The rows above are implemented entry points and local acceptance, **not evidence that a first-time player can discover or complete the whole task**. New gate QA-09 requires the actual packaged game to support a full uncoached onboarding → racer/profile → play → result → continue → records → quit journey without undocumented function keys; include TV-distance/readability, pad-only navigation, accessibility and meaningful recovery messages. QA-05 covers input-held-at-modal-close, controller-seat changes, per-surface guest freeze and action sequences after navigation. See [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md) J-01/J-11/J-12/J-19. The root router and provisional panel visual style remain shipping debt even if all existing shortcuts pass.

## Remaining bounded shipping work

1. **Root navigation integration:** wire each of the five destinations to an **existing** title/host authority and prove the real Windows route end-to-end before exposing it. Distinguish directly callable destinations (Practice, Options) from guest-owned Play/Multiplayer transitions and paused/result-owned Records. A disabled or inoperable row is not a completed root.
2. **Modal lifetime:** **[shipped, #763]** human-driven sessions hold guest frames while a settled-main-menu host modal is open (Practice picker, Tour Progress/action, frontend Options/Controls, Welcome, and now main-menu Records); the stock 2P select Local Tournament panel uses the same hold. `--script` harnesses never hold. Reuse `frontend_modal_hold_wanted()`; do not add a second timer mechanism.
3. **Visual fidelity:** present Modern surfaces with the original game's visual grammar while allowing proportional repositioning/resize in true Widescreen. Temporary dark rectangles are not final art direction. The original-game visual grammar and responsive re-layout acceptance are now documented in merged **PR #760** (`docs/MODERN-UI-VISUAL-FIDELITY.md`), but the current functional black host panels still require actual art/presentation implementation and Windows screenshot review.
4. **Accessibility:** existing adaptive text-fit/large-text model is not yet a persisted user-facing text-size option, and reduced flashing has no admitted product compositor seam. Do not conflate logical glyph-density scaling (1x–4x presentational output) with an accessibility font-size choice.
5. **Controller glyphs:** Controls/onboarding and the Local Tournament strip resolve live remapped pad names for GamepadMap-routed inputs (SNES L / Select); physical-button hints stay literal. Keep new hints on the same rule, never guessed physical-brand glyphs.

## Guardrails for follow-on agents

- Before edits, refresh `main`, inspect open PRs and recently touched branches. Never claim a feature is unimplemented merely because an older section in `docs/PROJECT-PLAN.md` or `docs/SEMANTIC-SUFFICIENCY.md` says a PR is pending.
- `docs/MODERN-PRODUCT-LAYER.md`, `docs/MODERN-RESULTS-NAVIGATION.md`, `docs/MODERN-TOUR-OVERVIEW.md`, `docs/MODERN-FRONTEND-OPTIONS.md` and `docs/MODERN-FRONTEND-CONTROLS.md` own the respective product contracts. This page summarizes status only.
- Maintain Authentic inertness, host input-release suppression, authoritative stock guest state and profile-local persistence. Native acceptance must assert the actual playable route, not merely an overlay's `OPENED` diagnostic.
- Finished Windows x64 player-facing routes must pass the shared native acceptance, onboarding/practice acceptance, UI evidence, unit suite and Authentic/widescreen gates as applicable.

