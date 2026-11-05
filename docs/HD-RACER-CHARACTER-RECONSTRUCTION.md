# HD racer character likeness: visual re-approval and reconstruction brief

**Status: visual direction reset, 2026-10-10.** Project-owner review of recruitment footage rejects the current procedural 4× HD unicycles as an acceptable visual realization of the original characters. They may be technically correct test assets but **are not approved as finished Remastered character art**. This decision is prospective and does not erase historical pose/hash approvals or evidence of technical correctness. Do not assert that visual likeness has been accepted because `analysis/data/racer-hd-art-approval*.json` says `shipping_art_approved: true`; those artifacts document the *prior* review under a narrower rubric.

**Inverse-graphics engineering companion (2026-10-31):** [source-registered technical specification](HD-RACER-INVERSE-GRAPHICS-SPEC.md) and [executable delivery plan](HD-RACER-INVERSE-GRAPHICS-PLAN.md). These reuse the original-source reference tooling and the existing unapproved shared GLB blockout from draft #2832; they do not override this visual veto or award likeness approval.

## Target

The target is **recognizably the same charming, rounded, pre-rendered 3D unicycle characters** from the original game's prominent, large-scale presentations: the animated original title/menu imagery where applicable, original packaging, manual and period promotional material, interpreted with ROM gameplay sprites. These have character and mass. Making a mechanically plausible contemporary bicycle, a minimalist icon, or a detailed pixel-art tracing misses that identity.

Reconstruct what the original detailed 3D models probably looked like **at source/render quality**, not what arbitrary new shapes can be made to fit a 32-pixel downsample. The external marketing artist's illustration is not guaranteed to reproduce the underlying model exactly, so corroborate important proportions against the title/gameplay rendering before treating them as canonical. **Pixar-like charm** here denotes rounded, readable anthropomorphic motion, not a request to import Pixar's actual `Red's Dream` design or borrow its artwork.

### Visual identity checklist

These are qualitative starting points requiring measurement against specific official references, not numeric claims about the missing original model:

1. **Saddle/personality:** broad, soft-looking, black, organically curved saddle that clearly reads as the character's "head"; front/rear taper and mounting must resemble the original large-scale depiction. No flat bar/capsule or tiny seat on an excessively tall mechanical stalk.
2. **Wheel and tire:** chunky, black rubber tire with the correctly proportioned metallic wheel interior, hub and apparent thickness, not a bicycle wheel reduced to a wire ring; wheel size relative to saddle and fork must derive from the reference. Keep genuine perspective distortion through tricks and turns.
3. **Frame/fork:** continuous, strongly colored rounded structural geometry, convincingly integrating upper neck, fork crown, wheel supports and axle. Preserve the original body’s bulky, toy-like/CG-rendered volume; avoid a skinny, disconnected stick or schematic triangulated brace where the source shows a different form.
4. **Pedals/cranks and hardware:** recognizable original shapes, locations, silhouettes and attachment points. Metallic detailing should clarify form, not create an over-engineered mechanism that overwhelms it.
5. **Materials/lighting:** period CGI-style dimensional shading: sculpted volume, dark satin/rubbery saddle and tire, colored curved glossy metal/plastic, legible highlights, bright but controlled hardware. Avoid flat vector/cartoon symbols, extraneous sparkle, hard outlines or modern photorealistic dirt.
6. **Character acting:** saddle/head tilt, squash and stretch, leaning, bounce, pedal phase, stunts and recovery must read as expressive physical acting, all driven by original state and cadence. The personality should survive at racing speed; do not add independent host animations that alter game behavior.
7. **Color/palette:** retain stock racer identities and preserve reliable palette-derived variants from a single canonical form and shared light rig.

**No numerical ratio is signed off yet.** Measure and publish the wheel outside diameter, saddle width/height, saddle-to-wheel vertical interval, crown width, fork spread and pedal offset in normalized, perspective-tagged *reference views*. Do not eyeball those dimensions across different camera angles or distort the already-proven guest contact/pivot to force a poster illustration's foreshortening into a side-view sprite.

