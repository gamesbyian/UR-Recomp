# HD Presentation visual-language specification

Status: Phase G design authority. The ordinary-race racer family now has sufficient semantic identity, exact composition guards, geometry anchors, live placement, fail-closed host substitution, and a continuous 16-frame registered temporal window to begin approval-ready asset dossiers. This document remains conservative where material/lighting/detail interpretation is not yet evidence-backed; other presentation families still await equivalent Phase E coverage.

The job is to reconstruct Uniracers' presentation coherently at modern resolution without changing authoritative game behavior or turning every ambiguous source pixel into permission to invent detail.

## Non-negotiable rules

1. Original simulation/state selects presentation state and timing.
2. Original silhouette, pose, contact and composition outrank decorative detail.
3. Replacement art must remain coherent across an animation sequence, not merely attractive frame-by-frame.
4. Where source evidence is ambiguous, retain the ambiguity in the asset dossier until a deliberate design decision is recorded.
5. Authentic stock presentation remains available as fallback and comparison.

## Evidence order

Prefer:

1. original ROM graphics/palette/state identity;
2. deterministic raw framebuffer and isolated layers;
3. neighboring animation states and repeated motifs;
4. documented original-development pipeline/history;
5. independent scaler/display reconstructions as interpretations;
6. external sprite sheets/screenshots as comparison references;
7. newly invented detail only after the above are exhausted.

No single upscaler or model output is evidence of authorial intent by itself.

## Geometry

For moving gameplay art, preserve:

- semantic pivot;
- track/contact point;
- apparent size across frames;
- silhouette envelope;
- relative attachment geometry;
- state-to-state pose identity.

For the unicycle in particular, wheel-ground contact and stable frame-to-frame geometry are release criteria, not polish.

## Racer source-production constraint

The original unicycle imagery was not authored as pixel art from first principles. The project’s developer-history evidence identifies Martin Good as the CG artist responsible for the unicycle renders and records Robbie Graham describing a highly detailed **3D source model rendered down into very small 2D game frames**, with many pedal/wheel phases plus stunt rotation, tilt/stretch and saddle motion. Dedicated Unicycle Compression and A0 plotting tools independently fit that production model.

For **Remastered** racer art, treat this as a strong reconstruction constraint:

- preserve the recovered semantic pose, silhouette envelope, pivot/contact geometry, palette relationships and guest-authored animation cadence;
- reconstruct curves and mechanical forms as coherent high-resolution geometry consistent with a smooth 3D source, rather than reproducing SNES pixel stair-steps as intentional edge design;
- use neighboring registered frames to distinguish persistent model features from downsampling/quantization noise;
- keep wheel, frame, saddle and pedal proportions temporally stable across the sequence;
- do not infer fine material, surface or lighting details merely because the source was 3D. The original high-detail source model is not currently available, so those remain explicit design decisions.

For **Original**, preserve the literal stock raster and its display treatments. **Reimagined** may depart further in surface treatment, but it still inherits the semantic pose/contact/timing contract unless a separate documented product decision says otherwise.

Evidence authority: `docs/original-development/DEVELOPER-TECHNICAL-HISTORY.md`, “Graphics and animation pipeline”.

## Material and lighting

The material model is still partially open, but the faithful Remastered racer now has two resolved presentation rules.

**Lighting space is object-local and baked into the representation.** Stock shading is part of the composed racer raster, and the accepted runtime applies H/V orientation after semantic selection. Faithful Remastered art should therefore carry its lighting/value pattern with the racer and let the same runtime transform mirror it. Do not add world-space or screen-space dynamic relighting to the baseline Remastered racer path; that would make highlights behave differently from the stock asset under flips.

**Edge treatment follows form, not source-pixel stair-steps.** Preserve the strong dark silhouette and internal value boundaries that survive across registered neighboring frames, but reconstruct them on smooth high-resolution contours consistent with the original 3D source-render pipeline. Do not impose a uniform new cartoon outline where the stock sequence does not support one.

The conservative material baseline is now also constrained. This is a synthesis of the ROM-derived dossier, developer testimony about the detailed 3D source model, and official packaging/promotional imagery. Packaging is a secondary appearance reference, not geometry authority.

