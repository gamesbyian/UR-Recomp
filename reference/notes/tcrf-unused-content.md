# TCRF unused-content reconciliation

Source page: The Cutting Room Floor, `Uniracers` article, supplied by the user on 2026-10-02.

This intake preserves the externally published files as **reference evidence**, not project-owned shipping assets. Claims from the page remain secondary-source leads until reproduced against the project's ROM/runtime corpus.

## Preserved artifacts

Expected repository paths after the one-shot intake workflow completes:

- `reference/imported/tcrf/Uniracers-Decomp.png` — unused boot graphics containing the text `used by decomp`.
- `reference/imported/tcrf/Uniracers1.ogg` — TCRF unused song 1.
- `reference/imported/tcrf/Uniracers2.ogg` — TCRF unused song 2.
- `reference/imported/audio/Uniracers.sf2` — Musical Artifacts artifact 8387, a fan-made Uniracers SoundFont supplied separately by the user.

The intake workflow records exact upstream SHA-256 values in the imported-corpus manifest. The user-supplied copies seen in chat had these hashes:

- `Uniracers-Decomp.png`: `e632ad3a504f52c6ecc8076010c2538d6741115b73fc1cea4c161ff34cd03625`
- `Uniracers.sf2`: `e6e05bd70a6d04dd131c2aa579622a22f589d0f7886f3af3ef6a24f7c819c2c4`
- `Uniracers1.ogg.mp3`: `2d604a47c06fddbbbad53f064c289faa07e454182be7597f9bdd3ae364e95173`
- `Uniracers2.ogg.mp3`: `00cd6be4330ffb503fd5726858734a2ebf5e16825ae2424d3e580ca25c06711e`

The two chat audio copies are MP3 transcodes/wrappers; preserve the upstream TCRF OGG files in Git instead of treating those chat derivatives as canonical.

## Claims to reconcile locally

The TCRF article provides concrete, falsifiable leads:

- SRAM anti-piracy comparison involving `$770000` and ROM `$838000`, followed by the destructive/crash path at ROM offset `0x70800B`.
- unused boot graphics saying `used by decomp`, reportedly loaded before the character-select unicycle graphics overwrite that VRAM region;
- the placeholder **Error Tour**, selected through `$7E00CE2D..$7E00CE31`, with placeholder races named `Unavailable`;
- unused ninth combo-message set at ROM offset `0x0BD679`;
- version string `ASJIver3.30` at ROM offset `0x18000`, reported to be copied into SRAM;
- build-date strings at ROM offset `0x541`;
- banned-name behavior and unused names/content;
- unused music PAR patches selecting records `$3B` and `$3D`.

## Audio convergence

The external music selectors are particularly valuable because they independently converge with the project's ROM-derived audio archaeology.

Current local evidence already establishes:

- `0x3B` matches preserved **Unused Song 1** and lacks an ordinary setup call;
- `0x3D` matches preserved **Unused Song 2** and lacks an ordinary setup call;
- those are the only reachability gaps in the otherwise populated `0x38..0x42` song-record family;
- package correlation currently points to `03:FB15` for unused song 1 and `03:FB55` for unused song 2.

TCRF's reported title-screen PAR patches therefore serve as independent corroboration, not implementation authority. Reconcile their exact patch semantics against the canonical ROM before promoting any additional package/setup interpretation.

## Rights/provenance posture

TCRF page text is CC BY 3.0 unless otherwise noted by the site. Media embedded on the page may retain separate underlying rights. Musical Artifacts metadata and hosted files likewise have file-specific licensing. All imported binaries here are quarantined research references pending any separate redistribution/shipping review.
