# Modern Product Layer

This document owns intentional modern product policy and the host/runtime boundary that implements it. It does not redefine stock fidelity. Historical behavior remains documented by the existing UI, progression, SRAM and semantic evidence surfaces.

## First seam: host administrative state

The first project-owned modern seam is deliberately small: independent host-side profile selection and settings.

The implementation lives in `native/product/host_product_state.{hpp,cpp}`. Its persisted envelope contains only:

- an optional opaque host profile ID;
- vibration enabled/disabled;
- pause-on-focus-loss enabled/disabled.

This state is administrative host state. It has no WRAM addresses, SRAM layout, racer slots, medal values, league state, course state, timers, physics state or other cartridge-era semantics.

The current codec is intentionally dependency-free and deterministic. Version 1 writes one canonical byte representation and rejects duplicate, unknown or malformed fields. The platform-specific file location and write strategy are left to the eventual shipping host shell.

## Authentic versus Modern policy

`ExecutionMode::Authentic` is the regression/reference policy. In this mode:

- host profiles do not participate in game behavior;
- host settings do not override stock behavior;
- modern administrative commands are disabled;
- the original guest frontend/progression/SRAM path remains the behavior under test.

`ExecutionMode::Modern` enables host-owned product facilities. Enabling it does not grant permission to mutate authoritative race simulation. Modern features must cross an explicit runtime adapter whose effects are independently testable.

The host-state store may physically exist while Authentic mode is active, but its contents must be observationally inert with respect to guest behavior.

## Ownership rules

Keep these domains separate:

| Domain | Owner | Examples |
| --- | --- | --- |
| Race simulation | original/recompiled guest | physics, collision, stunt state, RNG, race timing |
| Stock persistence | original/recompiled guest | 8 KiB SRAM, medal matrix, derived tiers, checksum |
| Modern administration | host product layer | profile identity, settings, future save catalog and UI policy |
| Presentation | host/runtime presentation layer | window state, output scale, future overlays and graphics mode |
| Session control | future explicit runtime adapter | pause/resume/restart/exit requests |

A modern profile is not a renamed unicycle/save slot. Racer identity and progression can later be associated with a profile by higher-level product policy, but the storage primitives remain independent.

## Extension points

Do not add these systems to `HostProductState` merely because they are planned. Add narrow interfaces when there is a concrete runtime consumer:

- **pause/restart:** a session-control adapter that can suspend host execution or re-establish a deterministic guest starting state without ad-hoc WRAM edits;
- **autosave/resume:** a coordinator that owns host save metadata while preserving guest SRAM as guest data;
- **records/ghosts:** append-only run artifacts keyed by profile and course identity, sourced from observed authoritative race state;
- **racer identity:** product data associated with a profile, explicitly separate from the original save-slot/unicycle coupling;
- **settings:** typed host options whose ownership and Authentic-mode fallback are explicit.

Network transport, accounts, cloud persistence and hosted leaderboards remain outside this architecture.

## Validation contract

Every host-state schema or transition must have deterministic tests. At minimum:

1. default state has one exact serialized representation;
2. encode → decode → encode is byte-stable;
3. malformed, duplicate and unknown fields fail closed;
4. Authentic policy exposes no host profile/settings/modern-command capability;
5. no new host schema field may silently acquire guest simulation or cartridge-save authority.

The current unit test is compiled and executed from `tests/unit/test_host_product_state_cpp.py`, so the contract participates in the lightweight project tooling test surface without requiring the external SNESRecomp build.

## Fidelity versus product policy

The distinction is explicit:

- reproducing the original frontend, racer/save-slot coupling and SRAM progression is a **fidelity** concern;
- choosing independent profiles, host settings, autosave UX, pause/restart UX, records and ghosts is **modern product policy**;
- a product-policy feature is acceptable only while the Authentic path stays reproducible and authoritative race behavior remains unchanged.

PR #213 closed the stock gameplay-authored progression/save-load acceptance gap. That evidence is the reason this layer can now treat SRAM as a proven guest-owned substrate rather than commandeering it as a modern profile store.
