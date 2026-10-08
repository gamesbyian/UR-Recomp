# Windows x64 Modern frontend: shipped surfaces and remaining integration

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
| In-race Pause, Options, Controls, Run Data, Records, Exit to Frontend, Quit | Modern race/results pause authority | Host session pause + real paused-frame presentation, not guest simulation while frozen | `docs/PAUSE-CONTROLLER-NAVIGATION.md` and Native UI evidence |

The entries above are **shortcuts and existing stock frontend flow**, not proof that the eventual five-destination Modern top-level menu exists as a rendered and routed player-facing root. `native/product/modern_root_menu.hpp` is currently a pure typed model (Play / Practice / Multiplayer / Records / Options); its labels and localization boundary are implemented, but the full live root router is not. Play and Multiplayer still follow stock title administration; the Records browser's admission is pause/results-owned rather than a free-standing main-menu browser. Do not declare a fully integrated Modern root, and do not invent a second route, records model, progression model or paused-session policy to make the root appear complete.

## Remaining bounded shipping work

1. **Root navigation integration:** wire each of the five destinations to an **existing** title/host authority and prove the real Windows route end-to-end before exposing it. Distinguish directly callable destinations (Practice, Options) from guest-owned Play/Multiplayer transitions and paused/result-owned Records. A disabled or inoperable row is not a completed root.
2. **Modal lifetime:** settled main-menu attract/timeout can replace an open host modal unless the guest input-frame hold policy is installed. Work for that specific fix is carried in **PR #763** as of this snapshot; do not describe it as merged or recreate a second hold/timer mechanism. Verify current PR state before assigning new work.
3. **Visual fidelity:** present Modern surfaces with the original game's visual grammar while allowing proportional repositioning/resize in true Widescreen. Temporary dark rectangles are not final art direction. The original-game visual grammar and responsive re-layout acceptance are now documented in merged **PR #760** (`docs/MODERN-UI-VISUAL-FIDELITY.md`), but the current functional black host panels still require actual art/presentation implementation and Windows screenshot review.
4. **Accessibility:** existing adaptive text-fit/large-text model is not yet a persisted user-facing text-size option, and reduced flashing has no admitted product compositor seam. Do not conflate logical glyph-density scaling (1x–4x presentational output) with an accessibility font-size choice.
5. **Controller glyphs:** the Controls/onboarding surfaces resolve live remapped pad names; remaining controller-first help needs equivalent authoritative hint labels, not guessed physical-brand glyphs.

## Guardrails for follow-on agents

- Before edits, refresh `main`, inspect open PRs and recently touched branches. Never claim a feature is unimplemented merely because an older section in `docs/PROJECT-PLAN.md` or `docs/SEMANTIC-SUFFICIENCY.md` says a PR is pending.
- `docs/MODERN-PRODUCT-LAYER.md`, `docs/MODERN-RESULTS-NAVIGATION.md`, `docs/MODERN-TOUR-OVERVIEW.md`, `docs/MODERN-FRONTEND-OPTIONS.md` and `docs/MODERN-FRONTEND-CONTROLS.md` own the respective product contracts. This page summarizes status only.
- Maintain Authentic inertness, host input-release suppression, authoritative stock guest state and profile-local persistence. Native acceptance must assert the actual playable route, not merely an overlay's `OPENED` diagnostic.
- Finished Windows x64 player-facing routes must pass the shared native acceptance, onboarding/practice acceptance, UI evidence, unit suite and Authentic/widescreen gates as applicable.

