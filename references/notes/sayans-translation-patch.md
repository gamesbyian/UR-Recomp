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
