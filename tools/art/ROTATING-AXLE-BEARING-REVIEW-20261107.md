# 2026 owner-preferred rotating axle and bearing candidate

**Status: optional, source-pinned mechanical experiment only. No recovered original 1994 machine, original motion law, complete character likeness or shipping-art approval.**

## Prior visual choice and the problem hidden in a still frame

The owner preferred the wider "after" pedals and requested orange markings mirrored across the axle. That design is source-certified in [merged #3236](https://github.com/gamesbyian/UR-Recomp/pull/3236) and remains immutable.

Its shaft belongs to the fixed fork_and_frame GLB parent while the two crank arms belong to the rotating pedals GLB parent. A rigid cylinder is axisymmetric, so the incorrect parent is hard to see in a still render. In the actual earlier owner review GLB, blue fork vertices approach the shaft rotation axis to **0.00599** units and the grey fork material surface to roughly **0.065** units. Both interfere with the long radius-0.065 drive shaft unless the stationary materials receive a bearing bore. The old source comment says the shaft joins the two cranks, so this is a concrete source-2026 mechanical inconsistency, without identifying any original 1994 joint.

## Reversible source hypothesis

The new [source derivative](rotating_axle_bearing_review.py) retains the owner-preferred two pedal Y-centres at ±0.56, mirrored orange stripes at ±0.436, symmetrical fork, straight seatpost, eight thin spokes and existing saddle. It changes exactly three source spans, and does not modify previous candidates, original canonical SCAD, default Pages model or shipping art.

1. Move the same long radius-0.065 shaft into the **rotating pedals parent**, sharing the existing metallic crank material colour.
2. Replace the stationary solid grey sleeve with a 0.13-radius *annular fixed sleeve* using a radius-0.071 bore, slightly longer than the sleeve.
3. Cut the same axial bore into both symmetric blue lower fork legs, which previously intersected the rotating shaft envelope.

The 80-facet bore's inscribed polygonal radius minus shaft radius is approximately 0.005945 authored 2026 units. This is a *source-level analytic candidate margin*, not a real surface-intersection proof.

## Confirmed actual surface and connectivity measurements

The [qualified exact-head real-model run #42339141969](https://github.com/gamesbyian/UR-Recomp/actions/runs/42339141969) and [retained physical GLB review artifact 13561180837](https://github.com/gamesbyian/UR-Recomp/actions/runs/42339141969/artifacts/13561180837) now independently prove source-drafted source-2026 bores. The original owner-preferred fixed blue fork and grey sleeve triangle surfaces both intersected the radius-0.065 shaft's axial envelope (zero minimum projected XZ radius). The new actual surfaces clear it by **0.005944440807759105** and **0.005944492040210955** authored units respectively, checked over all actual source triangles and not only vertices. Exactly three of sixteen material meshes changed; other thirteen and all five part pivots were preserved.

A further independent inspection of the source-exported silver crank material found **two disconnected, individually watertight crank components** in the old owner-preferred GLB and **one connected watertight crank-plus-shaft shell** in the newly exported optional candidate. The source-defined rotating axle therefore actually joins both crank arms in the 2026 mesh. This new topology distinction is now an explicit fail-closed real-GLB gate, not merely a reviewer observation. It does not certify physical welding strength, the independent wheel's keying, original 1994 joint design, or the whole character's likeness.

## Fail-closed actual GLB qualification

[Independent verifier](verify_rotating_axle_bearing_review.py) must consume the original and candidate independently authored actual GLBs in the EXISTING Windows Visual Atlas art-review export job and establish:

- Five original rig part parents and sixteen material nodes, with five parent transforms unchanged.
- Exactly **three changed actual materials**: stationary blue lower fork; fixed grey sleeve; rotating silver crank/shaft. Other thirteen material meshes, paints, colour identities and their transforms unchanged.
- Real watertight material surfaces and finite indexed triangles; the grey sleeve and blue lower fork must both be radially clear of the shaft by at least 0.0005 authored units across **every actual triangle**, including triangle interiors. A vertex-only check cannot prove this.
- The old source-owned fixed fork and sleeve must exhibit the historically identified radial overlaps as negative controls.
- Both opposed cranks, all orange marks, saddle, original thin spokes and original reference evidence unchanged.
- No new renderer, runner, Python persistence system, original ROM re-extraction or default art.

Local OpenSCAD CSG parsing succeeded for this optional candidate. A *monolithic* local STL export exceeded the execution budget; it **is not** independent proof of actual new mesh topology or clearance. This candidate must fail qualification if the actual modular GLB export is unsuccessful or lacks the required air gap. Until then the prior source design remains owner-preferred and this variant is experimental.

Even with the new **watertight, connected crank-plus-shaft** topology, independent wheel/rim and crank GLB parents must be rotationally coupled in any plausible drive model. The silver rotating crank/shaft shell remains a separate source material/parent from the wheel hub, so physical wheel-to-shaft keying, original 1994 axle design, authentic time law and full-character likeness are unproved. The earlier original-ROM phase-motion study used the older canonical 2026 GLB, not this wider/rotating-axle candidate, and must be repeated with real 48-frame original source registration before its numerical fit can be transferred.
