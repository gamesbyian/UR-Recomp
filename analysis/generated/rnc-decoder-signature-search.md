# RNC1 Decoder Signature Search

Mechanical search for opcode shapes derived from the preserved period `SOURCE/SUPERNES/RNC_1.S`. A hit is a candidate until surrounding code/control flow is checked.

## usa-retail

- entry-loose: `0x00B8F1` (LoROM 01:B8F1)
- entry-dp-sta: `0x00B8F1` (LoROM 01:B8F1)
- makehuff-shape: `0x00BADC` (LoROM 01:BADC), `0x00BE01` (LoROM 01:BE01)
- makehuff-prologue: `0x00BADC` (LoROM 01:BADC)

## europe-retail

- entry-loose: `0x00B8E2` (LoROM 01:B8E2)
- entry-dp-sta: `0x00B8E2` (LoROM 01:B8E2)
- makehuff-shape: `0x00BACD` (LoROM 01:BACD), `0x00BDF2` (LoROM 01:BDF2)
- makehuff-prologue: `0x00BACD` (LoROM 01:BACD)

## legacy-beta

- entry-loose: `0x00B8F1` (LoROM 01:B8F1)
- entry-dp-sta: `0x00B8F1` (LoROM 01:B8F1)
- makehuff-shape: `0x00BADC` (LoROM 01:BADC), `0x00BE01` (LoROM 01:BE01)
- makehuff-prologue: `0x00BADC` (LoROM 01:BADC)

## pal-prototype

- entry-loose: `0x00B8D1` (LoROM 01:B8D1)
- entry-dp-sta: `0x00B8D1` (LoROM 01:B8D1)
- makehuff-shape: `0x00BABC` (LoROM 01:BABC), `0x00BDE1` (LoROM 01:BDE1)
- makehuff-prologue: `0x00BABC` (LoROM 01:BABC)

## Traced writer-site context

Dynamic trace run 36517696016 identified USA writer PCs 01:BA96 and 01:BB73. For the other builds, contexts below use the unpacker-entry displacement so structurally corresponding code can be compared without assuming absolute addresses.

### course-byte-increment: USA offset `0x00BA96`, entry-relative +`0x1A5`

- usa-retail: `0x00BA96` (LoROM 01:BA96): `ba ba 81 25 8f 48 a5 91 a6 93 f0 12 4a 66 8f 88 f0 23 ca f0 09 4a 66 8f 88 f0 1a ca d0 ee 18 a5 82 69 02 00 90 05 09 00 80 e6 84 85 82 20 6f bb a2 10 00 80 d7 ca 86 93 85 91 68 60 00 00 01 00 03 00 07 00 0f 00 1f 00`
- europe-retail: `0x00BA87` (LoROM 01:BA87): `ab ba 81 25 8f 48 a5 91 a6 93 f0 12 4a 66 8f 88 f0 23 ca f0 09 4a 66 8f 88 f0 1a ca d0 ee 18 a5 82 69 02 00 90 05 09 00 80 e6 84 85 82 20 60 bb a2 10 00 80 d7 ca 86 93 85 91 68 60 00 00 01 00 03 00 07 00 0f 00 1f 00`
- legacy-beta: `0x00BA96` (LoROM 01:BA96): `ba ba 81 25 8f 48 a5 91 a6 93 f0 12 4a 66 8f 88 f0 23 ca f0 09 4a 66 8f 88 f0 1a ca d0 ee 18 a5 82 69 02 00 90 05 09 00 80 e6 84 85 82 20 6f bb a2 10 00 80 d7 ca 86 93 85 91 68 60 00 00 01 00 03 00 07 00 0f 00 1f 00`
- pal-prototype: `0x00BA76` (LoROM 01:BA76): `9a ba 81 25 8f 48 a5 91 a6 93 f0 12 4a 66 8f 88 f0 23 ca f0 09 4a 66 8f 88 f0 1a ca d0 ee 18 a5 82 69 02 00 90 05 09 00 80 e6 84 85 82 20 4f bb a2 10 00 80 d7 ca 86 93 85 91 68 60 00 00 01 00 03 00 07 00 0f 00 1f 00`

### decoded-output-write: USA offset `0x00BB73`, entry-relative +`0x282`

- usa-retail: `0x00BB73` (LoROM 01:BB73): `a5 95 a4 9f fa c8 c8 ca d0 ab 46 99 e6 95 c9 10 00 d0 9b 60 a7 82 e6 82 d0 11 38 66 82 e6 84 e2 20 eb a7 82 eb c2 20 c6 84 64 82 c6 82 60 c2 39 a3 04 85 84 a3 06 85 82 8b f4 00 00 ab ab a5 82 69 11 00 90 05 09 00 80`
- europe-retail: `0x00BB64` (LoROM 01:BB64): `a5 95 a4 9f fa c8 c8 ca d0 ab 46 99 e6 95 c9 10 00 d0 9b 60 a7 82 e6 82 d0 11 38 66 82 e6 84 e2 20 eb a7 82 eb c2 20 c6 84 64 82 c6 82 60 c2 39 a3 04 85 84 a3 06 85 82 8b f4 00 00 ab ab a5 82 69 11 00 90 05 09 00 80`
- legacy-beta: `0x00BB73` (LoROM 01:BB73): `a5 95 a4 9f fa c8 c8 ca d0 ab 46 99 e6 95 c9 10 00 d0 9b 60 a7 82 e6 82 d0 11 38 66 82 e6 84 e2 20 eb a7 82 eb c2 20 c6 84 64 82 c6 82 60 c2 39 a3 04 85 84 a3 06 85 82 8b f4 00 00 ab ab a5 82 69 11 00 90 05 09 00 80`
- pal-prototype: `0x00BB53` (LoROM 01:BB53): `a5 95 a4 9f fa c8 c8 ca d0 ab 46 99 e6 95 c9 10 00 d0 9b 60 a7 82 e6 82 d0 11 38 66 82 e6 84 e2 20 eb a7 82 eb c2 20 c6 84 64 82 c6 82 60 c2 39 a3 04 85 84 a3 06 85 82 8b f4 00 00 ab ab a5 82 69 11 00 90 05 09 00 80`

