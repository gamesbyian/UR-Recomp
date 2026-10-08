# Modern racer cosmetics and contributor crown Easter egg

Status: **post-baseline planned feature**, architecture specification only (2026-10-08). No cosmetics renderer, cosmetic pose registry, persistence field or crown artwork is claimed to exist. Windows x64 shipping fidelity, gameplay, frontend and HD coverage remain higher priority.

## Product intent

Provide optional, purely visual personalisation of modern racer identity: hats/crowns, scarves/ribbons, wheel decorations, auras, wakes/trails and stunt-reactive particles. Original named/color-coded unicycles remain available unchanged as presets. Cosmetic changes cannot influence gameplay, racer collision, acceleration, stunt recognition, AI, timers, RNG, course state, records, medals or the authoritative guest. Authentic mode remains completely inert. Modern with cosmetics disabled must reproduce its unadorned presentation.

### Named contributor crown

When a **modern racer's entered name contains** any of the following exact ASCII substrings, under ASCII case-insensitive comparison, automatically display a small, jaunty, tilted **golden crown**:

- `halamantariel`
- `dessyreqt`
- `nitrodon`

Examples that trigger: `The Real Halamantariel`, `DESSYREQT`, `Sir Nitrodon III`. Nonmatching prefixes, approximate spellings and confusables do not trigger; match substrings rather than token boundaries. Evaluate after the accepted racer-name input has been normalized through the existing name-validation/identity path; do not silently change what the name editor accepts. No announcement is required. This reward is a **derived appearance rule**, not a persisted grant and not an unlock. Renaming to a nonmatching value immediately removes it; renaming back restores it. Do not consume the player's ordinary headwear selection: resolve a separate forced honorary head-layer appearance, with an explicit deterministic rule to suppress or layer conflicting ordinary hats while the crown is active. Never write into stock SRAM for the crown and never conflate the crown with the preexisting stock forbidden-name / **COOL NAME!** Easter egg.

An appearance record may persist normal choices (e.g. `head`, `scarf`, `wheel`, `aura`, `trail`), but **must not persist the derived crown boolean as authority**. Re-evaluate from racer name on load, edit, profile activation, and racer selection. If content is missing, show the standard rider without disrupting player selection or saves. Show the crown on named AI/guest riders only if a deliberate later policy opts in; initial requirement is player-entered modern racer names.

## Code seams currently present

- `native/presentation/racer_guest_snapshot.hpp`: read-only P1/P2 semantic frame and composition words, including `0x0FE9/0x0FEB` primary and `0x0D3F/0x0D41` companion words.
- `native/presentation/racer_replacement_selector.hpp`: `RacerRegistration`, `RacerAnchor2`, semantic pivot, wheel/contact anchor, composition guards, and `transform_racer_anchor()`. These do **not** presently describe all cosmetic attachment poses.
- `native/presentation/racer_oam_placement.hpp`: PPU/OAM placement, flips, 256-line Y wrapping, split viewport and overlap rules.
- `native/presentation/racer_hd_presenter.cpp`: optional host-owned raster replacement with guarded sprite removal and 1x–4x density. Current authored replacement capture supports 256×224, not widened 342×224; missing registrations fall back to stock. Do **not** attach cosmetic drawing to successful HD replacement selection alone.
- `native/product/` and `docs/MODERN-PRODUCT-LAYER.md`: platform-neutral profile/racer identity and separately versioned host persistence; no guest SRAM ownership for appearance.

See `docs/knowledge/rendering-camera-and-oam.md` for the scanline-112 split and OAM slots 96–99. The framebuffer is not a general per-object depth map. A full-screen topmost accessory overlay would be incorrect around racers and foreground track objects.

## Proposed implementation boundaries

