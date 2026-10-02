# TCRF unused-content reconciliation

Source page: The Cutting Room Floor, `Uniracers` article, supplied by the user on 2026-10-02.

This intake preserves the externally published files as **reference evidence**, not project-owned shipping assets. Claims from the page remain secondary-source leads until reproduced against the project's ROM/runtime corpus.

## Preserved artifacts

Repository paths retained by this intake:

- `reference/imported/tcrf/Uniracers-Decomp.png` — unused boot graphics containing the text `used by decomp`.
- `reference/imported/tcrf/Uniracers1.ogg` — preferred upstream TCRF unused song 1 when the one-shot upstream fetch succeeds.
- `reference/imported/tcrf/Uniracers2.ogg` — preferred upstream TCRF unused song 2 when the one-shot upstream fetch succeeds.
- `reference/imported/tcrf/user-supplied-transcodes/Uniracers1.ogg.mp3` — user-supplied MP3 derivative retained for provenance/reference, not canonical audio evidence.
- `reference/imported/tcrf/user-supplied-transcodes/Uniracers2.ogg.mp3` — user-supplied MP3 derivative retained for provenance/reference, not canonical audio evidence.
- `reference/imported/audio/Uniracers.sf2` — Musical Artifacts artifact 8387, a fan-made Uniracers SoundFont supplied separately by the user.

The intake workflow records exact upstream SHA-256 values in the imported-corpus manifest. The user-supplied copies seen in chat had these hashes:

- `Uniracers-Decomp.png`: `e632ad3a504f52c6ecc8076010c2538d6741115b73fc1cea4c161ff34cd03625`
- `Uniracers.sf2`: `e6e05bd70a6d04dd131c2aa579622a22f589d0f7886f3af3ef6a24f7c819c2c4`
- `Uniracers1.ogg.mp3`: `2d604a47c06fddbbbad53f064c289faa07e454182be7597f9bdd3ae364e95173`
- `Uniracers2.ogg.mp3`: `00cd6be4330ffb503fd5726858734a2ebf5e16825ae2424d3e580ca25c06711e`

The two chat audio copies are MP3 transcodes/wrappers. They are preserved under `user-supplied-transcodes/` so the supplied evidence is not lost, but the upstream TCRF OGG files remain the preferred canonical reference whenever acquired.

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

## Manual duplicate cleanup

The root-level `Uniracers_USA.pdf` supplied alongside this intake was byte-identical to the already preserved `reference/imported/manuals/Uniracers-USA-manual.pdf` (Git blob `a52da4f94a75e3e76fd61a759cb8e0c3a4fbc5d3`, SHA-256 `50d5d02a3f8f04b9a38a1dac7ff05fd96f5583fbdf1d0afc201bbaea454e2235`). The duplicate root copy was removed; the existing archived manual remains authoritative.

## Completed binary intake

The first TCRF-direct runner attempt was blocked by HTTP 403 before writing binaries. The repaired intake preserved the source-quality audio corpus from Zophar's copy of the same KungFuFurby rip, including the complete SPC archive. The chat-supplied MP3 derivatives remain fingerprinted above for identity comparison.

| Repository file | Bytes | SHA-256 |
|---|---:|---|
| \`reference/imported/audio/zophar/91 Unused Song 1.mp3\` | 2766175 | \`dc61b18399fc24a21de3b9be264a6a0ae37deb82f7f16f7a71ff501b4cb9e76e\` |
| \`reference/imported/audio/zophar/91 Unused Song 2.mp3\` | 9203791 | \`c1ead84f99aa30d41ead5537af03d3748d5a81e7c0e40e789537d39686322959\` |
| \`reference/imported/audio/zophar/Uniracers (EMU).zophar.zip\` | 491821 | \`85a3f00cfe46cddd18caa714374ef54da6835f0d293557ce499de352b8d4fdb0\` |

TCRF continued to block automated retrieval of the raw \`Uniracers-Decomp.png\` media file. The user-supplied rendered copy remains fingerprinted in this note; the ROM itself remains the authority for reproducing the underlying unused tile graphic.

Musical Artifacts blocked automated retrieval of artifact 8387 from the runner. The exact user-supplied SoundFont remains fingerprinted above pending direct-byte ingestion through a binary-capable route.
