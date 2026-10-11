# HD upscaling, reconstruction and generative-art experiment plan

**Status (2026-10-10): documented external prior art and ROM-free experiment bookkeeping added; no candidate visual algorithm or generated sprite has been accepted into the Windows renderer.** The owning visual/approval authorities are [HD-ART-DIRECTION.md](HD-ART-DIRECTION.md) and, for racer character likeness and current visual approval, [HD-RACER-CHARACTER-RECONSTRUCTION.md](HD-RACER-CHARACTER-RECONSTRUCTION.md). The on-demand shader/tool pins remain [TOOLCHAIN.md](TOOLCHAIN.md), and active priority is [WORK-QUEUE.md](WORK-QUEUE.md). This is a *bounded visual-research plan*, not a competing graphics architecture, a permission to override QA-08, or a demand to pause the Baldosa Windows integration.

## Dovetail with the racer character-likeness reset (2026-10-10)

**This section supersedes any earlier inference in this document that an approved 4× pose is aesthetically approved.** After direct owner review of recruitment footage, the existing procedural C++ unicycles remain *technically validated historical fixtures*, but are **not artistically approved Remastered characters**. Read [HD-RACER-CHARACTER-RECONSTRUCTION.md](HD-RACER-CHARACTER-RECONSTRUCTION.md) before initiating racer-art experiments.

The central distinction: the original large-scale title/intro and contemporary official box/manual/promo images inform the **identity, proportions, volumetric design and personality** of the characters, with perspective/source provenance noted; ROM-derived sprite states remain authoritative for **timing, contact, actual pose registration, local transforms, color identity and safe visibility**. A model or shader that merely polishes the existing 4× procedural shapes does not address the rejected saddle/wheel/frame proportions.

### Combined production handoff, in order

1. **Source/provenance contact sheet:** assemble rights-aware *links and review captures*, not redistributed unlicensed originals. Include official large-scale racer images, authentic title/menu and moving ROM frame samples, legacy 4× C++ output, consistent viewpoints, and a document of what each image can and cannot establish. The old art is a control, never a design target.
2. **Geometry-first reconstruction:** measure normalized saddle/wheel/fork/axle/pedal proportions in appropriately matched official viewpoints; block out one physically coherent rounded character (prefer an offline **3D model/rig**, or parametric/vector model demonstrating equivalent multiview continuity). Examine flat silhouette, personality and gameplay-scale read **before** colors, textures, model upscaling or postprocessing. Retain exact ROM contact/pivot/pose mapping.
3. **Small supervised generative/restoration bakeoff:** the Wave Race 64 reference-atlas strategy informs *reproducible grouped candidate intake, selection, provenance and deterministic output assembly*, rather than requiring its N64-specific texture mapping or 1024×768 tile geometry. Condition style/lookdevelopment candidates on **complete characters and the newly approved canonical geometry**, not independent source-sprite hallucinations. Real-ESRGAN/chaiNNer variants can aid restoration and comparison, particularly world/background/UI art; no upscaler may redefine character silhouette or improvise inconsistent mechanical parts. Generative stills do not establish rotation continuity.
4. **Rigged family export and original host integration:** generate a few exact registered poses, including upright and expressive/trick samples, sharing model, lighting, materials and red/blue palette-derived geometry. Use the existing `racer_hd_presenter.hpp` asset slot, animation/pose registries, hash provenance and technical witness paths; if an offline 3D renderer or export adapter is needed, add it to the **art island**, not to the runtime guest, ROM, CI default or a parallel approval pipeline. Preserve existing alpha/visibility/priority safety gates and Original fallback.
5. **Independent multi-axis review:** (a) authentic timing/pivots/contact/OAM and guest-state proof; (b) cross-pose coherent model and motion; (c) at-native-size comparison to **original large-render character identity** and explicit owner aesthetic sign-off; (d) 1P/2P live captures at actual output sizes, with no misleading trailer claims. Reuse existing trial records and acceptance reports for provenance, extending their schema only where tested and necessary.

**Shader placement:** DKC2Recomp Reconstruct, pinned Slang xBR/ScaleFX and F-Zero-like CRT/LCD presentation treatments operate on *Original/fallback or the final composited output* for display comparisons. They do not generate a trustworthy source model and cannot clear the racer **character-likeness gate**. Test identical input frames and report temporal behavior before proposing player-facing options.

**Review order and spending:** Prioritize reference/contact sheet → verified model blockout → one gameplay-scale pose pair → short animation loop → optionally paid generation or restoration if it solves a demonstrated quality bottleneck. Keep art/model weights paid API dependencies isolated until measured and approved. Do not run twenty upscalers and select the prettiest wrong unicycle.

## Evidence and reuse findings

