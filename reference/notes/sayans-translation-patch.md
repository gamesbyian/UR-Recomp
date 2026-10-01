# Sayans Traductions Uniracers patch

Recovered: 2026-09-29

## Provenance

The Sayans Traductions historical site survives as a GitHub repository:

- repository: `romhackhispano/sayans.romhackhispano.org`
- pinned revision: `442d2f97bcf5e5d2e37af0ab303c367d96b9b2a7`
- original path: `old/traducciones/snes/uniracers/uniracers_esp.zip`
- original archive Git blob SHA-1: `b3a25f6e3f00f2314b4ce83804c0d2902ca3c2dc`

The repository copy preserved here has the same Git blob SHA-1, establishing exact byte identity with the upstream mirror.

Primary release-page evidence identifies the translator as `alias` and describes the March 28, 2002 release as 85% complete. Later indexes describe a Sayans 1.0b release, so treat those as distinct version-history evidence until the later patch itself is recovered.

## Preserved artifacts

### `uniracers_esp.zip`

- size: 1,261 bytes
- SHA-256: `828f65e6c0362f0050fbcf54925fa51c4ad43fb4750dbf2ce849b6c48b20f6c2`
- SHA-1: `ac3e7da98bf9da02fe9ac7ac4b634fbb8a77ac6f`
- MD5: `63286b25a0bf73d4bf2f4a656c43b6df`
- Git blob SHA-1: `b3a25f6e3f00f2314b4ce83804c0d2902ca3c2dc`

The ZIP contains one file, `Uniraceresp.ips`.

### `Uniraceresp.ips`

- size: 1,678 bytes
- SHA-256: `db68d50f647db678c31ee2d1ac84d9108292684d444d3b899abbbca88664bdd7`
- SHA-1: `4b4539a980329ebeb423155df873473aba2239ba`
- MD5: `549fb30836a2fb5a000c06f5f2c9c9b2`
- Git blob SHA-1: `0c6b89d94c8e1b06f940c14f70a9ea952315c4c3`

## IPS-only structural findings

The patch contains:

- 83 literal IPS records;
- 0 RLE records;
- 1,255 encoded write bytes;
- no IPS truncate extension.

The touched records cluster into three LoROM banks:

| LoROM bank | Records | Encoded bytes | File-offset span |
| --- | ---: | ---: | --- |
| `$80` | 48 | 903 | `0x000D89` through `0x007E60` |
| `$83` | 7 | 25 | `0x01830C` through `0x018407` |
| `$97` | 28 | 327 | `0x0BCC18` through `0x0BD87C` |

Many payloads are directly readable Spanish UI/gameplay text, including player/menu prompts, records/route labels, result phrases, cheat/help text, and other frontend strings. That is strong evidence that these ranges participate in player-facing text storage.

Do **not** infer that every touched byte is text. Some records contain non-printable values mixed into otherwise readable strings and the small bank-$83 edits are especially worth checking against the canonical ROM before assigning a semantic role.

## Next discriminator

Run the project-owned IPS analyzer against `reference/roms/retail/Uniracers_USA.sfc` and preserve a compact report containing:

1. actual before/after bytes and changed-byte count;
2. canonical LoROM addresses;
3. printable-text classification;
4. suspected pointer/index, font/graphics, header/checksum, or executable-code edits;
5. overlap with existing symbols, known RNC streams, and other mapped data.

Only after that comparison should any range be promoted into `docs/SYMBOLS.md` or another subsystem authority.

## Canonical USA comparison

The one-shot canonical-ROM analysis completed successfully against the verified USA retail baseline.

Durable compact result:
`analysis/generated/sayans-translation-summary.json`

Exact identities:

- canonical USA SHA-256: `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`
- patched-result SHA-256: `02901ab98e46df05d457ea1dac8bd62957e55cb5f6817fffbea1d724cae9f720`
- patch records: 83
- encoded write bytes: 1,255
- actual bytes changed against the canonical ROM: 1,187

Bank-level result:

| LoROM bank | Records | Encoded bytes | Actual changed bytes |
| --- | ---: | ---: | ---: |
| `$80` | 48 | 903 | 900 |
| `$83` | 7 | 25 | 25 |
| `$97` | 28 | 327 | 262 |

Payload inspection materially sharpens the interpretation:

- all 83 records contain at least one ASCII letter;
- 65 records are entirely printable;
- 18 mix readable text with 121 control/non-printable bytes;
- 14 records intentionally retain one or more bytes already present in the canonical ROM;
- the heuristic's lone `binary/unknown` record is still visibly translated text interspersed with control bytes.