- **tire:** dark rubber, with broad stable highlights rather than a chrome/mirror response;
- **saddle:** dark vinyl/leather-like surface, again with restrained broad highlights;
- **colored frame:** glossy painted/anodized-metal-like surface carrying the racer color;
- **neutral hardware:** bright neutral metallic hub/fork/pedal hardware;
- **cast/drop shadow:** do not add a new host-authored ground shadow in the faithful Remastered baseline. Track contact is already a recovered geometry constraint and the stock racer has no separate host-space shadow layer;
- **micro-detail:** mechanically plausible source detail is welcome only when it survives normal gameplay scale. Detail that aliases, flickers, changes the recovered silhouette, or disappears incoherently in motion/split-screen must be suppressed. The historical source model reportedly contained detail as fine as screw threads; that is evidence of source-model fidelity, not a requirement that every thread remain visible in the game render.

**Specular/highlight strength is also bounded for the first candidate.** Across the current 14-representation ROM dossier, the colored red/blue body uses a stepped value ramp in which the brightest colored tone is a small accent rather than the dominant fill, while the neutral hardware owns the rare near-white values. Treat that hierarchy as the relative contrast target: use broad baked highlights on the colored frame, keep the brightest colored highlight restrained, allow neutral metal to run substantially brighter, and do not add point sparkle/star glints. The dossier now records each representation's exact opaque RGBA histogram so later candidates can be reviewed against the source tone distribution without guessing.

With that rule, the first-family **visual-language baseline is closed enough to author a real Remastered candidate**. Candidate review may still tune numeric intensities, but it should do so inside these constraints rather than reopening material class, lighting space, edge treatment, shadow, or detail policy.

### First authored review candidate

**Current status note (2026-10-05):** This section intentionally retains the chronological review history. Statements below that individual poses are “not approved shipping art” describe intermediate checkpoints, not the current disposition. The retained 1205–1220 strip is now 10/10 unique poses shipping-art approved through PR #442, with approval bound to exact authored RGBA hashes and the review packet carrying its workflow/artifact/window evidence.


The first actual Remastered racer candidate now exists for exact representation `ordinary-racer-0x0541-p1-sync-reference` (`0541/0540 + 0D0D/0000`, P1 palette `0x06`). It is a 4x-density procedural high-resolution asset using the closed baseline above rather than the generic Scale2x contract placeholder.

Initial native acceptance run `37142692369` proved the authored representation flowed through the real host selector and split-screen presenter at frame 1220 in both top and bottom viewports with `guest_state_unchanged=1`, zero stable WRAM differences, and unchanged Original control hash. That first pilot was mechanically correct but failed the first gameplay-scale motion review: its sampled silhouette occupied `x=21..40, y=8..38` while the stock frame occupies `x=22..39, y=3..38`, and stock/candidate alpha IoU was only about 0.377. Because the registered 1219 -> 1220 stock transition changes only seven source pixels, the pilot's redistributed mass would have read as an avoidable scale/posture pop.

The candidate is therefore **tuned, not redesigned**. The revised authored geometry preserves the recovered contact anchor `x2/y2=61/76`, matches the exact stock gameplay-scale alpha envelope `[22,3]..[39,38]`, reduces the oversized wheel mass, and restores the saddle to the stock upper silhouette band. The established material, lighting, edge, shadow and detail rules are unchanged. Dossier review now measures 220 stock/candidate overlapping logical pixels over a 347-pixel union, alpha IoU `0.6340057637`, with the contact anchor and full envelope exact.

Native acceptance run `37146779451` is green end to end for the tuned candidate, including selector/orientation contracts, Original control, live top/bottom split-screen presentation and no guest-state mutation. Artifact `11283305196` retains the regenerated 16-frame / 14-representation dossier and tuned authored PNG.

Status is **motion-reviewed and accepted as the first-family authored reference candidate, but still not approved shipping art**. Its immediate consequence is a stricter authoring rule for subsequent frames: match recovered gameplay-scale envelope/contact first, then add smooth high-resolution form inside that contract. Do not reopen the already-set material or lighting language merely to make neighboring frames novel.