**Reproducible measurement tool:** [Projected likeness landmark protocol](HD-RACER-PROJECTED-LANDMARKS.md) binds all manually annotated reference positions to exact local source-image SHA-256, perspective, pixel-aspect, source credits and rights notes. It computes **projected 2D measurements only**, with no 3D camera correction, visual sign-off, source-image redistribution or automatic HD admission. Use it before proposing numeric canonical rig proportions.

## Reference dossier and precedence by question

Different evidence answers different questions; do **not** use a single undifferentiated "ROM always first" hierarchy for everything.

| Question | Primary evidence | Secondary checks |
|---|---|---|
| Who is the character? Large-form design, silhouette volume, construction, personality | Original game title/intro/menu imagery when genuinely high-detail; original box/manual/promo renderings; developer source-model testimony | Registered gameplay sprites and adjacent poses, with perspective caveats |
| How does a specific gameplay pose face/move, and where does it touch the track? | Exact ROM state, OAM/PPU-isolated original raster, measured pose registration, neighboring frames, original timing | Large-scale depiction to resolve deliberately lost source-model volume |
| How do different camera angles/rotations relate? | Multiframe gameplay families and stock perspective cues, reconstruction of a coherent 3D model/rig | Repeated original promo/title viewpoints |
| Materials and palette relationships | Original larger renderings corroborated by ROM palette/value ramps | Contemporary rendering experiments; models are proposals only |

Reference index (link to original source, record capture date and usage rights; **do not commit unlicensed scans to the repository**):
- Nintendo Life 2010 developer interview: https://www.nintendolife.com/news/2010/03/feature_the_making_of_unirally . Robbie Graham describes fully detailed CG models, saddle motion, tilt/stretch and many pedal phases; Martin Good's animation work is identified.
- Packaging/gallery: https://www.mobygames.com/game/8085/uniracers/covers/ ; https://gamesdb.launchbox-app.com/games/details/2104-uniracers ; https://openretro.org/snes/uniracers/edit .
- Original title-screen captures: https://gamedb.retronian.com/games/sfc/uniracers.html . Distinguish authentic title/intro frames from fan-art and box-art.
- Original game manual (for contemporary drawings and styling context): https://www.videogamemanual.com/snes/Uniracers%20%28USA%29.pdf .
- Local ground truth: current `native/presentation/racer_hd_presenter.hpp`, ROM source-frame dossier/review output, `docs/HD-ART-DIRECTION.md`, `analysis/data/racer-hd-art-approval*.json`.

Before calling a reference "the source model", annotate image origin, artist/region, frame/context, view angle, likely exaggeration/foreshortening, and what features it can actually prove. The North American cover is illustrative packaging credited to David Harto, not an authenticated render of Martin Good's source 3D mesh.

## Relation to community upscaling experiments

The reviewed external methods in [HD-UPSCALING-EXPERIMENT-PLAN.md](HD-UPSCALING-EXPERIMENT-PLAN.md) are intended to **feed this character reconstruction**, never override its visual-identity review:

- **Wave Race 64:** reuse the discipline of coherent assembled images/atlases, exact mappings, provenance, reviewed generation, and deterministic extraction. For this SNES racer, the corresponding semantic unit is a **whole character + registered neighboring poses**, ideally derived from one canonical rig rather than N64 texture fragments.
- **Real-ESRGAN/chaiNNer and constrained generation:** restoration/look-development/paintover proposals from official large-scale references and *newly validated model geometry*, with tracked model/weights, rights and settings. A stylized hallucination inconsistent in saddle/wheel/fork proportions or across motion is rejected regardless of pixel quality.
- **DKC2Recomp Reconstruct, Slang xBR/ScaleFX and F-Zero-like display presets:** Original/fallback and optional postcomposite comparison; these cannot discover a missing 3D racer model or certify the new Remastered character.
- **Existing project assets:** reuse our source-specific alpha/pose/OAM/temporal masks, exact frame captures, deterministic palette transformations and `tools/art/validate_upscale_trials.py`. Extend the validated provenance records to name the canonical blockout/camera and reference views when needed; retain old approved art/hashes only as technical controls.

