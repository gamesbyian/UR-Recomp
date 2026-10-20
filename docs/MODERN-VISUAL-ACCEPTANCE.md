# Independent Modern visual acceptance: native title and menus

**Status 2026-10-20: HOLD / evidence infrastructure, not visual sign-off.**
Owner: separate QA/visual-integration lane. The real Modern/Baldosa five-destination native root exists; the new intentional title, shared visual tokens, full destination skin and animated hero are simultaneous owner work. This review is based on `main` **`2cfe3350325f489d5db8347d90a5fecbc1526f4a`**, not a subsequently merged combined visual build. No new native executable was built or run while authoring this review. **0/25 newly source-captured cases; 0 passed final visual approvals.** Do not change `docs/RELEASE-QUALITY-LEDGER.json`.

The quality authority is [MODERN-UI-VISUAL-FIDELITY.md](MODERN-UI-VISUAL-FIDELITY.md); navigation and animation intent are in [MODERN-FRONTEND-MASTER-DESIGN.md](MODERN-FRONTEND-MASTER-DESIGN.md). Functional host limitations and the actual player path are in [MODERN-FRONTEND-SHIPPING-STATUS.md](MODERN-FRONTEND-SHIPPING-STATUS.md), [MODERN-NATIVE-PLAYER-JOURNEY.md](MODERN-NATIVE-PLAYER-JOURNEY.md), [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md) and [WORK-QUEUE.md](WORK-QUEUE.md). This is a per-candidate visual evidence **consumer**, never another frontend, renderer, route authority or release-gate owner.

## Three-project reuse preflight

Read `tools/select_three_project_reuse.py` and its grounded inputs `analysis/three-project-reuse-opportunities.json`, `analysis/data/three-project-apparatus-capability-matrix-20261010.json`, `analysis/agent-context-lanes.json`. Select the `release-qa` lane with `--include-conditional` for this work; `modern-product` is a relevant secondary owner reference. The resulting applicable existing choices are **candidate-evidence-envelope**, **route-input-identity** and **agent-work-packets**. First-divergence and effective-address pilots are irrelevant until an actual guest-bound difference demands them. Do not adopt new executable upstream code for screenshot auditing.

Actual pinned source examples inspected:

- **UR**: `native/product/modern_root_overlay_presenter.hpp` is the shared state-fed painter; `native/product/modern_root_physical_edges.hpp` already separates keyboard and P1 edge latches; `native/product/modern_overlay_composition.hpp`, `tools/evidence_contract.py` and hosted native `baldosa_native_*_probe.py` already supply layout/input/evidence infrastructure. Keep them as sole owners; this change only verifies captured output.
- **Baldosa USA**, pinned `10b864b9d14a7b7416dd909eb7b054c88faef101`: `src/main.c` delegates its SDL/window/controller presenter to SNESRecomp's existing host. Reuse its actual native host and controller seams rather than importing or writing another one.
- **Malmazuke PAL**, pinned `42d444594641d23f5d3c15da7b7c454bb5180e43`: `src/app/frontend.cpp` represents pad/keyboard state separately; it is useful for an independent conceptual input-review comparison, **not** a USA pixel oracle or shipping UI code.

Disposition: **reuse existing host and source-native smoke scripts; add one narrow, dependency-free, fail-closed capture receipt checker.** No imported executable/source or third-party art is added, no guest timing, state, records, renderer or control mapping is changed.

## Native capture matrix, currently pending

Machine-readable exact cases are in [`analysis/modern-visual-acceptance-matrix.json`](../analysis/modern-visual-acceptance-matrix.json). Every case requires a **real final-presented native output PNG**, the **same process's route log**, a **retained exact executable**, case-specific route metadata, and a correct full-file SHA256. The PNG's actual dimensions must be the requested final output size; a 256x224 or 342x224 logical raster relabeled `1920x1080` fails.

| Visual integration surface | Case identifiers | Independent finding / remaining discriminator |
| --- | --- | --- |
| Modern title, animated entry and reduced motion | `title-wide-1080`, `title-wide-keyboard`, `title-compact-43`, `title-reduced-motion` | **Uncaptured.** Verify stock-derived title, transition and stable reduced-motion frame against source art. |
| Root dimensions, 1x/higher density and focus | `root-wide-720`, `root-wide-1080`, `root-wide-4k-virtual`, `root-43-768`, `root-43-480`, `root-moved-selection`, `root-keyboard`, `root-disabled` | **Uncaptured in redesign.** Check actual selected art, safe-area typography and stale-profile lock; virtual UHD geometry is *not* physical 4K. |
| Profile creation, profile switch, P2 seat | `profile-first-run`, `profile-switch-existing`, `multiplayer-p2-owner` | **Uncaptured in redesign.** Reuse existing source-run/switch evidence and prove feedback, nested Back and two controller owners on same candidate. |
| Practice, Options and Records | `practice-locked`, `options-available`, `options-refused`, `records-empty`, `records-earned-1p`, `records-earned-2p` | **Uncaptured in redesign.** Distinguish disabled state from missing capabilities; inspect earned 1P/2P record bytes separately from screenshot. |
| Transition, Authentic isolation, focus loss | `transition-back-release`, `authentic-title-stock`, `authentic-stock-wide`, `focus-loss-modal` | **Uncaptured.** Exact same-source stock screenshots/guest input observation and modal release proof remain required. |

