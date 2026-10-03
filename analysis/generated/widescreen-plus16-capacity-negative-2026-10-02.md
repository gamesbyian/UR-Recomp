# +16 Widescreen presentation-capacity negative evidence

Date: 2026-10-02  
PR: #247  
Control: accepted native +8 hook from PR #228 / run `37081391730`

## Question

Can +16 retain the accepted first future column on the real guest secondary horizontal lane, then obtain the second required adjacent future column entirely in host-owned shadow storage by replaying existing stock preparation semantics against disposable guest snapshots?

The ownership rule was deliberately strict: no synthetic guest `$03xx` lane, no camera authority change, no simulation/activation/collision/progression change, and no final-composition widening.

## Attempt 1: repeat `A59E` inside the existing snapshot replay

Run `37083769287`, artifact `11258704967`.

The accepted +8 path remained intact: 617 preparation events, 317 exact later-stock payload matches, longest exact run 25, protected state equal.

For +16:

- first future column: 617 events, 317 exact later-stock matches;
- second host-shadow candidate: 557 events;
- adjacent/stock-transition-comparable pairs: 557;
- exact later-stock matches for the second column: **31**;
- longest exact second-column run: **22**;
- 60 preparation events could not produce a valid second helper result;
- protected sampled gameplay/camera/progression state remained equal.

This rejects immediate recursive `A59E` as a general second-column scheduler. The helper can sometimes advance into plausible adjacent geometry, but that geometry is not reliably the later stock content required by +16.

## Attempt 2: replay the complete stock `A52F` preparation routine on a cloned +16 camera

Run `37084288683`, artifact `11259897420`.

The runtime captured the complete `81:A52F` entry state, cloned CPU plus low WRAM, added +16 only to the clone's camera X, executed the complete stock preparation routine on that disposable state, harvested its prepared strip into host shadow storage, then restored authoritative state.

Again the accepted +8 path remained intact: 617 events, 317 exact later-stock matches, longest exact run 25, protected state equal.

For +16:

- first future column: 617 events, 317 exact later-stock matches;
- cloned full-preparation shadow candidates: 314;
- adjacent/stock-transition-comparable pairs: 314;
- exact later-stock matches for the second column: **0**;
- longest exact second-column run: **0**;
- protected sampled gameplay/camera/progression state remained equal.

The preparation acceptance gate failed, so the downstream object-liveness gate was intentionally not run.

## Architectural result

The stock guest preparation machinery is proven sufficient for the accepted +8 one-extra-column operation, but these experiments reject treating that machinery as a random-access producer for arbitrarily deeper future columns.

For +16, host-owned capacity remains the correct ownership direction, but the additional host column must come from a presentation source that can address the required future world/resource column directly. Replaying `A59E`, replaying the whole `A52F` routine against a camera-biased clone, or manufacturing extra guest descriptor lanes are not accepted paths.

The next bounded discriminator should therefore connect the already-recovered course/resource presentation model to a host-owned strip query or equivalent semantic presentation cache, while preserving the accepted +8 guest path as the deterministic control. Final composition, HUD, racer graphics and gameplay activation remain downstream and unchanged.
