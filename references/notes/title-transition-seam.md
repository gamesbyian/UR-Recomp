# Title-to-frontend compatibility seam

Recovered-work execution note, 2026-09-29.

Historical compatibility reports include emulators that stop after the Uniracers title screen or fail during the screen transition. The symptom is intentionally treated as a first-divergence seam rather than assigned to CPU timing, PPU state, DMA, SRAM or graphics by assumption.

## Cross-core local baseline

Run `36660094678` drove a bounded no-input boot timeline through pinned Snes9x and the repository-owned Beetle/bsnes-derived core.

Both references produced the same semantic state timeline to the guest frame:

| checkpoint | frame | `7E:009F currentMenu` |
| --- | ---: | --- |
| boot-060 | 60 | `00` |
| boot-120 | 120 | `00` |
| boot-180 | 180 | `00` |
| boot-240 | 240 | `00` |
| boot-300 | 300 | `84` |
| boot-360 | 360 | `84` |
| boot-420 | 420 | `84` |
| main-menu-first | 440 | `D7` |
| main-menu-settled | 500 | `D7` |

This makes the transition boundary concrete: the splash/title-family state `0x84` is established by frame 300, remains present at frame 420, and the first observed Main Menu state `0xD7` is frame 440.

Framebuffer hashes differ between the two correct reference implementations during visible title/menu scenes, so pixel identity is not a cross-core invariant. The state timeline and successful arrival at a stable Main Menu are the minimum compatibility contract. Framebuffer captures remain per-engine evidence for reducing any future visual divergence.

Durable evidence:

- `tests/input/title-transition-recon.script`
- `tools/summarize_title_transition.py`
- `analysis/generated/title-transition-reference-summary.json`

A future failure should be reduced to the first checkpoint where state progression, framebuffer class, or PPU/CPU evidence diverges rather than described only as "stops after title."