The first temporal-neighbor application is now also motion-reviewed. Exact frame-1219 representation `ordinary-racer-0x0541-p1-companion-0D2D-reference` keeps the reviewed 1220 wheel/fork/crank/contact/material/lighting solution and changes only the upper saddle profile required by the retained stock difference. Its gameplay-scale envelope exactly matches stock at `[22,2]..[39,38]`, contact remains `[61,76]`, and alpha overlap is 226 pixels over a 349-pixel union (IoU `0.6475644699`). Native run `37150356100` is green through live Original/HD split-screen acceptance with no guest-state mutation; artifact `11283522741` retains the two-authored-representation dossier. This validates the envelope-first rule across an actual adjacent animation transition, not only on the original reference frame. The neighbor remains review art, not approved shipping art.

Frame 1217 P2 `0542` is now motion-reviewed as the next distinct blue-player pose. Retained dossier evidence fixes its stock envelope at `[21,4]..[40,38]`, contact at `[59,76]`, and proves the frames-1215–1216 `057F/0542 + 0D4A/0000` P2 raster is byte-identical to the frame-1217 `0540/0542 + 0D2C/0000` raster. One authored asset therefore covers all three occurrences under separate exact guards. It inherits the reviewed P2 material/lighting language and measures 254 overlapping logical pixels over a 384-pixel union (IoU `0.6614583333`), with 313 candidate opaque pixels versus 325 stock. Native run `37173872885` is green and artifact `11291829520` retains the accepted shared-pose/reuse proof. This remains review art, not shipping-art approval.

The retained P2 `0543` pose is now motion-reviewed. Its two in-window exact contexts, `057D/0543 + 0D48/0000` across frames 1207–1212 and `057E/0543 + 0D49/0000` across frames 1205–1206 and 1213–1214, reconstruct to byte-identical stock art. One authored blue-player asset therefore serves both guards. It matches stock envelope `[20,4]..[40,38]`, bottom span `[26,31]`, contact `[57,76]`, and measures 242 overlapping logical pixels over a 388-pixel union (IoU `0.6237113402`), with 311 candidate opaque pixels versus 319 stock. Native run `37174353366` is green and artifact `11292358727` retains the accepted shared-pose/reuse proof. This remains review art, not shipping-art approval.

The completed 1205–1220 first-family strip now has an accepted authored-motion review contract rather than relying on per-pose approval alone. The promoted frame order covers both P1 and P2 for all 16 frames. At gameplay-centre sampling, every stock-static edge remains authored-static, every stock-dynamic edge remains authored-dynamic, authored bounds/contact remain exact to stock on every frame, and dynamic changed-pixel magnitude stays within the evidence-derived 0.75–2.25× stock band. Run `37174986502` / artifact `11292529288` proves P1 has 9 static + 6 dynamic edges with dynamic ratios `1.133–2.143`, while P2 has 12 static + 3 dynamic edges with ratios `0.961–1.494`; authored contact deltas match stock on every transition. The high P1 endpoint is the deliberately tiny seven-stock-pixel 1219→1220 saddle change. This closes sequence-level motion review for the retained strip while remaining explicitly short of shipping-art approval.

Runtime art review must distinguish source density from displayed density. The first accepted presenter intentionally sampled each 4× candidate back to the stock 64×64 logical footprint; that was sufficient for geometry/motion review but not an HD product claim. PR #364 closes the true-density promotion: stock guest geometry remains unchanged while exact registered replacements are displayed at native 4× density on a host-only 1024×896 surface, with native acceptance proving real within-logical-pixel detail rather than a nearest-scaled 1× composition. This presentation promotion does not itself approve any candidate as shipping art.

Shipping-art review now operates on visual-pose identity rather than raw guard count. The Racer acceptance artifact generates `review/index.html` from the dossier plus pose-equivalence worklist. It presents the 10 byte-distinct poses in the supported 1205–1220 strip once each, with stock 1×, nearest-4× reference, authored 4×, and authored gameplay-footprint views, plus matched-size live Original and true-density split-screen captures. The packet also preserves the exact semantic guards and observed frames behind each pose. Use that packet as the routine human review surface; semantic guard correctness remains enforced independently by the runtime and dossier gates.