| Source (immutable code/doc revision) | Actually demonstrated | Relevance and limits |
|---|---|---|
| [DKC2Recomp](https://github.com/elliotttate/DKC2Recomp/tree/3b386cb4a6b67472bc6693664ce61a11190e7b5d), MIT project source; [README](https://github.com/elliotttate/DKC2Recomp/blob/3b386cb4a6b67472bc6693664ce61a11190e7b5d/README.md) | Optional experimental **Reconstruct** postprocess: xBR-like corner decisions, decoding checker/line dithering, graded edge-softening controls, flat-display integration. Raw and CRT controls remain separate. | **Highest-priority shader research lead**, not proof of matching Uniracers moving racers, palettes, PAR or an acceptable host integration. Evaluate only against an *identical* current source-frame stream. Attribute MIT implementation if source is adopted; inspect the exact shader's additional notices/dependencies before copy. |
| [Wave Race 64 HD_TEXTURES](https://github.com/elliotttate/wave-race-64-recomp/blob/9041cc8024f6d2015859f88f5a0307b36cd4e50a/docs/HD_TEXTURES.md), document blob \`1682e6cb7ba8fff90c7e3f6f90e65d5101d4cc5f\` | 1,828 mapping pack, exact fragment reassembly, 1024×768 source atlases (8×6 / 4×3 / 2×1 / 1×1), paid Nano Banana 2 \`imagen-nano-banana-2-flash\` requests, output reassembly, manual image acceptance and alias/pattern/scroll-phase controls. Some results are source-preserving, not new detail. | **Best public process reference**, but **N64 texture** layout/mip pipeline is not directly portable to SNES OAM/OBJ sprites. Copy concepts into existing Racer-HD dossiers and project scripts, **not** RT64 packer or N64-specific code. No model/API dependency until a funded supervised pilot. |
| [FZeroSNESRecomp](https://github.com/mstan/FZeroSNESRecomp/tree/1686df46d4fc7c22b5dc8fdfaa5282ca4bd78562) | Display shader choices: None, CRT Soft, LCD Grid, Sharp, Warm Composite and manually loaded GLSL. HD Mode 7 2–10× is separate and warns high factors can be slow. | **Display option/preset precedent**. Do not confuse HD Mode 7 with high-resolution replacement of normal Uniracers OBJ artwork; imported shader compatibility and licensing must be reviewed. |
| [chaiNNer](https://github.com/chaiNNer-org/chaiNNer/tree/bbbbe247c54d09f4f3752fd966118a4dfa85437a), GPL-3.0 | General node-based image processing/upscaler front end, suitable for manual batch graphs and model A/B processing. | Candidate **external/manual workbench**, not a shipping or default-CI tool. The runtime/model/weight closure is currently unqualified for UR's offline island. Do not vendor the enormous app merely to add a dependency line. |
| [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN/tree/a4abfb2979a7bbff3f69f58f58ae324608821e27), BSD-3-Clause | Model family for super-resolution, including illustrated/anime-trained alternatives. | Local model-output hypothesis, not approved art and not evidence that its **weights**, models, or dependencies are islanded. Pin model identity/weights SHA and license if a specific experiment is actually executed. |
| [Libretro Slang](https://github.com/libretro/slang-shaders/tree/84bcd19a854348c0e6a1d3db814a76f11fb6f011) | Curated compare families: xBR/Super-xBR, ScaleFX, conservative sharp/bilinear, CRT/NTSC. | **Already pinned in \`tools/toolchain.json\`**; reuse as-is and verify exact preset paths at the pinned revision before running. Slang is not interchangeably loadable by an OpenGL GLSL-only frontend. |

These are *engineering precedents*, not independent evidence of Uniracers' original sprite geometry or quality rankings for its images. The independent rendering experiments must actually execute on our captures before any claim that a particular preset is better.

## Existing UR-Recomp assets that must be reused

- The current **historically motion/hash-reviewed but owner-visually-rejected reference art is procedural C++ at 4×**, not a directory of production PNG textures: \`native/presentation/racer_hd_presenter.hpp\`; canonical acceptance manifests in \`analysis/data/racer-hd-art-approval*.json\`. New PNG/AI candidates are **proposal inputs to that presenter/reviewer**, never a second runtime asset selector or a replacement approval registry.
- The 1205–1220 pose family, adjacent registered states, 1305–1306 family and 1244–1252/further reviewed strip witnesses already carry exact stock silhouette, wheel-ground contact, alias classes, semantic guards and motion metrics. Deduplicate byte-identical and proven palette-normalized poses **before** upscale or generation. A candidate changing stock-static portions dynamically is a fail.
- Reuse source-OBJ visibility policy, live PPU evidence, split-screen P1/P2 review, \`racer-hd\` approval visual pack and exact Original fallback. Don't accept attractive art as a substitute for a visible/reachable source sprite; QA-08 P2 source visibility remains a separate technical gate.
- Preserve independent dimensions: 256×224 source geometry, 7:6 historical PAR, actual logical Widescreen, 1×–4× internal authored density, output resolution, final-window postprocessing and presentation cadence. Dither/CRT only modifies the final composited image; it must not alter asset IDs, guest memory, simulation or Original reference comparisons.

## Phase A: immediate, cheap, source-identical *display* experiments

**Target:** decide if additional postcomposition treatments are worth *product-level implementation*, without authoring any assets.

1. Select a **single exact set of existing accepted** native/ROM capture witnesses with SHA and source-frame ordinal: static menu/HUD; fast ordinary-race movement; 2P split screen; a background/track edge; small alternating 3–8 frame motion window. Start with the current stock 1× frame and its corresponding native 4×/Original presentation, not unrelated YouTube images.
2. On the existing pinned Slang/RetroArch manual route, compare **nearest/raw** (control), **conservative sharp/super-xBR**, **ScaleFX**, and a **restrained CRT/NTSC** example. Inspect the exact DKC2Recomp Reconstruct source/conditions as a *separate* isolated candidate; port only if output on the identical source can be compared without rewriting the host. Keep \`Raw Pixels\` and \`Authentic\` untouched. Do not mix CRT decoding with a permanently baked Remastered source.
3. Pin complete software revision, actual preset path/pass chain and parameters, source SHA, frame, render resolution, PAR policy, sample point/edge mode, GPU/renderer and run identity. Score at **1080p**, **1440p**, **2160p** and both full 1P and 2P HUD, but do **not** mistake 2160p scaling for a new 4K-resolution art asset.
4. Evaluate temporal shimmer, motion streaking, coherent contours, wheel spokes/contacts, HUD legibility, split-screen edge effects, menu grey/checkers and colour drift. Include exact stock screenshots and motion clips in one review packet. Record the **negative cases** alongside good-looking frames.
5. **Stop/promotion:** if no repeatable improvement over nearest at normal play scale, keep as a reference shader. If helpful, create a separate bounded renderer/presentation proposal with exact input/output contract and accessibility/reduced flashing considerations. Product controls and default settings are not modified by this plan.

The first matrix is intentionally small. A wall of twenty shaders on one screenshot is not sufficient comparison and would create irreproducible visual clutter. Source frames are the common experiment input.

## Phase B: upscale/author candidate art *by family*, not every observed sprite

**Target:** find whether a generator or model saves review-quality artist time without weakening silhouette or motion correctness.

- Pilot one **source-registered canonical racer pose**, a neighboring motion pose and at most one environment/UI family, but begin from the **reference-measured new character blockout**. Keep the existing C++ 4× output only as a historical technical baseline (not a new-art style target). Do not overwrite historical hash-bound fixtures. A palette-equivalent red/blue pose must reuse the **same candidate geometry**; recolouring is a deterministic project transform, not an independent model call.
- Establish a precise **nearest-neighbour 4× baseline**; then try a *small* justified set of local models/presets (e.g. Real-ESRGAN illustration variant, a higher-fidelity restoration model) and, only if funded/approved, one hosted generative model. Exact weight hash/licence, model revision, parameters, seed when supported, prompt/version and source IDs are required.
- Assemble original tile/fragment groups into their **semantic complete image** before generation and split only **after** geometry is reconstructed. This is especially important for alphabet/glyph rows, logo strips, menus, periodic scrolling textures and any overlapping sprite components. The Wave Race 1024×768 atlases and 8×6/4×3/2×1/1×1 layouts are examples, **not compulsory production geometry** for SNES sources.
- For animation, generate constrained **family/strip candidates**, keep the same material and mechanical features across neighbors, and inspect motion at **actual gameplay scale**. Do not approve a beautiful isolated still that changes wheel radius, spoke arrangement, saddle, contact or silhouette across adjacent frames.
- Reconstruct transparency from **original source alpha/mask**, not AI-painted grey/black background. Detect/fringe-clean cautiously: edge alpha coverage remains an exact reviewed parameter. Typography is reconstructed deterministically whenever glyph identity/width/spacing is known; generated text can be used only as a reviewed proposal and must not invent letters.
- Periodic scrolls and reused scenery must derive from **one reviewed periodic master** and deterministic crops, not separate independent generative passes. Any new detail unrelated to original evidence must be called out as an authored decision. Preserve source art and original/reference fallback for rejected results.
- Guard external spend: **preparation/atlasing is free of generation side effects**. Before invoking a paid service, record approval/limit, quoted unit and projected spend, provider/model, request ID and deterministic source-sheet/hash identity. Resume existing jobs, never silently resubmit a batch after failure. Never embed API keys in Git or a generated report.

**Historical hash/technical acceptance is preserved, while current racer appearance approval is explicitly withheld.** Proposals enter the existing `HD-ART-DIRECTION.md` packet and `analysis/data/racer-hd-art-approval*.json` record ecosystem, with the **separate original-character likeness approval** in `HD-RACER-CHARACTER-RECONSTRUCTION.md`. New racer art cannot be declared visually shipping-ready without both this human likeness approval and retained mechanical/temporal/runtime QA. A generative candidate that merely matches stock silhouette at one frame is *not* mechanically or temporally accepted.

## Experiment record: first-party offline validator

New script: \`tools/art/validate_upscale_trials.py\`. It reads JSON manifest schema \`UR-HD-UPSCALE-TRIALS/1\` and checks source semantic identity, capture/source provenance, **actual PNG hashes**, unique trial IDs, exact **4× dimensions** for authored candidates, explicit PAR/view/display-treatments for display-only candidates, tool revision/model/settings, generative request/prompt provenance, and explicit rejected/needs-work reasons. It never executes a model or changes shipping art, and cannot output a shipping approval. One JSON file and a report can be retained *per source candidate*; large image sets stay in the existing ignored scratch artifacts unless intentionally retained as bounded reviewed evidence.

Example **synthetic placeholder** input, requiring real PNGs/hashes when executed:

\`\`\`json
{
  "schema": "UR-HD-UPSCALE-TRIALS/1",
  "source": {
    "path": "stock-057e.png",
    "sha256": "REPLACE_WITH_ACTUAL_64_HEX_SHA256",
    "semantic_id": "source-verified-057e",
    "asset_kind": "racer_pose",
    "provenance": {
      "capture_or_extraction": "specific approved frame/asset dossier",
      "rom_or_source_identity": "exact canonical ROM/build identity"
    }
  },
  "candidates": [{
    "id": "nearest-baseline",
    "kind": "art_4x",
    "output": {"path": "nearest-057e.png", "sha256": "REPLACE_WITH_ACTUAL_64_HEX_SHA256"},
    "method": {"name": "nearest-4x", "revision_or_model_id": "first-party-pinned", "settings": {"scale": 4}},
    "decision": "unreviewed"
  }]
}
\`\`\`

Commands: \`python3 tools/art/validate_upscale_trials.py path/to/trial.json --report /tmp/trial-summary.json\` and \`python3 -m unittest tests.unit.test_validate_upscale_trials\`. This is an integrity/bookkeeping gate, **not** alpha raster equivalence, animation approval or original/native gameplay acceptance. The existing approval and QA apparatus remains authoritative. No model loader, virtualenv, expensive capture workflow or new CI trigger is added.

## Acquisition / islanding disposition

- **Already available and pinned:** RetroArch, Slang shaders, bsnes-hd, SuperFamiconv and accepted screenshots/source assets as available through existing canonical tooling. Inspect installed pins before adding another copy.
- **Acquired now:** immutable reference commit/blob identities and a project-owned dependency-free offline trial validator; no external executable code has been copied. Pinned DKC2 and Wave Race notes are sufficient for U1 methodological adoption and first experiments.
- **Candidate, not acquired:** complete DKC2 Reconstruct source closure (MIT, but first isolate exact shader + host assumptions), optional chaiNNer GPL GUI, GPU-dependent ESRGAN framework/model/weight files, hosted Nano Banana 2 (paid external API), F-Zero custom GLSL loader. None are a safe or useful default island vendor **without measured trial need, license audit, exact bytes, offline dependency closure and relevant tests**. Don't advertise toolchain availability just because a URL is cited.
- Before any executable adoption: follow \`docs/ISLAND-TOOLCHAIN-PLAN.md\`, \`docs/TRUSTED-UPSTREAM-ADOPTION.md\`, \`docs/THIRD-PARTY-CODE-AUDIT.md\`, \`third_party/manifest.json\`. Prefer project-owned minimal CPU/GLSL math adapting *ideas*, using existing build/frontend seams. Shader-language/renderer interface mismatches, licensing and CRT LUT data dependencies are real integration gates.

## Stop conditions and ownership

This remains an optional **graphics research lane** after critical Windows/QA-08 work, unless a bounded source-visibility or shipping-display defect directly requires it. Within graphics art work, **source-referenced character-likeness reconstruction takes precedence over producing more old-style 4× racer poses**. Source-exact gameplay/render fidelity remains a parallel, independent priority. One comparative result must not become an option/default or spawn automatic nightly workflows. No claims of user-facing model generation, free commercial redistribution of artwork, complete sprite coverage or accepted physical 4K output flow from this document alone.
