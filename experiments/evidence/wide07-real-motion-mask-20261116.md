# WIDE-07 genuine moving-frame motion-mask comparison (2026-11-16)

Source-bound independent analysis of retained GitHub Actions artifacts, performed in the isolated analysis container (not the owner's PC). No new emulator execution or acceptance is claimed.

- Original USA: [run 43772817330](https://github.com/gamesbyian/UR-Recomp/actions/runs/43772817330), artifact 14184488104, SHA `05701c1d19389e90c86b8294a78e4d2ede95183b`; `evidence/atlas-899/ws-product-atlas-899.fb.bgrx` and `evidence/atlas-902/ws-product-atlas-902.fb.bgrx`, original reported guest frames 1935 and 1938.
- Native: [run 43767096090](https://github.com/gamesbyian/UR-Recomp/actions/runs/43767096090), artifact 14181849776, SHA `150a0199853b514928803b552e6fd73b642e0ede`; `evidence/native-899/state.fb.bmp` and `evidence/native-900/state.fb.bmp`, native reported guest frames 1945 and 1948.
- Both sequences are 256 × 224 pixels. Decode original as BGRX8888 (ignore X); decode native 24-bit BMP with row-stride and bottom-up orientation. A pixel is changed when any B, G, or R byte differs from its own engine's previous capture.
- Observed original changed pixels: **29,877**; native changed pixels: **29,877**; intersection: **29,877**; union: **29,877**; original-only: **0**; native-only: **0**; Jaccard: **1.0**.
- Absolute original/native BGR equality: **1,773 / 57,344** pixels at the first pair; **1,774 / 57,344** at the second. The earlier measured deterministic green-channel conversion discrepancy explains why motion-mask identity must not be misrepresented as colour equality.
- Frame numbers differ by ten between engines. These captures demonstrate matching spatial change support over each engine's three-frame interval, **not** proof of absolute phase alignment, identical per-frame timing, identical RGB values, full-course behavior, or a USA course acceptance.
- Independent acceptance stays **0/45**.

Next experiment: collect ordered genuine original/native captures at *each consecutive guest frame* around this moving interval, with producer-specific frame-counter receipts; test shift candidates on per-frame motion masks rather than equating three-frame input durations. Pass: unique phase alignment with repeatable image evidence and a justified colour-conversion correction. Fail: ambiguous shift or divergent masks, then isolate the first divergence at exact source SHA.
