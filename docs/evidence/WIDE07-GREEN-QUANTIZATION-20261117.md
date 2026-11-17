# WIDE-07 genuine green quantization diagnosis (2026-11-17)

## Source-bound execution

GitHub-hosted [run 44006755584](https://github.com/gamesbyian/UR-Recomp/actions/runs/44006755584) completed at experiment SHA `8af7462f5f19f0e93eb6630851e7fd2c5add6a86`, executing `bash experiments/run.sh` on Ubuntu. Retained [artifact 14294247550](https://github.com/gamesbyian/UR-Recomp/actions/runs/44006755584/artifacts/14294247550) contains `green-expansion.json`, ZIP hashes, and the execution receipt (expires December 1). The inputs were actual original-USA artifact 14184488104, producer `05701c1d19389e90c86b8294a78e4d2ede95183b`, and native artifact 14181849776, producer `150a0199853b514928803b552e6fd73b642e0ede`. Both are 256×224 captures. This experiment reuses authentic captured bytes; it is not a self-test.

## Actual observed result

For original/native checkpoint indices 899/899 (guest frames 1935/1945), 55,571 green values differ. For indices 902/900 (guest frames 1938/1948), 55,570 differ. Previous genuine RGB comparisons found zero red and blue mismatches and identical 29,877-pixel change masks. Guest-frame registration and input-timeline equivalence are **not established**.

For frame 899, original green values classify as 56,743 compatible with both six-bit expansion mappings, 601 compatible only with bit replication, **zero** scaled-only and **zero** neither. Native values classify as 1,774 both, 601 scaled-only, **54,969 neither** (the 224×256 total is 57,344). For the second pair native has 54,964 neither, 606 scaled-only, and 1,774 both; original has 56,738 both and 606 replication-only. The two mappings tested are `(v << 2) | (v >> 4)` and `(v*255+31)//63` for v=0..63.

At pixel (0,0), the real original green byte is 166 and native is 165, while red and blue agree. `166` is representable as a six-bit green expansion (`v=41` yields bit replication 166); `165` is representable as a five-bit channel expansion (`v=20` yields `(v<<3)|(v>>2)=165`). **Hypothesis:** the original producer preserves RGB565's six-bit green, whereas native BGRX output expands five-bit SNES green directly. This is a capture/pixel-format quantization hypothesis, **not** proof of native PPU incorrectness. Native's 54,969 values outside either six-bit mapping strongly support testing it.

## Required corrective execution

1. Locate the exact native framebuffer BMP producer and original Snes9x RGB565→BGRX dump conversion. For a genuine mismatched coordinate capture the pre-conversion SNES BGR555/CGRAM or PPU output value and both producer paths. Verify whether native `(g5<<3)|(g5>>2)` versus original's six-bit intermediate `g6=(g5<<1)|(g5>>4)` explains all differences; do not assume this formula without checking source and samples.
2. On a new source-bound `experiments/*` branch from fresh main, capture or re-acquire actual original/native frames with authenticated provenance. Report exact counts of native values compatible with five-bit replication, source g5→output correspondence, and residual mismatch after **comparison-only** normalization, including first residual pixel coordinates.
3. Only then change the responsible output/capture conversion if the reference convention and display contract justify it. Rerun real bytes and separately resolve original 1935→1938 versus native 1945→1948 absolute phase and input registration.
4. Do not credit a course: 0/45 remains until complete independent USA behavioral qualification.

No gameplay or renderer correction is claimed by this evidence commit.