Older hosted Windows journeys demonstrate controller-semantic functionality of the *then-current* engineering UI, not this redesign's visual accuracy. The October 19 [independent Windows candidate audit](QA-WINDOWS-INDEPENDENT-OWNER-CANDIDATE-MATRIX-20261019.md) confirms zero real SDL joystick devices and dummy audio for hosted owner evidence. It cannot establish human-operated controller usability, audible cues, source likeness, physical display, 4K/PAR, or the new title's appearance. No screenshots have been fabricated, and no media/trailer assets are used.

## Capture and independent verification

Capture from a specific **actual Windows packaged Modern/Baldosa binary** (prefer source-once native SDL final-output readback, retaining viewport dimensions and sampled-frame/route timing). For each case:

1. Start the **exact executable** with the legal owner-supplied ROM, private clean user-data root and a deterministic controller/keyboard route. Never archive the ROM, private profile contents, real names or another person's data.
2. Preserve the entire process stdout/stderr and input route, exact exit status, tested Git commit, native executable hash, output geometry, rendering density, guest frame, host frame, mode, keyboard/gamepad semantic seat and selected/cancelled state. Record the actual process, not a prior process's log. Pad injection on CI remains **semantic**, not physical device certification.
3. Extract an unaltered final-presented screenshot to PNG (RGB/RGBA 8-bit, non-interlaced). Keep a sequence or brief native capture for transitions and reduced-motion comparisons. Do not crop, upscale, retouch, recompose, or generate the evidence image.
4. Add a JSON manifest beside these files with `schema_version: 1`, the full 40-character lowercase `source_sha`, `capture_runtime: "native-sdl-final-output"`, `exe_sha256`, relative `executable`, and `captures`. Each capture gives `case_id`, `screen`, `mode`, `input`, `state`, `source_sha`, `exe_sha256`, `driver` (`native-semantic-pad` or `native-keyboard`), `png`, `png_sha256`, `route_log`, `route_log_sha256` and nonempty `route_markers` containing **actual** runtime log substrings, not expected invented events.
5. Audit extracted bytes from an independent reader:

```sh
python3 -m unittest -v tests.unit.test_check_modern_visual_capture_bundle
python3 tools/check_modern_visual_capture_bundle.py /path/to/evidence/manifest.json \
  --require-complete --json-out /path/to/evidence/structural-audit.json
```

Incomplete inventories can be assessed without `--require-complete`, but are clearly reported as incomplete. An invalid hash, path traversal/symlink, duplicate case, fake/mismatched image dimensions, mode/seat confusion, unsupported capture type or missing log marker is fatal. The test suite synthesizes cases only to test **rejection logic** and earns no native evidence.

**Scope of the tool:** byte integrity of cited files, declared source/executable consistency *within the bundle*, PNG-envelope CRCs and dimensions, route-log substring presence, and inventory completeness. It cannot prove that an executable actually emitted those pixels, that an image is visually correct or that a cited marker reflects the claimed button event. Those require independent execution/frame witnesses and source comparison. Its response therefore permanently contains `visual_approved: false`, `hardware_approved: false`, `authentic_isolation_approved: false`, `release_gate_credit: 0`; no automated path to human approval exists. An executable SHA binding still needs the recorded build SHA and artifact source chain independently checked, not a producer claim alone.

## Adversarial visual review per accepted *candidate*

After structurally verified captures exist, compare **real PNGs**, sequential frames and original stock title/menu reference, assessing original-derived glyphs, approximate font strokes/kerning, semantic color ramps, selection feedback, logo proportions, racer silhouette/poses, safe area and all status strings. Inspect contrasting bright/dark backgrounds and the worst text length; check a whole text glyph envelope against the image bounds, not merely that the panel rect fits. Run root moved-selection, disabled stale-profile, locked Practice, empty and populated Records, two P1/P2 profiles, controller ownership, held A/Back and focus-loss cancellation. Support keyboard navigation, remapped prompts and reduced motion by **observed** independent routes.

Keep functional, visual and release decisions disjoint:

- **Functional / structural**: native execution with known-exact binary and source, observed button edges, route logs, screenshot dimensions and navigation assertions.
- **Visual review**: explicit independent stock-comparison decision at 4:3 and 16:9 across outputs and densities; original-derived art approval from the project owner where required.
- **Physical and human**: actual Windows display/TV safe areas, 4K/PAR, two independent controllers, sound and uncoached navigation, on exact packaged hash.
- **Authentic isolation**: paired source-aligned stock mode comparisons and guest-state/CRC authority; similar screenshots or unused Modern handlers alone cannot prove it.

**Stop/merge criterion for this lane:** independent QA code and regression checks can merge without claiming the redesign accepted. Final visual/physical approval remains a separate documented hold until verified final PR heads, native captures, human design review and actual hardware results exist. Visual agents own their art/title/menu animation/source; this lane owns only audit cases, evidence verification and cross-PR integration review. If another visual agent changes a case schema, resolve by PR discussion instead of making competing route/painter edits. Do not merge the new visual design merely because this structural checker goes green.
