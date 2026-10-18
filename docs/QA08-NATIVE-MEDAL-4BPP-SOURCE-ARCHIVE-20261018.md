# QA08: independently reproduced physical native medal OBJ tile provenance
18 October 2026 | **source-only, archived evidence, no product correction**

## Decisive finding

A genuine compiled current Uniracers USA Win32 PE running the authenticated
RF017 5,484-guest-frame two-pad route captured the source PPU's actual
nontransparent sprite 4bpp decode and writes at five previously identified
medal coordinates across five host frames (4032,4048,4064,4080,4176).
The Windows run [39123459879](https://github.com/gamesbyian/UR-Recomp/actions/runs/39123459879)
was marked **failed** because its *post-run parser* incorrectly compared the
physical encoded OBJ zbuffer to a CGRAM colour word. The original raw
binary/PPU events survived in artifact **12134793278**.

The actual source ZIP SHA-256 is
`725ef03df3d43ff5d30b4bea944e32555974fb0b0e01af025da76ef88959b408`,
containing only `baseline/log.txt` SHA-256
`ff0ca813911fb4b8d3c61cadc358df49e8b409e82eae9619956a09ce3433a602`.
The real original native source contains exactly 25 actual physical
4bpp writes, 25 effective PPU pixel-owner records, 175 OAM-line
entries and 276 actual CGRAM port writers. At **all 19 OBJ-main**
positions, the last real decoded 4bpp OAM sprite write's encoded
pixel/priority/palette word equals the **same guest, same raster**
effective PPU OBJ zbuffer, byte-for-byte. The other six samples
are BG1-main and contain zero real OBJ writers. Six OBJ-main coordinates
contain two genuine writes; the lower-index OAM sprite overwrites
the earlier slot according to the pinned PPU logic.

**A previously apparent renderer disagreement was an instrumentation error.**
The current pinned PPU calls `ppu_evaluateSprites(ppu,line-1)`;
its physical sprite evaluator sees zero-based `raster_y`, while the later
legacy compositor observes `ppu_line=raster_y+1`. The first experimental
trace mistakenly observed the *next* sprite row. Even after that was fixed,
the second parser compared `obj_word` (the observed CGRAM RGB15 **colour**)
against `obj` (the actual 16-bit encoded **OBJ zbuffer**). These
are different values, e.g., native guest4032/x205/y115 has actual OBJ
zbuffer `64e4` but CGRAM pixel colour `0cd1`.

`tools/qa08_verify_archived_native_medal_4bpp.py` independently
replays exactly the retained source zip, without a game build, alternative
PPU renderer, VRAM texture reconstruction, colour adjustment, frame
shift, CPU/APU changes or inferred pixels. It checks outer/member
SHA, all expected true source records, 25 source coordinates, evaluator/
composer +1 registration, original PPU 4bpp bitplane extraction, real
OAM attribute/tile/palette and encoded sprite priority algebra, plus
the final effective zbuffer. A second deliberately non-programming
visual verification may inspect the original 2014 Snes9x screenshot
and independently archived OAM, but **a field-end OAM snapshot does NOT
establish which original sprite was the active pixel writer**.
Native input-source parity, old Snes9x sprite priority and
complete 1P/2P result-screen original source RGB5 equality therefore
remain explicitly **unproven**.

The live source re-run of experimental [#1833](https://github.com/gamesbyian/UR-Recomp/pull/1833)
should also obtain a correctly typed full machine receipt. This source
archive replay independently certifies only the above 25 witnessed pixels
whether or not that newer run finishes, because every retained source byte
is immutable and independently hashed. The failed experiment's log-only
ZIP does **not** include a re-computable full 5,484-entry guest CRC
array: it was checked by its actual Windows route before post-processing,
but this verifier expressly does **not** claim to have recomputed it.

## Resulting source/fix boundary

Actual native OBJ fetch-to-final-buffer agreement rules out the simplistic
hypothesis that the current renderer is choosing the wrong last OAM
sprite or using the wrong 4bpp bits at these 19 sample points. It does
**not** identify the earliest original/native 2014 difference. The two-field
native-original OAM producer timing difference and CPU/NMI source writer
lead remain distinct open causal candidates. **No** global video shift,
manual sprite tile reindex, palette repaint, CGRAM hack, speculative
medal layer fix or CPU clock adjustment follows from this evidence.

Production graphics [#1780](https://github.com/gamesbyian/UR-Recomp/pull/1780)
is separately source-qualified and held for independent acceptance.
The observer remains diagnostic-only, with no source engine modification
permitted into shipping. Modern SRAM #1713, approved HD racer art,
physical 3840x2160/7:6, final Windows OS recovery and
`docs/RELEASE-QUALITY-LEDGER.json` remain with their respective owners.
