# ART-4K: retrospective original-ROM translation-orbit control

Complements merged #3022's target-anchor translation baseline. The 35 masks are revalidated against the authentic USA ROM-composed raster corpus. The **109 adjacency edges, 19 changes and 90 holds belong to an authored reference registry**, not independently witnessed original-emulator cadence. See merged #3025 and draft #3026.

For each same-player same-window authored adjacent pair, optimize a fixed finite grid of integer translations (default ±2 logical pixels, no alpha clipping), minimizing XOR between the shifted previous mask and the *actual next mask*. Preserve all equal minimum shifts, a deterministic least-motion tie break and the margin to the next distinct residual. Compare the optimal shift with #3022's *target-derived* visible-alpha anchor shift. A zero residual means a rigid integer shift can explain that pair under the stated constraints. A positive residual cannot be eliminated by any eligible such shift, but does not by itself prove a 3D mesh deformation; rotation, occlusion, bake/view and sprite shape changes remain possibilities.

**This is an optimistic retrospective oracle**, because the target mask itself chooses the shift. It does not predict motion or establish true source translation, a wheel contact point, original 1994 animation timing, camera, pose mapping, likeness or shipping art. A rig fit must never optimize a novel-frame score using an oracle displacement selected from that held-out frame.

ROM-free core tests:
    python3 -m unittest tests.unit.test_audit_original_racer_translation_orbit

Source-authenticated execution via the existing original-ROM corpus producer:
    python3 tools/art/audit_original_racer_translation_orbit.py --corpus /private/source-corpus.json --radius 2 --out /private/new/original-translation-orbit.json

This standalone source-only diagnostic reuses the established corpus validator, authored window walker, and write-once report. It does not add a rig/viewer, change native presentation or create an expensive default workflow. Before interpreting totals, run it once on the real source corpus; the six ROM-free unit controls prove only the bounded algorithm. Inspect in particular the two changing-mask authored edges with fixed visible alpha anchor. Source-matched pose work should use the existing #2832 five-part rig with a fixed shared camera. Authentic cadence remains gated on actual emulator-captured PPU/OAM evidence.
