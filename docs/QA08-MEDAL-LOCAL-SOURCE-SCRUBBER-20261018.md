# QA08: authenticated local 25-capture medal scrubber

18 October 2026 | source-only original/native visual adjudication utility. **No shipping pixels, ROM files, saved profiles, web dependencies, CPU/APU changes, or release status.**

The merged [original callback registration](QA08-ORIGINAL-MEDAL-CALLBACK-REGISTRATION-20261018.md), [medal 25-field recurrence](QA08-MEDAL-REGISTERED-NEXT-INTERNAL-STAGE-20261018.md), [actual physical sprite winner](QA08-ORIGINAL-NATIVE-MEDAL-OBJ-WINNER-CROSSWALK-20261018.md), and [three-field original-painter transition](QA08-TRUE-ORIGINAL-MEDAL-POSE-BOUNDARY-20261018.md) establish the source facts. They also show why visually comparing native guest frame *f* against original Snes9x internal painter *f* is an **invalid replacement for original video callback f−1**.

An independent QA reviewer can now inspect **all 25 truly archived medal-source appearances** in a single private local HTML with a scrubber, correct original callback label, unchanged native PPU crop and RGB5 large-error mask. No arbitrary timeline offset toggle is offered, and the utility is not an emulator or image editor.

## Exact inputs

- Original 2014 Snes9x **inner** `original.zip` from artifact **12075111053**, SHA256 `72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e`.
- Genuine integrated Windows 263-frame **outer artifact** **12151839452**, SHA256 `832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727`. Its embedded source ZIP must have SHA256 `c36fdd0238735e739219b013d25665e42a008a7827ee97631a322217c9f4f0cd`.

These are already independently certified artifacts, **not** an instruction to build another Windows emulator or re-run 2014 Snes9x.

```sh
python3 tools/qa08_medal_capture_scrubber.py \
  --original /private/qa08/original.zip \
  --integrated /private/qa08/github-artifact-12151839452.zip \
  --out /private/qa08/medal-source-review.html

python3 -m unittest tests.unit.test_qa08_medal_capture_scrubber
```

The stdlib-only generator refuses archive SHA drift, lost original/native full-route and CRC identity, original callback/native guest source labels without **f−1**, original BGRX or native P7 frame SHA drift, cropped/retimed source images, changed source channel layout and overwriting another local HTML. It emits PNG using only standard-library zlib/CRC and embeds source crops in the **local output**. The exact x184..245 / y78..168 crop intentionally includes genuine surrounding pixels for spatial context. The heatmap marks pixels where any RGB5 channel differs by **more than one step**, with other disagreement counts retained separately. Each local HTML is a copyrighted original-artwork derivative: **keep it off Git and public artifacts**. Neither original nor native frame pixels are committed to the repository.

## What it can and cannot establish

Correct-frame original callback f−1 versus native guest f is the only supported movie registration. All 25 captures cover guest **4032..5184 in steps of 48**, with frame manifest identity checked for each. The same imported source route does not itself prove original/native controller consumption, CPU/PPU clock equivalence, guest4016 forced-black cause or seven/28-field palette ingestion. An out-of-step original internal painter coincidence, a grayscale frame alias, or a mask with fewer visibly red pixels must **not** be promoted as a production output shift, tile replacement, recolour or QA08 event pass.

Output is a human-review artifact, **not** the full 263-frame original/native source proof, a physical UHD presentation test, shipping Remastered 3D art, or independent release acceptance. Its main benefit is eliminating subjective visual guesswork while reviewers inspect exactly registered source evidence.