The first true-density shipping-art review was recorded in `analysis/data/racer-hd-art-approval.json` from native run `37180202506` / artifact `11295241964` and deliberately held all 10 unique poses at `needs-refinement`. That review drove the subsequent family-wide structural passes rather than pose-specific ornament: saddle attachment/volume, wheel/hub/crank/pedal modeling, retained internal structure and finally the crown/frame junction were refined under the already-closed geometry and motion constraints. PR #442 records the final reviewed state from run `37248763308` / artifact `11319814239`; follow-up acceptance run `37249144430` proves all 10 unique poses `approved`, zero family blockers, zero stale hashes and `shipping_ready=true`. Every alpha mask remains unchanged from the prior accepted strip, so envelopes, recovered contacts, temporal occupancy and byte-identical pose reuse remain intact. `tools/build_racer_hd_shipping_readiness.py` is still fail-closed: approval belongs once to the unique visual pose, is inherited only through exact pose equivalence, and is bound to the exact authored RGBA hash so any future pixel change automatically requires re-review.

The reversed frame-1218 predecessor is now motion-reviewed as the third authored pose. Its stock transition is materially larger than 1219→1220, so the candidate is not a translated copy: wheel, fork, crank and saddle geometry are locally re-fitted while keeping the established object-local lighting and material rules. The sampled candidate exactly matches stock envelope `[23,2]..[40,38]` and contact `[63,76]`; alpha overlap is 270 pixels over a 365-pixel union (IoU `0.7397260274`). Native run `37151331456` is green through live Original/HD split-screen acceptance with no guest-state mutation, and artifact `11284028173` retains the three-authored-representation dossier. This pose is also review art, not approved shipping art.

Frame 1217 proves that authored-art identity must remain separate from synchronized-state identity. Its exact P1 registration `0540/0542 + 0D2C/0000` has a byte-for-byte identical stock raster to frame 1218, with the same envelope and contact, even though the P2 context differs. The presenter and dossier therefore deliberately reuse the reviewed frame-1218 authored asset while retaining a separate exact composition guard. Native run `37151848274` confirms that reuse through live split-screen presentation with no guest-state mutation; artifact `11284007664` retains the four-registration/three-visual-pose dossier state. This is accepted context-safe reuse, not a fourth authored pose and not shipping-art approval.

The next actual visual change, repeated frames 1215–1216 exact P1 `057F/0542 + 0D4A/0000`, now has one authored 4x Remastered pose shared by both temporal occurrences. It deliberately continues the reviewed rubber/saddle, glossy colored-frame, bright neutral-hardware, object-local lighting and no-outline language rather than inventing a new treatment. Gameplay-scale sampling is the acceptance surface: candidate and stock envelopes are both `[22,2]..[41,38]`, and the authored bottom span `31..34` preserves recovered contact `[65,76]`. Retained review measures 264 overlapping logical pixels over a 384-pixel union (IoU `0.6875`). Native run `37159887643` is green through live top/bottom split-screen substitution with no guest-state mutation, and artifact `11286898413` retains the five-registration/four-visual-pose dossier state. This pose is motion-reviewed, not approved shipping art.

The immediately preceding repeated P1 state `057E/0543 + 0D49/0000` at frames 1213–1214 (also 1205–1206) is now motion-reviewed as the next distinct stock pose. Its authored asset inherits the accepted 057F material/lighting treatment and expands only the evidence-backed geometry to stock envelope `[21,2]..[42,38]` with contact `[67,76]`. Gameplay-scale review measures 251 overlapping logical pixels over a 405-pixel union (IoU `0.6197530864`), with 331 candidate opaque pixels versus 325 stock. Native run `37163141373` is green through live split-screen presentation and guest-state invariants; artifact `11288098806` retains the dossier. This remains review art, not shipping-art approval.

The six-frame P1 state immediately before that, `057D/0543 + 0D48/0000` at frames 1207–1212, is now motion-reviewed as the next distinct retained pose. Its authored asset continues the same reviewed material and object-local lighting language while fitting stock envelope `[21,3]..[43,38]` and contact `[69,76]`. Gameplay-scale review measures 246 overlapping logical pixels over a 397-pixel union (IoU `0.6196473552`), with 322 candidate opaque pixels versus 321 stock. Native run `37164968261` is green through live split-screen presentation and guest-state invariants; artifact `11289251993` retains the dossier. This remains review art, not shipping-art approval.

