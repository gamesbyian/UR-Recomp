# Asset Restoration and Audio Modernization Pipeline

Last updated: 2026-09-29

This document defines the production workflow for turning authoritative Uniracers source evidence into modern visual and audio assets. It complements `HD-VISUAL-REFERENCE-PIPELINE.md`, which governs visual-reference generation and comparison, and `HD-ART-DIRECTION.md`, which governs coherent-art decisions.

The central rule is simple: **generated or processed outputs are candidates, never authority**. Original ROM/SPC data, deterministic emulator output, extracted palettes/samples, animation neighbors and verified game-state context remain the factual source layer.

## 1. Production hierarchy

Prefer the least inventive transformation that satisfies the presentation goal:

1. exact extraction from ROM/SPC/runtime state;
2. deterministic reconstruction or re-rendering from extracted data;
3. conventional signal/image processing;
4. learned restoration or upscale models;
5. generative reconstruction constrained by source structure;
6. human cleanup and art/audio direction.

Do not jump to generative synthesis when the source data can be reconstructed exactly.

Every accepted asset must retain a provenance chain back to authoritative inputs.

## 2. Repository shape

Target structure:

```
tools/
  graphics/
    extract/
    compare/
    upscale/
    generative/
    palette/
  audio/
    spc/
    brr/
    render/
    analyse/
    restore/
    compare/

assets/
  source/
  candidates/
  approved/

workflows/
  graphics/
  audio/

models/
  manifests/
  README.md
```

Large model weights are not committed. Commit manifests, exact model/version identifiers, hashes, licenses, acquisition instructions, workflow definitions, parameters and small fixtures. Store weights in ignored caches or CI/download artifacts only when needed.

## 3. Graphics toolchain

### Deterministic plumbing

Prefer scriptable tools for bulk and regression work:

- ImageMagick;
- libvips;
- Python Pillow/OpenCV where project-specific logic is needed;
- ffmpeg for frame extraction and video-derived references;
- existing SNES extraction/reconstruction tooling already owned by the project.

Use these for:

- crop/trim/alpha normalization;
- palette extraction and comparison;
- contact sheets;
- atlas assembly;
- difference images;
- color-space normalization;
- batch resizing;
- animation-sequence inspection;
- checksum/provenance capture.

### Upscale families

Do not standardize on one upscale model. Maintain a small comparison matrix spanning materially different assumptions:

- nearest-neighbor / integer pixel scaling;
- conventional bicubic/Lanczos baselines;
- ScaleNx / HQx / xBR / xBRZ / SABR / ScaleFX / Super-xBR reference families already tracked by the visual-reference plan;
- waifu2x;
- Real-ESRGAN;
- Real-CUGAN;
- emulator/shader outputs from the pinned RetroArch / Slang / bsnes-hd reference toolchain.

For each semantic asset or representative frame, generate side-by-side candidates from the relevant subset rather than treating any one result as canonical.

### Generative reconstruction

Use generative tools only after exact geometry, animation relationships and palette/context are understood.

Preferred reproducible surfaces:

- ComfyUI workflow JSON;
- scripted Hugging Face Diffusers pipelines;
- ControlNet-style structural conditioning;
- IP-Adapter/reference-image conditioning;
- Krita plus AI-diffusion tooling for local inpainting/outpainting and human-guided cleanup.

Preserve, where relevant:

- source image(s);
- edge/line/depth/segmentation controls;
- model and checkpoint identifiers;
- VAE/adapter identifiers;
- seed;
- sampler/scheduler;
- step count;
- guidance values;
- denoise strength;
- crop/upscale geometry;
- prompt/negative prompt if used;
- post-processing steps.

A generative result that cannot be reproduced closely enough for review is not production-ready.

### Animation coherence

For animated replacement assets, evaluate the sequence as a system rather than independent stills.

Automated checks should measure:

- contour drift;
- apparent scale drift;
- pivot/rotation-center drift;
- contact-point drift;
- silhouette discontinuity;
- frame-to-frame flicker;
- inconsistent invented detail;
- palette/lighting discontinuity.

The original animation timing and simulation state remain authoritative unless a documented product decision says otherwise.

## 4. Graphics comparison dossiers

When Phase E extraction is mature, every important replacement asset should have a compact dossier containing:

- raw extracted source and palette;
- authoritative framebuffer appearances;
- neighboring animation states;
- geometry/contact anchors;
- nearest/conventional upscale baselines;
- selected pixel-art scaler outputs;
- selected neural upscale outputs;
- emulator/shader interpretations where relevant;
- one or more constrained generative studies if useful;
- notes recording what details are known versus inferred;
- the approved candidate and rationale.

This makes art review comparative and evidence-driven rather than prompt-driven.

## 5. Audio source hierarchy

Prefer direct SPC/APU evidence to enhancement of mixed recordings.

The project should treat the SNES audio pipeline as recoverable structured data:

