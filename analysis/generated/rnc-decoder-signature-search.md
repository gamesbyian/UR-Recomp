# RNC1 Decoder Signature Search

Mechanical search for opcode shapes derived from the preserved period `SOURCE/SUPERNES/RNC_1.S`. A hit is a candidate until surrounding code/control flow is checked.

## usa-retail

- entry-loose: `0x00B8F1` (LoROM 01:B8F1)
- entry-dp-sta: `0x00B8F1` (LoROM 01:B8F1)
- makehuff-shape: `0x00BADC` (LoROM 01:BADC), `0x00BE01` (LoROM 01:BE01)

## europe-retail

- entry-loose: `0x00B8E2` (LoROM 01:B8E2)
- entry-dp-sta: `0x00B8E2` (LoROM 01:B8E2)
- makehuff-shape: `0x00BACD` (LoROM 01:BACD), `0x00BDF2` (LoROM 01:BDF2)

## legacy-beta

- entry-loose: `0x00B8F1` (LoROM 01:B8F1)
- entry-dp-sta: `0x00B8F1` (LoROM 01:B8F1)
- makehuff-shape: `0x00BADC` (LoROM 01:BADC), `0x00BE01` (LoROM 01:BE01)

## pal-prototype

- entry-loose: `0x00B8D1` (LoROM 01:B8D1)
- entry-dp-sta: `0x00B8D1` (LoROM 01:B8D1)
- makehuff-shape: `0x00BABC` (LoROM 01:BABC), `0x00BDE1` (LoROM 01:BDE1)

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