With the P1 1205–1220 strip now saturated, the next product-facing gap is the other live racer rather than more adjacency search. The canonical frame-1220 P2 representation `ordinary-racer-0x0540-p2-sync-reference` is now the first motion-reviewed authored blue-player asset. It inherits the same dark rubber/saddle, bright neutral hardware, smooth source-model geometry and object-local baked-light hierarchy, while using the P2 blue palette relationship and preserving stock envelope `[23,3]..[40,38]` and contact `[63,76]`. Gameplay-scale review measures 266 overlapping logical pixels over a 361-pixel union (IoU `0.7368421053`), with 304 candidate opaque pixels versus 323 stock. Native run `37166854227` is green through live top/bottom split-screen presentation and guest-state invariants; artifact `11290145680` retains the dossier. This does not broaden semantic coverage and remains review art, not shipping-art approval.

The immediate frame-1219 P2 context `0540` under `0541/0540 + 0D2D/0000` has a byte-for-byte identical deterministic stock raster to the reviewed frame-1220 P2 baseline: identical RGBA/PNG hashes, envelope, histogram and contact. It therefore reuses the same authored blue-player asset under its own exact synchronized guard. Native run `37169313027` is green through live split-screen presentation and guest-state invariants; artifact `11290454491` retains the proof. No second P2 drawing is warranted unless that equivalence changes.

Frame 1218 is the next genuine P2 visual change: semantic `0541` under `0540/0541 + 0D2C/0000`. Its authored asset keeps the reviewed P2 material/lighting solution and translates the accepted 0540 geometry exactly one logical pixel left, matching stock envelope `[22,3]..[39,38]` and contact `[61,76]`. Gameplay-scale review measures 250 overlapping logical pixels over a 372-pixel union (IoU `0.6720430108`), with 304 candidate opaque pixels versus 318 stock. Native run `37169795518` is green and artifact `11290901577` retains the proof. This remains review art, not shipping-art approval.

Secondary appearance references include the official North American/European packaging scans and the 2010 developer feature. They agree with the stock dossier on dark wheel/saddle masses, colored glossy body/frame forms, and brighter neutral hardware. Do not copy marketing-only sparkle/star effects into ordinary gameplay frames merely because they appear in packaging art.

Reference provenance:
- developer recollection / source-model description: https://www.nintendolife.com/news/2010/03/feature_the_making_of_unirally
- high-resolution North American packaging scan catalog: https://openretro.org/snes/uniracers/edit
- additional packaging-image catalog used only as a visual cross-check: https://gamesdb.launchbox-app.com/games/images/2104-uniracers

These web/scan references are supporting interpretation only. Canonical geometry, palette identity, timing and replacement registration remain ROM/runtime derived.

## Palette relationship

HD Presentation does not need to remain limited to SNES palette precision, but colors should preserve recognizable relationships among:

- player colors;
- track/world families;
- HUD states;
- highlights/shadows;
- gameplay-significant contrast.

Any expanded color model should be checked against representative raw and CRT/NTSC references so "cleaner" does not accidentally mean "different graphic language."

## Texture/detail budget

Avoid detail that flickers, aliases or becomes visual noise at racing speed.

A replacement should survive:

- native 4K output;
- common downscales such as 1440p and 1080p;
- motion;
- split-screen;
- different host sampling policies.

Prefer stable large-form cues over ornamental microtexture.

## Dithering and CRT-era effects

Classify each source pattern before translating it.

A checker/dither may represent:

- intended texture;
- transparency approximation;
- shade interpolation;
- palette limitation;
- display-dependent blending.

Do not blindly reproduce the source pixels at HD and do not blindly smooth them away. Use raw source plus controlled NTSC/CRT reconstruction to infer the likely visual role.

## UI and typography

Reconstruct glyph identity and layout deliberately.

Prefer semantic glyph/font reconstruction over substituting a convenient modern typeface. Preserve characteristic widths, baselines, spacing and unusual letterforms where they contribute to the game's identity.

HUD and menu chrome may use cleaner host-resolution geometry, but should remain compositionally traceable to the stock layout.

## Asset approval packet

A replacement candidate should be reviewable with:

- semantic ID;
- raw source;
- palette;
- geometry anchors;
- animation neighbors;
- representative stock in-game capture;
- selected scaler/display interpretations;
- replacement still;
- replacement animation strip/clip when animated;
- sampling/render policy;
- documented intentional deviations.

## Change discipline

This file is allowed to become opinionated as evidence accumulates.

When a design decision changes, record why. Avoid silently changing the visual language asset-by-asset.
