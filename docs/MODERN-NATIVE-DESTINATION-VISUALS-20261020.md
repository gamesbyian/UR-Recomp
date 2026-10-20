# Native Modern destination presentation | 2026-10-20

Status: **implementation candidate; human visual approval and packaged native screenshots pending.** This is a destination-composition note, not a release-gate change.

## Scope and authority

The five canonical Modern root destinations remain **Play, Practice, Multiplayer, Records, Options** in their established order. The root/title and universal typography/layout primitives belong to the sibling visual workstreams. This lane owns the **opened destination compositions** and the stock-backed profile child surfaces in `native/product/modern_native_destination_presenter.hpp`. It does not own the Modern route state machine, product storage, Baldosa guest, splash/title, Authentic screens or the release ledger.

Play currently confirms directly into the authentic stock 1P route. There is no fake standalone Play screen to reskin. The Play **root selection and preview** remain with the shared root-shell owner, with the gameplay handoff intact. Practice opens the real source-available course picker. Multiplayer opens the two-seat catalog-backed join or the explicit unrecorded-stock-2P consent. Records reads canonical 1P runs/2P matches; Options reads/apply only the existing real host settings. Racer setup uses actual preset/catalog state and next-boot commit semantics.

## Three-project reuse preflight

Source-grounded equivalent of `tools/select_three_project_reuse.py --lane modern-product --include-conditional` performed against live main's `analysis/three-project-reuse-opportunities.json`, capability matrix and lanes, plus `docs/BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md`. Applicable **now** entries: `baldosa-native-core`, `modern-controller-journey`, `candidate-evidence-envelope` and `agent-work-packets`; conditional `framework-delta-porting` is unnecessary. Decision: reuse `ModernRootOverlayView`, `ModernRootOverlayPainter`, original stock BG2 visual-language evidence and the already integrated Baldosa state machine. No other runtime, new menus, invented records, alternate save path or copied upstream UI framework.

## Visual language and composition contract

- The source-verified [stock menu language](../analysis/generated/menu-visual-language.json) supplies the yellow 16-pixel title/black shadow, grey 8-pixel supporting text and ice-blue selected arrow/band. Use the existing palette tokens and host glyph painter. The host glyph implementation still needs a **source-font visual review** and possible handoff to the common design-system owner.
- Destination panels use the native root rectangle: a 138-logical-pixel child body inset by 11 pixels and beginning at root Y+42. Title hierarchy, active row, contextual data, warning/status and Back/Confirm legend remain visible. The renderer clips text by the *actual logical glyph budget*; full timing hundredths must survive narrow Records.
- The pure layout accepts a stock `256x224` raster with a `240x204` root, and the project's PAR-calibrated `342x224` widescreen logical target with an `318x204` root. Do not stretch fonts or invent a 216-line crop. Both preserve a common physical safe-area policy. The **current shipping Baldosa root draw entrypoint remains 256x224 only**; the 342x224 layout is proven as a renderer geometry contract, **not yet integrated into a native widescreen execution/presentation path**. That separately owned integration must provide an actual wider root surface and screenshot before a widescreen acceptance claim.
- Records is explicitly read-only; no new replay or save action. The warning displays lack of history for unbound 2P. Racer switching is marked for next boot, never immediate. Practice exposes original unlocked-tour count and source-route launch status, not speculative courses.
- The new presenter overpaints only the existing child modal **after** the shared `render_modern_root_overlay` draws. It never edits the shared renderer file, root cursor, menu model or guest pixel data outside the overlay. This is the integration seam for the title and shared visual-language agents. Avoid separately modifying the native root presenter for these six child views; coordinate on `ModernRootOverlayView`/palette changes if a shared component API evolves.

## Verification / remaining visual approval

Native ROM-free C++ contract: `tests/native/modern_native_destination_presenter_test.cpp` (all child view states, narrow and actual 342x224 logical-wide geometry, full 1P record time, selected rows, help, 2P confirmations, profile next-launch status, invalid-bounds no-draw). Python compile runner: `tests/unit/test_modern_native_destination_presenter_cpp.py`, including a check that the **real** Baldosa draw entrypoint contains exactly one destination hook and forwards product-owned view fields. These are functional and layout contracts, **not photographic quality or packaged Windows certification**.

Required screenshot evidence still open:
1. Build and boot one immutable Windows native package with the real generated guest; log source commit, compiled executable SHA256, archive SHA256, configuration and output mode. Capture actual Play-selected root, Practice course, both Records pages, selected/adjusted Options, 2P join/unrecorded warning and first/second/switch racer panels. Include selection moved, saved/failed status and pressed/back paths without modifying guest state.
2. Capture the same family in genuine native `342x224` wide logical / `3840x2160` calibrated display output and stock `256x224` fallback once wide root composition is wired. Include 1x and final high-density rendering and note 7:6 PAR.
3. Have the owner compare actual pixels against source title/menu atlas for lettering, palette, cursor, panel/background detail, motion and high contrast. Original-derived typography and composed 16:9 art still require human approval. Capture real P1/P2 pads, pause/Options, cold relaunch and unmodified Authentic output. No QA ledger or art sign-off is granted here.

One owner handoff: integration/title/common visual agents may change the root shell or glyph primitives but must retain the presenter view contract. The next implementer can attach the pure 342x224 destination painter when the wide native overlay entrypoint is genuinely available, then take source-bound screenshots. **No trailer/media work belongs in this lane.**