1. Add a **read-only pose attachment registry** keyed by validated racer composition/semantic frame and player, with seat-top, rear seat/scarf point, fork, wheel hub and wheel/contact anchors, and orientation/depth metadata. Recover each anchor from measured sprite geometry; don't assume H/V flips alone recover arbitrary animated rotations. Explicitly mark unmapped frames unknown; fail closed to no attachment rather than guess. Preserve existing semantic pivot/contact provenance.
2. Add a host-only cosmetic presentation compositor, independent of HD asset availability and independent of authoritative guest mutation. It consumes validated read-only guest snapshots, OAM placement, camera/viewport projection and appearance configuration. Preserve Original/Remastered/Reimagined mode expectations, 1×–4× internal scale, original 256×224 and validated widened view geometry. Do not strip guest OBJ pixels unless a correctly layered replacement is guaranteed to draw.
3. Resolve correct ordering and clipping relative to P1/P2 sprites, other OBJ/background priority, and scanline 112. Take care with wrapped OBJ Y, OAM slot priority, widened materializer and the experimentally guarded P1-only HD path. For unknown depth/coverage, preserve Original and omit the unsupported cosmetic part rather than draw through an occluder.
4. Animate scarves, trails, auras and particles from authoritative simulation-frame samples, per-racer identity and presentation-only history. Presentation FPS/interpolation never increments cosmetic simulation or feeds the original game. Pause freezes effect clocks; restart/replay/switching racers resets or deterministically reconstructs history as appropriate. Bound history and particle counts. Optional reduced-flashing settings must govern intense effects when implemented.
5. Persist normal cosmetic selections with an additive, bounded, versioned modern racer appearance schema behind platform-neutral storage. Keep profile identity separate from racer identity; original SRAM and guest name slots are not cosmetic stores. Read-only recordings remain valid without packs. An optional appearance snapshot in replay metadata must be non-authoritative, fail closed and never influence deterministic run/ghost validity.
6. Implement an independently testable pure `honorary_crown_for_name(name)` policy in modern racer identity/presentation configuration, called at the right accepted-name boundary, and keep honorary crown rendering separate from an ordinary optional hat slot.

Suggested code ownership: presentation-only `racer_cosmetic_pose.*`, `racer_cosmetic_presenter.*`, `racer_cosmetic_effects.*` (new files); independently reviewed racer-name policy in product code; integration with existing profile serialization and frontend only through their current owners. These filenames are proposals, not existing APIs.

## Delivery and acceptance sequence

**Phase 0: policy and fixtures.** Pure name-matching tests for lower/upper/mixed case, substring forms, renamed-to-nonmatching behavior, false positives, empty/max-length inputs and existing forbidden-name Easter egg independence. Define appearance precedence and unsupported content fallback.

**Phase 1: measured pose pilot.** Extract and validate seat, wheel and rear attachment anchors for the most common original/HD poses; include an upside-down flip and transition. Provide visual/native snapshots, not just synthetic geometry tests.

**Phase 2: three visible proofs.** A tilted gold crown, wheel glow and moving ribbon/trail, each behind an opt-in Modern cosmetic flag; ensure accessories attach, flip, wrap and freeze correctly. Crown uses the pure name policy.

**Phase 3: compatibility.** Test stock and HD fallbacks across 1P/2P, 256×224/widened fields, split seam, overlapping racers, foreground occlusion, 1×–4×, replay/restored run and high presentation FPS. Unsupported intersections must fail closed without corrupting stock sprites.

**Phase 4: player experience.** Independent user-selected cosmetic slots, profile/racer persistence, renderer-mode asset variants, optional unlock catalog and accessibility choices. Integrate with existing racer customization frontend rather than creating a second identity editor.

**Non-negotiable parity gate:** For identical deterministic inputs and race contexts, toggling all cosmetic features must preserve authoritative WRAM, PPU/OAM/VRAM state (except host presentation buffers, which are out of guest state), gameplay outputs, race completion and persisted deterministic run hashes exactly. Name edits or appearance changes cannot alter authoritative timing or course results. Test cold-process save/reload and fail-closed missing/invalid cosmetic packs.

## Priority

This is a post-baseline optional feature. Do not divert active CI, physics, graphics fidelity/HD-family coverage, widescreen semantics, packaging, replay, tournament or frontend owners without coordination. The pure name-policy tests and pose investigation are safe independent groundwork; full render integration follows a stable authentic/HD presentation acceptance gate.
