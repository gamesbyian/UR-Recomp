# Modern frontend visual-fidelity contract

## Screen system design companion

The companion [`MODERN-FRONTEND-MASTER-DESIGN.md`](MODERN-FRONTEND-MASTER-DESIGN.md) details the proposed screen hierarchy, reusable menu-component grammar, contextual layouts, controller/focus and modal rules, and visual implementation sequence. This document remains the authoritative *quality and source-fidelity gate*: stock screenshot/SFX evidence must determine actual tokens and animation decisions, and a tidy new component library alone does not satisfy stock-family visual acceptance. Check responsive 4:3/16:9, original regional identity, packaged-native captures, and Authentic inertness.

Status: **required final-product presentation; current host-drawn black panels are provisional functional scaffolding**.

This document clarifies the presentation acceptance requirement already established in `PROJECT-PLAN.md` and the stock menu evidence in `UI-STATE-MAP.md`, `analysis/generated/menu-visual-language.json` and `analysis/generated/menu-sfx-ids.json`. It does not create a new gameplay/menu router, require changing stock ROM assets, or authorize writing guest state.

## Product intent

The finished Modern Windows frontend must look and behave like an evolution of **Uniracers**, not a debug console laid over the game. Keep the original logo, signature menu typography and colour language, backgrounds, dimensional/moving selection treatment, transition character and UI sounds recognizable. Modern navigation may reorganize choices, but its rendered presentation should belong to the same visual family.

The present black rectangular overlays with monospaced white labels, including **Welcome/Help**, **Quick Practice**, **Tour Progress** and other host-owned panels, are useful to prove input routing and product state. Their existence does **not** satisfy final visual acceptance. Do not describe these as production-polished, or infer that a functionally passing native smoke constitutes art-direction completion.

## Rendering contract

- Retain **Authentic** stock frontend and original menus as regression/reference behaviour. Do not restyle Authentic or alter guest simulation, SRAM semantics, timing, or historical menu assets for Modern polish.
- Treat host-owned UI as a presentation layer over the accepted Modern product models and input policies. Reuse settled semantic copy/navigation/selection authority; do not duplicate course, tour, profile or pause logic in rendering.
- Derive Modern backgrounds, title treatments, lettering, contrast, cursor/highlight motion, framing, transitions and sound feedback from the measured stock visual-language evidence. Literal pixel-for-pixel reproduction is optional for new surfaces; clear family resemblance is mandatory. **Layouts are not frozen at cartridge-era positions or sizes:** widescreen, high-density artwork and new Modern features may justify moving, regrouping, resizing, rebalancing or expanding UI elements, including stock-derived elements in Modern mode. Preserve visual grammar and hierarchy rather than historical coordinates.
- Design coherent screens for Quick Practice, Tour Progress, Help/Onboarding, Pause, Options, Controls, Records/Local Runs, results, racer/profile setup, and Modern root navigation. Do not merely wrap the existing debug text in ornate borders.
- Preserve responsiveness to keyboard and controller, readable text, selection focus, safe areas, 4:3 and widescreen composition, high-DPI/internal scale, and accessibility preferences. Avoid obscuring critical stock information. Original indicators remain visible where relevant.
- A functional prototype may retain temporary monochrome panels while the underlying routes are under development, but **release readiness requires an intentional finished visual treatment**. No automatic declaration of completion from type/state/route tests alone.

## Art-direction decision rule

Judge changes by a counterfactual design test: **Would this plausibly look like a thoughtful evolution the original game's designers might have made if given a wider canvas, higher-resolution assets and modern interface requirements?** This is a design-review heuristic, not a claim to know the developers' intentions.

- Prefer extending the existing typographic proportions, bright colour relationships, dimensional treatments, selection cues, graphic motifs, background rhythms and playful kinetic character over transplanting generic desktop UI widgets.
- Use extra horizontal space purposefully for previews, tour/track context, records, status, selection detail and other Modern additions; redistribute weight and spacing instead of simply stretching or centering a narrow SNES panel.
- Scale or reorganize interface elements to preserve readable hierarchy at modern display sizes. A larger canvas does not require uniform enlargement, and an expanded information hierarchy need not use more screens.
- Preserve recognizability and original indicator semantics, but allow their **placement, size and grouping** to change in Modern presentation when this improves composition or makes room for new information. Do not stretch stock raster art indiscriminately; use appropriate high-resolution reconstruction where available.
- Keep layout policy responsive to aspect ratio and density, not hard-coded to one screenshot. At 4:3 and 16:9, the composition may differ while remaining identifiably the same design system.
- Explain significant departures in visual review by pointing to original design principles and the practical modern constraint or feature they solve. Reject novelty for its own sake and strict 1994 coordinate matching as competing blanket rules.

## Acceptance evidence

For each Modern surface, retain screenshots at representative states (normal, selection moved, confirmation/cancel where applicable) from the **packaged Windows executable**, not only a standalone mockup. Review against the stock menu reference for typography, palette, hierarchy, selected-state animation, frame/background treatment and sound transitions; assess whether deliberate layout/scale changes suit the wider/higher-resolution presentation rather than treating changed coordinates as regressions. Exercise keyboard/controller parity, 4:3 and 16:9, 1x and higher render density where supported, and Authentic mode regression. Capture material differences and exceptions with explicit approval, rather than silently lowering this bar.

**Release gate:** the black-on-black/white-text engineering panel aesthetic is not the accepted final treatment for player-facing Modern menus. Any surface still using it is tracked as presentation debt, even when fully functional. This is a visual/product gate, not a claim that current functional smoke tests are failing.
