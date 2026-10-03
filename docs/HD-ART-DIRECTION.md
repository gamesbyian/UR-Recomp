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

The final material model is intentionally not fixed yet.

Before production replacement art begins, choose and document:

- wheel/frame/saddle/pedal material interpretation;
- light direction/environment assumptions;
- specular/highlight behavior;
- outline/edge treatment;
- shadow behavior;
- maximum micro-detail appropriate to the game's scale and speed.

Use original rendered frames and developer-history evidence to constrain these choices.

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
