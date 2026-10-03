# Third-pass inference audit

Date: 2026-10-02

This pass re-ran the derive-first audit after the native racer-selection and PPU-placement seams landed, the Widescreen scene-policy recovery was rescued, gameplay-authored progression/save-load was closed, and the latest Restart Race/native Widescreen runs supplied new negative/bounded evidence.

## 1. Racer replacement identity and placement are independent coordinates

The merged racer presentation path now has two clean inputs:

- semantic raster identity comes from authoritative guest WRAM through the read-only racer snapshot/selector;
- screen placement, size and H/V orientation come from live PPU OAM/high-OAM/OBSEL.

Therefore screen position and flip state should not be part of the semantic replacement-asset key. Select/cache the replacement by semantic racer presentation identity, then apply the live OAM transform downstream.

This is useful because animation/state timing stays guest-authored while the host can substitute higher-resolution pixels without inventing a second animation system.

## 2. The first HD racer replacement hook can have zero guest-state authority

PR #239 proved the real native selector can naturally choose Remastered from live WRAM while exposing no guest write path. PR #241 proved project-owned placement code can consume the native PPU storage directly.

Together those results mean the first draw-frame replacement prototype does not need to patch WRAM, OAM, animation counters or simulation. Unknown/unregistered tuples can simply fall back to Original.

That is the narrowest product-facing HD seam available and should remain the default architecture unless a concrete frame family falsifies it.

## 3. Widescreen is a domain-specific, viewport-local policy

The recovered policy now marks representative 1P and ordinary 2P as evidence-backed **mixed** scenes. The consistent ownership rule is:

- preserve stock simulation/activation;
- widen preparation/camera/presentation only where retained evidence supports it;
- compose independently per viewport in split-screen.

So “make the game wider” should never become one global world-liveness switch. The remaining VS question is only whether VS needs a presentation exception, not whether authoritative activation ownership changes.

## 4. Modern profiles should coordinate guest SRAM rather than duplicate progression

Gameplay-authored medal/tier/checksum persistence is now accepted through a fresh save/reload cycle, while the modern host-state seam intentionally contains no cartridge-era progression fields.

The resulting product constraint is straightforward: future autosave/resume metadata may identify, version or catalogue a guest save artifact, but the 8 KiB guest SRAM should remain the authoritative progression payload. Duplicating medal/tier state into the host profile would create two writers for one semantic domain.

## 5. Immediate snapshot equality is not enough for Restart Race

Fresh PR #235 run **37079739225** now reaches the real experiment after the toolchain patch was repaired.

It captures a 324,142-byte snapshot at frame 925 and restores it with exact immediate equality, digest **57348edd**. But after the required 60-frame replay, equality fails specifically in the APU partition:

- expected APU digest: **0848aa7e**
- actual APU digest: **1b1b116b**

This is a useful negative result. Restart certification must include forward replay, not merely “save then load returns identical bytes.” The next discriminator should focus on APU state/timing that is outside the restored snapshot or advanced asymmetrically around restore. At audit time, Restart remained unaccepted; the post-audit resolution below records the later accepted fix.

## 6. The stock-helper Widescreen path has a natural +8 capacity boundary

The accepted PR #219 mechanism established one additional 8-pixel column through the stock secondary horizontal lane. The latest native-hook run **37078584156** strengthens that model:

- 617 +8 preparation events;
- 317 exact later-stock payload matches;
- longest consecutive exact-match run 25;
- protected gameplay/camera/progression state unchanged;
- +16 and +24 stop at the secondary-lane-capacity boundary.

At audit time, the native hook was not yet accepted because 11/617 +8 PREP events appeared to fail the strict immediate-adjacency predicate. The post-audit resolution below records that these were analyzer false negatives and the tightened final acceptance.

The inference is nevertheless bounded: +16/+24 are not simply larger values for the same one-spare-lane mechanism. They require additional queue/storage capacity or a different scheduling strategy after the +8 exceptions are understood.

## Admission consequences

The next useful work is narrower than before this audit:

1. HD racer pixel substitution can proceed using the already-separated semantic-identity and live-placement inputs.
2. Restart Race should investigate the APU restore/replay seam specifically.
3. Widescreen should explain the 11 +8 adjacency exceptions before promoting the native hook, then treat +16/+24 as a capacity-extension problem.
4. Autosave/profile work should preserve guest SRAM as the progression source of truth.

The Restart and native-hook findings above preserve the then-open PR state at audit time. Their merged current dispositions are recorded below; later retained Widescreen evidence also closes the +16 host materializer seam.

## Post-audit resolutions — 2026-10-03

The two open runtime findings were subsequently resolved without weakening their original falsifiers.

- **IA3-R01 / Restart Race:** PR #235 merged after workflow run `37080761750` passed the same capture → 60-frame advance → exact restore → 60-frame replay contract. Root cause of the earlier APU divergence was missing rollback ownership of the desktop host's extended `RtlApuFrameClock`; rollback residue v7 now preserves that clock. The historical negative remains useful because it established that immediate restore equality alone is insufficient.
- **IA3-W02 / native +8 Widescreen hook:** PR #228 merged after final run `37081391730` accepted all 617 same-camera preparation steps. The earlier 606/617 result came from an incorrect analyzer model that treated the full edge word as a plain 5-bit ring counter. Raw traces show all 617 preparations advance exactly one low-five-bit position on the 32-column VRAM ring. Their full-word step shapes are 589× `+1`, 17× `-31`, and 11× `+33`; each shape is observed in stock control transitions. The independent 317 exact future-stock payload matches, 25-column consecutive run, protected-state equality, and +16/+24 capacity stop remain intact.

Current consequence: neither finding is an open research blocker. Restart proceeds to product/UI integration; Widescreen beyond +8 proceeds as an explicit presentation-capacity design problem.