This is strong evidence that the recovered 85% patch is overwhelmingly a text/control-data edit across three ROM clusters. No pure binary-only record was found, so this patch does **not currently provide evidence** for a separate font-graphics edit, pointer-table rewrite, header/checksum update, or executable-code-only patch. That is an evidence statement about this patch, not proof those structures do not exist elsewhere.

The next useful local question is therefore narrower: identify the reader/renderer routines and control-byte semantics for these three text clusters, or recover the later Sayans 1.0b / independent Sinister patch to see whether either translation had to modify additional structures.


## Control-byte vocabulary and reader candidates

The 85% Sayans patch now has a derived control-byte grammar report at
`analysis/generated/sayans-control-byte-vocabulary.json`.

Across the 83 IPS records, the translated payloads contain 121 non-printable
bytes. None of those 121 bytes is preserved byte-for-byte from the USA ROM at
the same patched location, so the useful evidence is the **new translated
stream grammar**, not a claim that the patch merely retained original inline
controls.

Recurring translated control runs include:

- lone `FF` terminator/separator candidates;
- `FF FC 10` (4 occurrences);
- `FF FC 0D` (3);
- `FF FC 16` (3);
- `FB FC 0D` (2);
- `FF FC 01`, `FF FC 13`, and `FF FC 17` (2 each);
- an ordered five-entry family
  `F3 00 FF FE 06 0D`,
  `F3 01 FF FE 02 10`,
  `F3 02 FF FE 04 13`,
  `F3 03 FF FE 04 16`,
  `F3 04 FF FE 06 19`.

These patterns strongly suggest a compact text/layout/control language, but no
byte has been promoted as newline, terminator, color, position, length or
selector solely from frequency.

A ROM-wide heuristic scan for immediate compares against the high control
vocabulary (`F2/F3/F8/FB/FC/FE/FF`) produced a particularly strong candidate
around `03:8975`: within a compact sequential-byte loop it explicitly compares
against `FC`, `FF`, and `FB`, while ordinary bytes are dispatched through
`00:8C41`. Related compare loops occur around `00:C4BC`, `00:C5D3`, and
`03:AA36`. This is now a bounded reader-disassembly target, not yet a promoted
symbol.

Durable evidence:

- `analysis/generated/sayans-control-byte-vocabulary.json`
- `analysis/generated/sayans-reader-candidates.json`
- `tools/analyze_translation_controls.py`
- `tools/scan_text_control_reader_candidates.py`

The next discriminator is bounded 65816 disassembly plus callsite mapping for
`03:8975`, its ordinary-byte callee `00:8C41`, and the related loops. Reader
semantics should be named only if control flow supports the translated grammar.


### FC layout handler and character metadata

Bounded 65816 analysis has now promoted the strongest static reader candidate.

At `03:8971`, `Text_HandleFCPositionControl`:

- preserves the incoming accumulator and recognizes low-byte `FC`;
- consumes the following parameter byte;
- scans the following character stream until `FF` or `FB`;
- sends ordinary character bytes through `00:8C41`;
- computes `parameter * 32 + horizontal adjustment` and stores the resulting tilemap-style offset in DP `$9F`.

That is strong evidence that the translated `FF FC xx` / `FB FC xx` forms encode a positioned/centered line transition on a 32-column tilemap. The exact user-facing meaning of each `xx` value remains intentionally unnamed.

The shared helper at `00:8C41`, promoted as `Text_TestCharacterMetadataBit7`, indexes `00:C6F8` by character code and tests bit 7. It has four direct callsites: `00:8C3D`, `00:C4CB`, `00:C510`, and `03:8998`. The metadata table's SHA-256 is `0b32a02cb81e5d0eac9334f247bfe627369408000a726fab2cd0a3a858d76302`.

Printable-table inspection shows that uppercase A-Z are bit-7 clear while lowercase a-z, digits, and much punctuation are bit-7 set. This disproves the tempting but unsupported "bit 7 = glyph width" label. The helper is retained as a character-class/metadata test until rendering evidence explains the visual consequence.

The related loops around `00:C4BC`, `00:C5D3`, and `03:AA36` remain useful follow-up targets for the remaining `FB/FF/F2/FC` grammar.

Durable semantic summary:

- `analysis/generated/sayans-text-layout-semantics.json`