Recommended first acceptance artifact: one contact sheet and **side + expressive-pose short loop** with four aligned columns (original high-detail source reference where available; raw gameplay sprite; old C++ 4× technical baseline; geometry-rebuilt candidate). Evaluate both enlarged and normal gameplay/split-screen sizes. The project owner must approve **likeness** separately from byte-exact mechanics. Do not treat a model output or smooth shader as a substitute for that approval.

## Cross-project graphics plans and possible collaborators (2026-10-10 inspection)

**Candidate roster:** [HD-RACER-ARTIST-LEADS-20261010.md](HD-RACER-ARTIST-LEADS-20261010.md) is already merged to `main` with public evidence links, modeling-versus-rigging qualifications and the distinction between fandom and availability. Do not duplicate it in the playtester roster or assume any listed person has consented to contribute.

**Malmazuke / PAL** — [`malmazuke/unirally-reconstruction`](https://github.com/malmazuke/unirally-reconstruction) has a future M5 high-resolution asset-pack goal in [`docs/PROJECT_PLAN.md`](https://github.com/malmazuke/unirally-reconstruction/blob/main/docs/PROJECT_PLAN.md): **logical asset identity -> replacement image + pivot + frame order/timing**, original-local-asset fallback, size/memory budget, no gameplay hash changes. [`D-0005`](https://github.com/malmazuke/unirally-reconstruction/blob/main/docs/decisions/D-0005-classic-content-distribution.md) specifies original ROM-derived content isolation and replacement through the same logical identity. This is a useful independent **format/contract comparator** for Blender/rig-derived exports and PAL pose evidence, **not** a ready-made upscaling method, rig implementation or collaborator directory. The project's plan explicitly defers replacement-art commissioning until after its near-term native slice, and its current [CONTRIBUTING.md](https://github.com/malmazuke/unirally-reconstruction/blob/main/CONTRIBUTING.md) does not accept external PRs. No named HD visual artist or specific Blender/generative model choice was found in current main's README, plan, future ideas, contribution rules and tree inventory. This finding is scoped to these public surfaces, not proof that no private discussions exist.

**Baldosa / USA** — [`baldosa/uniracers-recomp`](https://github.com/baldosa/uniracers-recomp) currently prioritizes native AOT/decomp correctness and original-ROM assets. Its [README](https://github.com/baldosa/uniracers-recomp/blob/main/README.md), [recomp design](https://github.com/baldosa/uniracers-recomp/blob/main/docs/superpowers/specs/2026-10-06-uniracers-recomp-design.md), [implementation plan](https://github.com/baldosa/uniracers-recomp/blob/main/docs/superpowers/plans/2026-10-06-uniracers-recomp.md) and [decomp plan](https://github.com/baldosa/uniracers-recomp/blob/main/docs/superpowers/specs/2026-10-07-uniracers-decomp-design.md) do not specify a high-resolution racer art pipeline, trained upscaler, 3D character artist, or a Blender rigging collaboration. Its runtime, renderer, ROM/OAM and reproducible routes can independently test **our** high-density output; it does not currently supply the replacement art.

**Action:** Keep the *character-likeness source*, *artistic human review*, *canonical geometry/rig*, *existing UR exact-pose host integration*, and *technical cross-project evidence* as distinct responsibilities. At export design time, check Malmazuke's M5 manifest fields against our existing source-registered pose/anchor/temporal manifests and copy only useful concepts; do not introduce a duplicate runtime selector or asset-pack format without measured need. The cross-project repos do not presently remove the need to recruit a suitably skilled visual artist or commission one canonical 3D rig.

## Required workflow

1. **Freeze promotions, not the pipeline.** Existing 4× drawings remain reversible comparison and engineering fixtures; preserve their exact hashes, ROM registration, runtime fallbacks, coverage data and prior reviews. Do not rewrite historical `approved` records to pretend the original reviewer didn't approve them. Their **character-likeness visual sign-off is now explicitly withheld** in this current authority.
2. **Build the reference contact sheet:** paired views of official large-scale art, authentic in-game title/menu renders, the corresponding stock racer frames at both nearest-pixel and normal gameplay size, and the current authored 4× raster. Label mixed angles, region, source and evidence/rights.
3. **Measure and block out one canonical model:** a neutral 3D model/rig is a strong candidate given DMA's original workflow; a vector/parametric source is acceptable if it achieves the same physical consistency. Start with the saddle-wheel-fork proportions in reference-matched side and three-quarter views. Review flat silhouettes and major masses *before* materials. Use an offline exporter, **not** a new runtime simulation or a second graphics architecture.
4. **Run a small style bakeoff:** reproduce one static side pose and one expressive action pose. Compare current C++ asset, revised parametric/3D render and stock original in precisely registered coordinates. Keep the same guest geometry and material identity. Reject any image that only looks attractive when enlarged.
5. **Approve the model, then generate the family:** use original pose/state/flip/pedal cadence, canonical camera/lighting/materials, palette equivalence, transparent alpha, pivot/track-contact and OAM-layer rules. Do not individually hallucinate 100s of independent poses. Feed the current deterministic hash/manifest/replacement presenter path; scope all tooling and dependencies under the existing art island.
6. **Review motion as artwork:** 16-frame source window plus available transitions; full-resolution and normal-size footage in 1P and split-screen, Original vs Remastered, real 16:9 and output scaling. Show uninterrupted sequences and zoomed/pixel-level images, not cherry-picked frame stills. Include title/menu large renders *as the style reference*, not as a claim that those particular views appear in race gameplay.
7. **Collect explicit human artistic approval** before describing a family as visually/shipping ready. Document reviewer's approval, referenced comparison packet and immutable asset hashes. Keep separate mechanical correctness, geometry/animation, visibility/QA-08 and **character-likeness** statuses. Existing CI green and old `shipping_art_approved` are **necessary historical evidence, not sufficient future likeness clearance**.

## Artist-facing release criteria

- In blind side-by-side comparisons with original high-detail references, the remaster should immediately read as **that same unicycle design**, not an arbitrary new unicycle. If the wheel/saddle/fork ratios are conspicuously different, it fails.
- Model proportions coherent across ordinary upright, tilted, stretched, turning, jumping and stunting poses; both color variants share geometry and material response.
- Silhouette, large value masses, seat expression and hardware read at native gameplay scale and split-screen, not just 4× inspection.
- Existing trace/state determinism, precise contact/placement/alpha/OAM authority, safe Original fallback, 1P/2P and wideness release tests remain independently mandatory. Do not relax correctness thresholds just to make a prettier image.
- Review packet shows official-large-render vs stock vs *candidate* vs live capture, with provenance, reproducible export, test results and explicit current artistic disposition.
- The recruitment trailer must not suggest the present procedural HD drawings are the final remastered characters. It may show them as explicitly labeled **WIP/experimental**, or show Original sprites until an artistically approved replacement exists. Coordinate with trailer owner; do not commandeer the trailer lane.

## Immediate first assignment

The art agent should produce a **single reference-registered character turnaround and pose study**, not another dozen approved-from-IoU-only procedural frames. Reuse source assets/provenance, the existing 4× presenter, exact pose registries and approval packet. Report which *specific* proportions are wrong in today's authored art, the numerical original/reference landmarks, the corrective model geometry, and honest before/after captures. Submit as a scoped graphics PR with no guest/simulation or master-trailer edits.

Do not mistake temporary availability of playable HD pixels for artistic completion. The user has explicitly vetoed the existing visual character realization.