```
SPC/APU state
  -> per-voice sequence/events
  -> BRR sample bank + loop metadata
  -> DSP/ADSR/pitch/echo state
  -> exact reference render
  -> reconstructed or modernized render
```

Where exact source-state extraction is possible, neural source separation is a fallback rather than the first step.

## 6. Audio toolchain

### Exact/reference rendering

Bring in or wrap:

- `snes_spc` or an equivalent cycle-accurate SPC700/DSP reference renderer;
- BRR extraction/decoding tooling such as BRRtools;
- deterministic ffmpeg/SoX-style processing for resampling, normalization, filtering and format conversion.

Required capabilities:

- exact SPC playback;
- per-voice muting/soloing;
- channel-isolated renders;
- BRR extraction to lossless PCM;
- loop-point preservation;
- SNES Gaussian-filter reference rendering;
- DSP/echo state inspection where practical.

### Sequence recovery

Evaluate SPC-to-MIDI / engine-specific sequence extraction only as scaffolding. Automatic conversion is evidence, not authority.

Recover when possible:

- note onset/duration;
- tempo;
- instrument/sample assignments;
- pitch bend;
- vibrato/modulation;
- ADSR;
- loop structure;
- channel priority/state.

Manually validate converted sequences against isolated reference renders.

### Music reconstruction

For each track, choose among:

- exact high-quality rerender of original samples and sequence;
- original BRR samples rendered cleanly at modern output rates;
- reconstructed high-resolution samples matched to the BRR source;
- replacement/recorded instruments constrained by the original arrangement;
- hybrid approaches.

Preserve composition, timing, melodic/rhythmic structure and game-trigger semantics unless a documented alternate presentation mode intentionally changes them.

Modern mixing/mastering may improve headroom, stereo field, noise floor and output format, but should not erase the recognizable source identity.

### Sound-effect reconstruction

Catalogue sound effects as semantic assets with:

- source BRR sample(s);
- pitch/envelope behavior;
- ADSR;
- DSP/echo/filter context;
- trigger/state context;
- exact reference render.

Then decide per effect whether the modern presentation should:

- preserve the exact effect;
- rerender at higher fidelity;
- reconstruct from a higher-quality source/sample analogue;
- subtly layer modern material;
- replace it while matching the original spectral and temporal envelope.

Avoid applying one blanket “HD SFX” treatment to every effect.

### Neural audio tools

Source separation or generative audio tools may be useful when direct structured evidence is unavailable, especially for external recordings or reference material. Candidate families include Demucs/RoFormer-style separation and modern audio-restoration models.

Do not use neural separation in place of SPC voice isolation when the emulator/APU state can provide exact channels.

## 7. Provenance contract

Every generated/restored candidate should have a machine-readable sidecar recording at least:

- semantic asset ID;
- authoritative source file/hash;
- extraction tool/version;
- processing tool/model/version;
- parameters;
- workflow file/hash;
- seed where applicable;
- intermediate source hashes where practical;
- human edits;
- reviewer/status;
- license/provenance notes for external models or source material.

Approved outputs must be traceable to the candidate that produced them.

## 8. Automation and CI posture

Do not put GPU-heavy image/audio generation into default CI.

CI should instead validate cheap invariants:

- workflow/manifest schema;
- referenced source hashes;
- model-manifest completeness;
- missing provenance;
- deterministic comparison scripts on tiny fixtures;
- approved-asset dimensions/formats;
- animation anchor/sequence checks where cheap;
- audio loop metadata and sample-format invariants.

Heavy generation should run manually or in explicit opt-in workflows and deposit compact review artifacts.

## 9. Acquisition priorities

Acquire or pin tools only when they serve a concrete workflow. Priority order:

### High priority when production begins

- ImageMagick / libvips / ffmpeg wrappers;
- comparison/contact-sheet/diff tools;
- waifu2x / Real-ESRGAN / Real-CUGAN runners;
- ComfyUI workflow contract or equivalent scripted Diffusers path;
- snes_spc reference renderer;
- BRR extraction/decoding;
- waveform/spectrogram comparison tooling;
- provenance-sidecar schema.

### Medium priority

- Krita AI-assisted cleanup workflow documentation;
- ControlNet/IP-Adapter model manifests;
- sequence/MIDI extraction experiments;
- automated animation-coherence metrics;
- model chaining / tiled generation helpers.

### Specialist / evidence-driven only

- large families of style models;
- exotic neural restoration stacks;
- stem-separation models when SPC channel isolation already answers the question;
- heavyweight audio workstations or GUI-only tooling that cannot be scripted or provenance-captured.

## 10. Acceptance principle

The production question is never “does this look/sound more modern?”

The acceptance questions are:

- is the source identity preserved?
- is known geometry/timing/state preserved?
- are invented details deliberate and reviewable?
- can the result be reproduced?
- can a reviewer compare it against exact source evidence?
- does it remain coherent across neighboring frames/tracks/effects?
- does authentic/reference presentation remain available for regression?

A modern asset that fails those tests remains a candidate, however attractive it is.
