# Output Resolution Product Contract

This document records the accepted ownership and behavior for Modern-mode output
resolution, including the completed user-facing Options/runtime integration.
It keeps platform, refresh-rate and monitor-change policy explicit so later video
settings do not reopen this decision.

It does **not** redefine logical SNES geometry, Widescreen scene composition,
HD asset resolution, internal render scale or authoritative guest timing.

## Current implementation layers

The resolution stack is intentionally split into four independently tested
layers:

1. **Desktop capability boundary**
   - SNESRecomp exposes normalized active-monitor output modes through
     `SnesDesktopOutputMode { width, height, refresh_millihz }`.
   - SDL2 and SDL3 enumeration/application differences remain framework-owned.
   - The setter accepts only an exact enumerated mode.
   - Native acceptance run `37169879696` proved a non-empty active-monitor
     catalog, valid desktop/native and first-mode descriptors, exact-mode
     application, rejection of an impossible descriptor and rejection of an
     out-of-range query.
   - The same branch passed the pinned-framework SDL2 and SDL3 network-island
     builds.

2. **Semantic resolution catalog**
   - Product code represents resolution as either:
     - `Native`, or
     - explicit `width × height`.
   - Raw monitor modes are deduplicated by dimensions. Refresh variants do not
     become duplicate resolution rows.
   - Explicit choices are sorted deterministically by pixel area, then width,
     then height.
   - `Native` remains a semantic first choice even when the monitor's native
     dimensions also appear as an explicit resolution.

3. **Host-state persistence**
   - Host-state schema v6 stores:
     - `output_resolution=native`, or
     - `output_resolution=WIDTHxHEIGHT`.
   - Versions 1 through 5 remain readable and conservatively migrate missing
     output resolution to `Native`.
   - The existing desktop state filename remains unchanged so migration is
     in-place.
   - Final rebased acceptance for the v6 slice:
     - project unit tests `37175077191`;
     - Restart/SRAM acceptance `37175077186`;
     - full native product smoke `37175062942`.
   - The native smoke proves schema-v6 save/reload while all existing Modern
     settings and Authentic-mode inertness remain green.

4. **Runtime apply policy**
   - Windowed: output-mode application is not applicable.
   - Borderless fullscreen: output-mode application is not applicable.
     Borderless remains desktop-native.
   - True Fullscreen: the semantic resolution is resolved to one concrete
     enumerated host mode, then handed to the platform adapter.
   - Outcomes are explicit:
     - `NotApplicable`;
     - `Applied`;
     - `Unsupported`;
     - `HostRejected`.
   - A missing callback is a host rejection, not success.
   - This distinction exists so live settings can use the same
     apply → persist → rollback discipline as Display Mode, VSync and
     Presentation FPS.

## Resolution and refresh are separate settings

Output resolution is **not** a refresh-rate selector.

For a requested width × height, true Fullscreen prefers the supported mode whose
refresh is closest to the monitor's current desktop/native refresh. An exact
native refresh wins when available. Ties prefer the higher refresh.

This rule avoids an output-resolution row silently changing the user's refresh
policy. Presentation FPS remains separately host-owned, and VSync remains
separately host-owned.

The guest simulation cadence is never derived from any of these values.

## Display-mode interaction

The three display modes retain distinct product semantics:

- **Windowed** uses ordinary desktop window sizing/presentation. Selecting an
  output resolution must not force an exclusive monitor mode.
- **Borderless** uses the desktop-native monitor mode. An explicit saved output
  resolution remains persisted but is not applied while Borderless is active.
- **Fullscreen** is the only display mode that applies a concrete enumerated
  output mode.

Changing Display Mode into Fullscreen therefore requires resolution
reconciliation/application as part of the live candidate. Leaving Fullscreen
does not need to apply another exclusive mode.

This is separate from Widescreen logical-view policy and separate from internal
render scale.

## Monitor-change recovery

A persisted explicit resolution may disappear when a laptop is docked,
undocked, moved to another monitor or resumed into a changed display topology.

The current-monitor catalog therefore owns the **effective** selection:

- if the persisted explicit dimensions still exist, keep them;
- if they no longer exist, normalize the effective selection to `Native`;
- do not silently rewrite persistence merely because the monitor changed;
- cycling from a stale persisted choice begins from `Native`;
- an empty/invalid catalog also yields `Native` as the safe semantic
  selection.

This separates a durable preference from a temporary monitor capability.

## User-facing integration

The Modern-mode row follows this integration contract:

1. Enumerate the active monitor through the normalized SNESRecomp capability
   API.
2. Build the semantic `Native + unique WIDTHxHEIGHT` catalog.
3. Reconcile the persisted value against that catalog for the effective row.
4. Add one shared keyboard/controller Options row for Output Resolution.
5. On a proposed change:
   - build a candidate host state;
   - if Display Mode is true Fullscreen, resolve and apply its concrete mode;
   - if Windowed or Borderless, treat resolution application as not applicable;
   - save the candidate host state;
   - on save failure, restore the previous effective Fullscreen mode;
   - commit the candidate in memory only after live apply and persistence
     succeed.
6. If Display Mode is changed into true Fullscreen, apply the current effective
   resolution as part of that candidate transition.
7. Authentic mode must not enumerate/apply Modern resolution policy as a
   product setting and must not load Modern host state.

Native product smoke run `37179257856` closes the user-facing integration:
the generated Modern host selected an explicit resolution from the live Xvfb
monitor catalog, persisted schema v6, reloaded and reapplied it in a fresh
process, preserved Authentic inertness, and passed the forced persistence-failure
case in which the live candidate mode was rolled back and the state file remained
byte-identical. Presentation-FPS cadence, Restart/SRAM, Exit-to-Frontend and the
other native product acceptance steps remained green in the same run.

The native acceptance should prove at minimum:

- the row is derived from the actual active-monitor catalog rather than a
  hard-coded resolution list;
- one enumerated explicit resolution can be selected and persisted;
- a fresh process reloads the semantic dimensions;
- true Fullscreen applies one exact supported host mode;
- Borderless remains desktop-native;
- unsupported/stale dimensions recover effectively to Native;
- save failure rolls the live mode back;
- Authentic mode remains inert;
- Restart/SRAM and Presentation FPS cadence acceptance remain green.

## Out of scope

This contract does not decide or implement:

- internal HD render scale;
- arbitrary desktop window-size presets;
- logical SNES output geometry or pixel-aspect ratio;
- Widescreen viewport/scene composition;
- HD asset source resolution;
- graphics packs or post-processing;
- variable-rate guest simulation.

Those are independent presentation/product decisions and must not be collapsed
into Output Resolution.
