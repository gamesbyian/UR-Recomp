# Historical 2014 native replay fidelity gap

Source: GitHub Actions run 36780628583 from superseded PR #90.

The preserved 2014 Dessyreqt SMV can be replayed deterministically through the Snes9x reference path and through the native SNESRecomp host using the exact controller-stream adapter added by the rescued work.

The final PR #90 run did **not** establish native/reference fidelity. Its denser checkpoint pass reported the first sampled mismatch at guest frame 440. The reference reached active race state at frame 794 and race-results state at frame 2874; the native replay did not occupy those corresponding states at those frames. Later sampled state also diverged.

This is retained as a useful fidelity/decompilation target rather than a CI blocker. The historical replay workflow therefore records and uploads the divergence while succeeding so long as it can produce a sufficiently populated comparison.

Interpretation constraints:

- Do not treat this result by itself as proof that the translated CPU code is wrong. Startup state, SRAM/controller-stream timing, host frame semantics, hardware emulation, or incomplete static translation could each contribute.
- Frame 440 is the current earliest sampled divergence, not necessarily the first divergent instruction.
- Use the dense 440-460 window as the initial bisect surface. Add instruction/WRAM/dispatch checkpoints before broadening the search.
- The exact-input host patch is evidence infrastructure and should remain narrow; gameplay semantics should not be patched merely to make this historical movie match.

This result should feed the multi-ROM/multi-analyzer workstream: any routines active around the first divergence are high-value candidates for independent disassembly, function-boundary comparison, runtime execution tracing and semantic labeling.
