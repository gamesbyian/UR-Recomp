# WIDE-07 genuine framebuffer channel diagnosis (2026-11-16)

Status: authentic bytes compared on GitHub-hosted Ubuntu; **not** phase-qualified, **not** an accepted course (0/45).

## Reproducible provenance

- Source-controlled execution: [run 43975730959](https://github.com/gamesbyian/UR-Recomp/actions/runs/43975730959), exact SHA `058a249991a9e46299c3b12fd2fafec5b11222d0`, command `bash experiments/run.sh`, job `script_linux` 133679243599, successful. Retained evidence artifact [14280777319](https://github.com/gamesbyian/UR-Recomp/actions/runs/43975730959/artifacts/14280777319) includes `real-comparison.json`, `channel-diagnosis.json`, manifest and ZIP hashes.
- Original-USA source artifact 14184488104, run 43772817330, producer SHA `05701c1d19389e90c86b8294a78e4d2ede95183b`; Snes9x 1.63+1bcc369, core pixel format RGB565, dumped BGRX8888.
- Native source artifact 14181849776, run 43767096090, producer SHA `150a0199853b514928803b552e6fd73b642e0ede`; snesrecomp BGRX8888.
- Both framebuffer captures decode to 256×224 RGB; original bytes are BGRX and native BMP rows are interpreted according to BMP height sign, with BGR channel ordering.
- Original capture indices 899→902 correspond to guest frames **1935→1938**; native indices 899→900 correspond to guest frames **1945→1948**. Native master clocks 695201600→696273746; original metadata does not supply a comparable master clock. Equal interval motion does not prove equal absolute phase or input timing.

## Genuine observations

| Original/native capture | R mismatches | G mismatches | B mismatches | Any RGB mismatch |
|---|---:|---:|---:|---:|
| 899 / 899 | 0 | 55,571 | 0 | 55,571 |
| 902 / 900 | 0 | 55,570 | 0 | 55,570 |

For 899/899, native-minus-original green deltas: -1 at 39,033 pixels; -2 at 7,813; +2 at 6,745; +1 at 1,980; zero at 1,773. For 902/900: -1 at 38,457; -2 at 8,071; +2 at 7,058; +1 at 1,984; zero at 1,774. The first mismatched coordinate is (0,0) for both pairs.

Across the measured intervals each producer changed **29,877** pixel positions, with 29,877 shared, zero original-only and zero native-only. These are *motion-mask* observations, not a full-course or phase acceptance.

## Narrow causal hypothesis and next executable experiment

The channel-isolated ±1/±2 discrepancy is consistent with differing RGB565 green quantization or expansion at the **capture/output conversion stage**. It is not yet proof that native PPU colour math is incorrect. Do not modify gameplay or native PPU rendering on this evidence alone.

Next: obtain a fresh authenticated pair of genuine original/native frames and their producer code paths; record a few raw RGB565 source words or native pre-output colour words at the exact mismatched pixel coordinates. In a source-bound `experiments/*` recipe, compute both conventional 6-bit green expansions (bit replication `(g6<<2)|(g6>>4)` and scaled/rounded `(g6*255+31)//63`) against original and native BGRX bytes. Compare per-channel residual counts after candidate normalization, retain pixel-level witnesses and exact SHA/clock/input registration. Only patch the *responsible producer conversion* after identifying the mapping from raw values, and rerun the real-byte comparison.

If phase or input registration remains unproven, capture consecutive frames with explicit guest-frame and input-edge timestamps before treating any remaining pixel residual as a renderer defect. Preserve 0/45 until an independent complete USA event is qualified.
