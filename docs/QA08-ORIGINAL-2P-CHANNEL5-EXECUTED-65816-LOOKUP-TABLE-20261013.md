# QA-08: executed original 65816 colour-HDMA table builder

**Source-captured actual original USA guest code, not speculative reverse engineering.**

The opt-in true-original Snes9x run
[38516727525](https://github.com/gamesbyian/UR-Recomp/actions/runs/38516727525),
artifact **11871652978**, ran the exact pinned 2P controller route
through original frame2473, with confirmed real second camera
$0DDB=1 and in-race flag $0313=1. A read-only **before-execution**
opcode probe captured **55 original USA ROM instructions** in bank
$82:D5C0..D66F at actual original frame1781, including all
**18 independently proven WRAM writer PCs** from the ten-window
source change census [#1493](https://github.com/gamesbyian/UR-Recomp/pull/1493).

Source ZIP SHA256: 45b4d1f2275a78698c18697adcee3490cfe0f27537e089c638d33c29ac9d8611.
Uncompressed opcode JSON SHA256:
724a89124d5b18d53b89803fc3f64716e136b1901d7d0c49b44fac70f8c7a090.
Original final WRAM SHA256:
9350bcb02f3cbf490678c5276245ec2c7fe36b9078bfab9e912d86c5cbc93bf6.

A compact, human-readable and machine-readable extraction containing
**all 55 original executed instruction bytes**, every one of the
18 genuine original WRAM writer instructions, and six HDMA descriptor
triplets is retained in
analysis/data/qa08-original-2p-channel5-executed-opcode-table-layout.json.
No ROM, save or raw WRAM image is committed.

## Four-byte indexed source ROM lookup

The directly executed original USA instruction sequence includes:

| Original CPU PC | Real opcode bytes | 65816 instruction and source meaning |
|---|---|---|
| $82:D5CD | AF 48 07 77 | LDA long $77:0748, first selection value |
| $82:D5D1..D5D3 | 0A 0A AA | ASL A twice; TAX: index = selection multiplied by four |
| $82:D5D4 | BF 2A D5 82 | LDA long indexed X from $82:D52A |
| $82:D5D8 | 8F 86 20 7E | STA long $7E:2086, first COLDATA red byte |
| $82:D5DC..D5E8 | BF ... / 8F ... | LDA from $82:D52B and +2, STA $7E:2089/208C |
| $82:D5EC..D5F8 | BF 2D D5 82 / 8F ... | LDA fourth lookup byte then STA $7E:2085/2088/208B: all CGADSUB=04 |
| $82:D5FC..D608 | A9 01 / A9 6D, 8F stores | Construct the 01,01,6D upper HDMA count bytes |
| $82:D60C | AF 50 07 77 | LDA long $77:0750, actual original selection/flag |
| $82:D610 | 89 08 | BIT immediate #$08 |
| $82:D612 | F0 06 | BEQ +6. **Not taken in this original execution** |
| $82:D614 | AF 49 07 77 | Actual fallthrough loads $77:0749 as second selection |
| $82:D618 | 80 04 | BRA to $82:D61E, skipping unobserved alternate path |
| $82:D61E..D621 | 0A 0A AA / BF 2A D5 82 | Multiply second selection by four and load same four-byte ROM lookup |
| $82:D625..D645 | 8F / BF instructions | Actual second-view $7E:208F/2092/2095 COLDATA and $7E:208E/2091/2094 CGADSUB |
| $82:D649..D655 | A9 01 / A9 6D and 8F | Construct second view HDMA count bytes 01,01,6D |

**The 18 original change-bracketed WRAM writers are all opcode
8F = STA absolute long**, each with the literal destination
$7E:2084..2095 encoded in its actual four original ROM bytes.
This establishes an executable source relationship between
a **four-byte table entry at $82:D52A + 4×selection**,
upper/lower selection flow, and the exact direct-mode HDMA table
that had been observed transferring bytes in the pinned native PPU.

The source observation does not yet reveal the values of the
original ROM palette lookup **for every possible selection**.
It proves only the two *executed* selection paths in this original
script. The untaken BEQ branch targets $82:D61A, which was
not executed in this trace, so its semantics and fallback choice
must **not** be invented.

## Six independently crossed direct HDMA descriptor triplets

Original emulator full-route writer bytes, source-mapped to the
independently accepted channel5/mode1 native paired register writes:

| WRAM descriptor | Header byte | Second byte: $2131 CGADSUB | Third byte: $2132 COLDATA |
|---|---|---|---|
| $7E:2084..2086 | 01 | 04 | 2F red15 |
| $7E:2087..2089 | 01 | 04 | 40 green0 |
| $7E:208A..208C | 6D | 04 | 80 blue0 |
| $7E:208D..208F | 01 | 04 | 20 red0 |
| $7E:2090..2092 | 01 | 04 | 53 green19 |
| $7E:2093..2095 | 6D | 04 | 80 blue0 |

The values 01,01,6D / 01,01,6D are actual **original
executed-game writes**, not visually reconstructed line counts.
Pinned SNESRecomp DMA source reads a descriptor header as
repCount, then for mode1 writes two adjacent BBUS registers and
decrements repCount on each HBlank. A header value 6D means
109 lines without the high repeat bit. In the native source log,
the red upper colour is established by tags 2–4 and remains
until tags 113–115 set lower green, with a separate before-first-
line prime that duplicates the initial two register writes.
No source-observed write to $7E:2096 was recorded; **do not
upgrade an unchanged zero-filled byte into a proven guest
instruction or physical termination write**.

Native acceptance was not inferred from this table alone:
pinned AOT [38514112274](https://github.com/gamesbyian/UR-Recomp/actions/runs/38514112274)
independently source-observed all seven **$2131=04** writes,
and pinned AOT
[38504531564](https://github.com/gamesbyian/UR-Recomp/actions/runs/38504531564)
independently observed all seven actual $2132 COLDATA writes.
All 2,473 guest CRC records and 26 actual BG3-main/OBJ-subscren
text-intersection pixels were accepted in the source geometry runs.

## Research consequences and limits

This original ROM lookup is a strong **identity/palette-source
archaeology handle** for future source-grounded HD art. A faithful
reconstruction can read original selector/index and CGRAM/PPU
source, rather than painting baked red HUD pixels into racer
images. It does **not** authorize any existing procedural HD
character for shipping: the owner has rejected that likeness,
and human art approval remains necessary.

The original source study was at **original emulator frame1781**,
not assumed equal to Baldosa guest frame2208. Neither native-
original full same-input per-frame parity nor physical SNES
midscanline timing has been established here. This work is
**analysis only**, with no gameplay/oracle, Modern, release QA,
ROM patch, compositor, widescreen, authentic 256x224/7:6 PAR,
or exact 4x Original fallback changes.

Next source question: identify actual original selector values
at $77:0748/0749 and recover the real ROM lookup table entries
for independently rendered racer identities. A bounded original
read-only selector-register probe should precede any inferred
new pose, skin or colour.


## Machine-checked cross-evidence chain (2026-10-13)

\`tools/check_qa08_channel5_source_to_pixel.py\` now consumes four **already
accepted, independent, retained** source artifacts: this run's 55 fetched
opcodes and 18 STA-long writers; the ten-process original Snes9x WRAM
write-census; the pinned native channel-5 seven-write COLDATA handoff;
and the genuine 26-pixel BG3/OBJ original PPU palette fingerprint.
It performs a narrow **cross-validation**, not a new guest execution or
an original-vs-native same-frame pixel comparison.

The crosscheck rejects bad ROM identity, original frame 1781, native frame
2208, changed route/WRAM fingerprints, a missing/aliased original writer
PC, invalid \`8F\` long store operands or destination, a broken observed
upper/lower palette lookup branch, any of the 18 original descriptor bytes,
incorrect channel-5 direct mode-1/native source address, one of seven
actual COLDATA values/tags, inconsistent post-transfer live fixed RGB15,
and the separately source-measured 26-pixel BG3/OBJ colour fingerprint.
Duplicate evidence JSON object keys are forbidden.

The source-to-register-to-pixel bridge is independently measurable at
two native original-source coordinates:

| Native row | Latest actual COLDATA write before that row | Live PPU fixed RGB15 | Independent BG3/OBJ pixel source observation |
| --- | --- | --- | --- |
| 50, upper | \`$7E:208C = $80\` at DMA tag 4 | \`$000F\`, red15 | 13 upper overlap pixels, fixed red15, after upper OBJ98 deletion red5=28 |
| 162, lower | \`$7E:2095 = $80\` at DMA tag 115 | \`$0260\`, green19 | 13 lower overlap pixels, fixed green19, after lower OBJ96 deletion RGB5=(13,19,0) |

The per-line ordering is specifically the *pinned native renderer's*:
normal native tag L is written after output row L−2 and before row L−1.
The tag-0 first-line prime is separate; six original source descriptors
cause seven actual native COLDATA writes. \`$2132\` is a **component-enable**
write, not an all-channel RGB assignment: the checker applies independent
red/green/blue masks to the previously observed *live* register value and
requires each subsequent live PPU readback to agree. Source-side
\`$2131 CGADSUB=04\` companion writes were separately executed and
accepted by #1491. No caller should substitute the CPU-side raster journal
for those live HDMA effects. The formerly suggested \`$2133 SETINI\`
mode-1 companion has been disproved; mode 1 starts at BBUS \`$31\`,
so it writes \`$2131 CGADSUB\` then \`$2132 COLDATA\`.

Re-run on the source-backed compact evidence without downloading a ROM:

\`\`\`sh
python3 -m unittest tests.unit.test_qa08_channel5_source_to_pixel -v
python3 tools/check_qa08_channel5_source_to_pixel.py \
  --layout analysis/data/qa08-original-2p-channel5-executed-opcode-table-layout.json \
  --census analysis/data/qa08-original-snes9x-2p-channel5-eighteen-writer-PCs.json \
  --native analysis/data/qa08-original-native-channel5-hdma-coldata-source-handoff.json \
  --pixels analysis/data/qa08-2p-original-native-text26-obj-palette-fingerprint.json \
  --out /tmp/qa08-channel5-crosswalk.json
\`\`\`

This additional validator crosschecks the **summaries and their source
artifact hashes**; it does not rehash the underlying archived ROM, opcode
ZIP, finished raw P7 image or 78 raw compositor observation lines. For
acceptance requiring those bytes, rerun the existing original/native
source tests on an exact pinned build and inspect their artifacts. The
26 original pixel source readings are source-accepted but **most racer
pixels, physical timing and full original/native per-frame RGB equality
remain unproven**.

Next high-value original capture remains the selector bytes
\`$77:0748/$77:0749\` at frame1781, the four LUT source bytes read for
each, and a **same-input, same-raster-coordinate original/native live
register/PPU comparison** at the already accepted 26 discriminating
points. A register-only comparison cannot promote final colour.
