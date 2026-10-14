# QA-08: seven real channel5 mode1 $2133 SETINI companion bytes

**Pending exact native AOT observation and strict acceptance.** The previously
merged graphics source proof #1461/#1474 captured only the COLDATA first half
of SNESRecomp channel5 mode1 direct HDMA in native USA 2P guest frame2208.
The source-backed audit #1487 established the other half of each mode1
transfer targets the adjacent **$2133 SETINI** register and uses one more
byte of the same direct WRAM table. However, **actual native $2133
bytes have not been measured**.

The independent original-Snes9x two-player
[run 38510398955](https://github.com/gamesbyian/UR-Recomp/actions/runs/38510398955)
now proved 18 executed WRAM changes, all at original emulator frame1781,
including five actual writer PCs and values for the candidate adjacent
source bytes:

| Native COLDATA source | Mode1 source-predicted SETINI byte | Original Snes9x observed WRAM write | Original executed PC |
| --- | --- | --- | --- |
| 7E:2086 / 2F | 7E:2087 | 01 | 82:D602 |
| 7E:2089 / 40 | 7E:208A | 6D | 82:D608 |
| 7E:208C / 80 | 7E:208D | 01 | 82:D64B |
| 7E:208F / 20 | 7E:2090 | 01 | 82:D64F |
| 7E:2092 / 53 | 7E:2093 | 6D | 82:D655 |
| 7E:2095 / 80 | 7E:2096 | not an observed changed-byte instruction | none |

**This table is original WRAM table-write provenance, not a native $2133
PPU-write or physical-console timing claim.** Even though the original
source values agree exactly for all six independently accepted native
COLDATA bytes, full same-input/frame original-native parity remains
unproven. There is no valid inference from "unmodified zero-filled guest
RAM" to a source-observed 2096 actual PPU value.

## Strict native source test added to the existing factory

The disposable pinned Baldosa/SNESRecomp source patch
`tools/qa08_patch_hdma_coldata_source.py` now observes **both**
real BBUS transfer paths, unchanged and strictly optional under
`UR_QA08_HDMA_COLDATA_FRAME=2208`:

- The preexisting $2132 original/native COLDATA source log is untouched.
- A new `UR_QA08_HDMA_SETINI` source line only for channel5 and
  BBUS address 0x33 records the *actual* $2133 byte, A-bus
  source bank/address, channel, mode, direct/indirect flag, HDMA
  table cursor, original PPU write-log tag and **PPU setini after write**.
- Both source probes are read-only; no native guest data, PPU register,
  DMA timing, graphic asset or renderer behaviour is changed.

The new
`tools/check_qa08_native_hdma_setini_source.py` requires the
preexisting **seven strict native COLDATA source records** plus the
**78 original 2P BG3/OBJ PPU compositor records and all 2,473 original
guest CRC entries**. It checks exactly seven native SETINI records in
the same old stock original 2P run, matching each measured COLDATA
source tag and requiring that the actual second source address is
first-plus-one. It verifies actual PPU after-write SETINI equals the
native BBUS byte and fails closed on unexpected mode, channel,
source bank, timing tag, truncation or source colour receipt.

The checker **reports rather than assumes** whether each of the
five independently observed original Snes9x WRAM values agrees with
the actual native SETINI source byte. An original/native mismatch
at those addresses would be a concrete follow-up discrepancy,
not an invitation to weaken the original-raster or other native
acceptance comparator.

One existing pinned AOT run; no new game process or cumulative factory.
On success retain
`baldosa-evidence/ws342_native_mode1_setini_2208.json`.
**Unclosed:** all unsampled racer pixels, independently timed physical
SNES HDMA, original-vs-native paired replay full parity, and artist
approval for any replacement HD racer. Original 256x224 and 7:6 PAR,
342-wide real world and exact 4x Original fallback remain unchanged.

## Exact-head native negative, 2026-10-13

[Run 38511429620](https://github.com/gamesbyian/UR-Recomp/actions/runs/38511429620), pinned native job 115680598480, is **red** for this newly proposed discriminator. The existing strict original PPU field, 2-pixel main BG3/sub OBJ, all **78** 26-intersection compositor source records, 2,473 guest CRCs and seven genuine COLDATA source bytes **all passed** first. The subsequent new SETINI checker failed at `not precisely seven genuine original-native SETINI write records`.

The actual archived stock native 2P route log, retained in artifact **11870196499**, contains **zero** `UR_QA08_HDMA_SETINI` records. This is a **negative for the new observer's stated source witness**, not proof that physical SNES channel5 never wrote SETINI. Do not infer the supposed companion bytes from original Snes9x WRAM values or the channel5 mode field, and do not pass or merge the new native acceptance until the failure is source-adjudicated. In particular, inspect the disposable DMA source's actual second transfer destination and the write-source tagging at `dma_transferByte`, including the distinction between observed source channel5 mode1 and an actual BBUS33 register write. The report's expected seven records are a **test hypothesis**, not accepted native history.

The separate failing unit assertion was an **error-message regex mismatch** in adversarial fixture testing: the strict checker correctly threw `genuine paired SETINI address/channel/PPU state differs`; the test only allowed `source|record`. This test wording has been corrected without relaxing a single register, source-address, original-pixel or native CRC gate. No release acceptance or physical hardware finding is supported by the failing experiment.

