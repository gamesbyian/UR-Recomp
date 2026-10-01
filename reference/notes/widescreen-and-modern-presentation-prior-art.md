# Widescreen and modern-presentation prior art

Status: curated external-reference note for Phase F / Phase G.

This note records architectures and failure categories worth studying before implementing Uniracers presentation changes. These projects are references, not implementation authorities. Reproduce relevant claims locally against Uniracers before turning them into game-specific behavior.

## Super Mario World Widescreen / wide-snes

Pinned reference:

- repository: `VitorVilela7/wide-snes`
- revision: `b988c0afdb98ec778ce4cd140abc1ae3b5828fab`
- upstream describes 352x224 and 384x224 widened modes, with different pixel-aspect treatments, implemented as a ROM patch plus bsnes-hd configuration.

Why it matters:

The useful lesson is the taxonomy of engine assumptions exposed by genuine SNES widening, not transferable addresses or patches. Phase F reconnaissance should explicitly look for analogous Uniracers seams:

1. viewport/camera bounds;
2. background/tilemap preparation outside the classic viewport;
3. sprite X encoding, clipping, culling and wraparound;
4. object spawn/proximity/activation assumptions;
5. world/course boundary handling;
6. graphics/stage streaming horizons;
7. fixed-screen HUD/menu layers versus world layers;
8. SNES windowing/color-math/scanline effects;
9. pixel-aspect, overscan and target-width policy;
10. per-aspect exceptions and scripted composition.

wide-snes demonstrates why a widescreen patch may need both game-side changes and emulator-side presentation policy. It should not be used as evidence that any particular Super Mario World fix applies to Uniracers.

## bsnes-hd widescreen diagnostics

Pinned through the project toolchain as a specialist workbench.

Its widescreen controls map unusually well to the questions Phase F must ask:

- per-background-layer widening;
- sprite modes (`clip`, `safe`, `unsafe`, `disable`);
- widescreen edge markers;
- window-effect fallback/ignore behavior;
- overscan and pixel-aspect correction;
- arbitrary aspect targets;
- background cropping/auto-cropping;
- scanline-dependent background widening.

Upstream explicitly warns that objects/sprites generally do not become correct in newly visible widescreen areas without game-specific ROM changes. That makes bsnes-hd useful as an exposure probe, not a shipping implementation.

The project should own a small reproducible diagnostic preset matrix rather than depend on interactive hand configuration. Exact presets belong under the Phase F harness once a deterministic command/output route is proven.

## Zelda64Recomp / RT64 architecture

Pinned reference:

- repository: `Zelda64Recomp/Zelda64Recomp`
- revision: `b65c482ed672258eb684ab94a4e8c8aa662615ee`

Useful architectural observations:

- original game execution remains authoritative while a modern renderer supplies presentation enhancements;
- arbitrary aspect ratios are supported rather than treating 16:9 as the only widened state;
- HUD placement can be constrained independently from world aspect;
- original framebuffer/depth/shading effects require explicit preservation in the modern renderer;
- upstream documents edge-animation quirks in some very-wide cutscenes, a useful warning that scripted composition needs dedicated coverage.

This is relevant to UR-Recomp's separation between authoritative SNES state, Widescreen policy and host-side HD Presentation. It is not a claim that the N64 rendering techniques themselves transfer to the SNES.

## HD-pack-style semantic indirection

A recurring useful architecture in emulator enhancement systems is:

```
original graphics/state identity -> replacement presentation asset
```

UR-Recomp should preserve that abstraction without adopting an unrelated pack format blindly. The canonical HD Presentation manifest should key important replacement art from deterministic semantic state or extracted source identity, never solely from fuzzy framebuffer matching.

## Project takeaways

The combined prior art supports five project rules:

1. Keep 4:3 authentic output as the permanent oracle.
2. Treat Widescreen and HD Presentation as coordinated but separate implementation phases.
3. Model simulation/activation, preparation/streaming, render/culling, camera/composition and UI widths independently even when the stock game happens to conflate them.
4. Probe newly visible space systematically before permanently changing behavior.
5. Reconstruct HD art from semantic source/state evidence and explicit art-direction rules, not from one favored upscaler.

External repositories may change. Use the pinned revisions above when a research conclusion depends on specific source behavior.