## Cross-build exact bytes around candidate entry hits

### ROM offset `0x00B8D1`

- usa-retail: `a6 0e c0 00 00 f0 0e a8 8a 49 ff ff aa 98 49 ff ff e8 d0 01 1a 60 20 db b8 6b 48 29 f0 4a 85 00 4a 4a 18 65 00 85 00 68 29 0f 18 65 00 85 00 60 c2 39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20`
- europe-retail: `ff ff e8 d0 01 1a 60 20 cc b8 6b 48 29 f0 4a 85 00 4a 4a 18 65 00 85 00 68 29 0f 18 65 00 85 00 60 c2 39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20 60 bb 85 8f 64 93 a9 02 00 20 6b ba a0 20 00`
- legacy-beta: `a6 0e c0 00 00 f0 0e a8 8a 49 ff ff aa 98 49 ff ff e8 d0 01 1a 60 20 db b8 6b 48 29 f0 4a 85 00 4a 4a 18 65 00 85 00 68 29 0f 18 65 00 85 00 60 c2 39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20`
- pal-prototype: `4a 4a 18 65 00 85 00 68 29 0f 18 65 00 85 00 60 c2 39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20 4f bb 85 8f 64 93 a9 02 00 20 5a ba a0 20 00 20 bc ba a0 a0 00 20 bc ba a0 20 01 20 bc ba a9 10`

### ROM offset `0x00B8E2`

- usa-retail: `e8 d0 01 1a 60 20 db b8 6b 48 29 f0 4a 85 00 4a 4a 18 65 00 85 00 68 29 0f 18 65 00 85 00 60 c2 39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20 6f bb 85 8f 64 93 a9 02 00 20 7a ba a0 20 00 20 dc`
- europe-retail: `4a 4a 18 65 00 85 00 68 29 0f 18 65 00 85 00 60 c2 39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20 60 bb 85 8f 64 93 a9 02 00 20 6b ba a0 20 00 20 cd ba a0 a0 00 20 cd ba a0 20 01 20 cd ba a9 10`
- legacy-beta: `e8 d0 01 1a 60 20 db b8 6b 48 29 f0 4a 85 00 4a 4a 18 65 00 85 00 68 29 0f 18 65 00 85 00 60 c2 39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20 6f bb 85 8f 64 93 a9 02 00 20 7a ba a0 20 00 20 dc`
- pal-prototype: `39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20 4f bb 85 8f 64 93 a9 02 00 20 5a ba a0 20 00 20 bc ba a0 a0 00 20 bc ba a0 20 01 20 bc ba a9 10 00 20 5a ba 85 8b 4c 85 b9 a0 a0 00 20 06 ba 85 9d`

### ROM offset `0x00B8F1`

- usa-retail: `4a 4a 18 65 00 85 00 68 29 0f 18 65 00 85 00 60 c2 39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20 6f bb 85 8f 64 93 a9 02 00 20 7a ba a0 20 00 20 dc ba a0 a0 00 20 dc ba a0 20 01 20 dc ba a9 10`
- europe-retail: `60 c2 39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20 60 bb 85 8f 64 93 a9 02 00 20 6b ba a0 20 00 20 cd ba a0 a0 00 20 cd ba a0 20 01 20 cd ba a9 10 00 20 6b ba 85 8b 4c 96 b9 a0 a0 00 20 17 ba`
- legacy-beta: `4a 4a 18 65 00 85 00 68 29 0f 18 65 00 85 00 60 c2 39 a3 06 85 86 a3 08 85 84 a3 0a 85 82 a3 04 8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20 6f bb 85 8f 64 93 a9 02 00 20 7a ba a0 20 00 20 dc ba a0 a0 00 20 dc ba a0 20 01 20 dc ba a9 10`
- pal-prototype: `8b eb 48 ab ab a9 00 02 85 88 a9 00 00 85 8a a5 82 69 11 00 90 05 09 00 80 e6 84 85 82 a7 82 29 ff 00 85 8d e6 82 d0 07 a9 00 80 85 82 e6 84 20 4f bb 85 8f 64 93 a9 02 00 20 5a ba a0 20 00 20 bc ba a0 a0 00 20 bc ba a0 20 01 20 bc ba a9 10 00 20 5a ba 85 8b 4c 85 b9 a0 a0 00 20 06 ba 85 9d a5 86 18 e5 9d 85 9f a0 20 01 20 06 ba 1a 1a`

