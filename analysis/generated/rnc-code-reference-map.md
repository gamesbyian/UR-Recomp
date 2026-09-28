# RNC Decoder Calls and Packed-Stream References

Generated mechanically from the identified RNC1 entry and the 45 validated stream starts. CPU-bank mirrors are searched explicitly. A raw pointer hit is evidence of byte-level reference only until surrounding structure is classified.

## usa-retail

Identified unpacker entry: `0x00B8F1` (LoROM 01:B8F1).

### Direct JSL callers

- `0x013322` (LoROM 02:B322), encoded target bank `81`: `a5 04 29 01 8f 83 21 00 a6 4b 20 93 b2 8f 80 21 00 ca d0 f6 ab 6b c2 20 22 f1 b8 81 68 68 68 68 e2 20 c2 10 6b 04 00 80 e0 00 04 e0 80 20 00 04 00 81 20 00`

### Packed-stream pointer references

| Stream | Stream offset | 24-bit pointer hits | 16-bit address-word hits in likely pointer region |
|---:|---:|---|---|
| 1 | `0x0C0000` | `0x001D34` (LoROM 00:9D34)→18:8000, `0x1DBD32` (LoROM 3B:BD32)→18:8000, `0x1EB893` (LoROM 3D:B893)→18:8000, `0x1EDDF7` (LoROM 3D:DDF7)→18:8000, `0x1F5443` (LoROM 3E:D443)→18:8000, `0x1FA30B` (LoROM 3F:A30B)→18:8000 | 1862 |
| 2 | `0x0C0183` | none | 19 |
| 3 | `0x0C1B4A` | none | 1 |
| 4 | `0x0C207E` | none | 6 |
| 5 | `0x0C46DA` | none | 4 |
| 6 | `0x0C65FA` | none | 3 |
| 7 | `0x0C7EA7` | none | 2 |
| 8 | `0x0C9748` | none | 1 |
| 9 | `0x0C9C9F` | none | 130 |
| 10 | `0x0CC1AB` | none | 2 |
| 11 | `0x0CD2D3` | none | 7 |
| 12 | `0x0D01A5` | `0x0AA4AC` (LoROM 15:A4AC)→9A:81A5 | 6 |
| 13 | `0x0D1678` | none | 1 |
| 14 | `0x0D21D2` | none | 1 |
| 15 | `0x0D3BB8` | none | 3 |
| 16 | `0x0D43C8` | none | 2 |
| 17 | `0x0D64E0` | none | 2 |
| 18 | `0x0D8326` | none | 1 |
| 19 | `0x0D8603` | none | 8 |
| 20 | `0x0D9EB0` | none | 2 |
| 21 | `0x0DBC7A` | none | 3 |
| 22 | `0x0DCD58` | none | 2 |
| 23 | `0x0DE31A` | none | 3 |
| 24 | `0x0DE6AD` | none | 2 |
| 25 | `0x0DFE8E` | none | 3 |
| 26 | `0x0E13E1` | none | 1 |
| 27 | `0x0E2E68` | none | 4 |
| 28 | `0x0E4497` | none | 5 |
| 29 | `0x0E4FB7` | none | 3 |
| 30 | `0x0E6C20` | none | 28 |
| 31 | `0x0E7A42` | none | 3 |
| 32 | `0x0E92E4` | none | 2 |
| 33 | `0x0EB0B9` | none | 5 |
| 34 | `0x0EB4B3` | none | 31 |
| 35 | `0x0ECC1E` | none | 20 |
| 36 | `0x0EDD2E` | none | 8 |
| 37 | `0x0F00CC` | none | 4 |
| 38 | `0x0F0F06` | none | 5 |
| 39 | `0x0F13B8` | none | 1 |
| 40 | `0x0F2978` | none | 6 |
| 41 | `0x0F45E1` | none | 3 |
| 42 | `0x0F7AB7` | none | 2 |
| 43 | `0x0F8B60` | none | 4 |
| 44 | `0x0F9F23` | none | 1 |
| 45 | `0x0FB9D7` | none | 4 |

## europe-retail

Identified unpacker entry: `0x00B8E2` (LoROM 01:B8E2).

### Direct JSL callers

- `0x013325` (LoROM 02:B325), encoded target bank `81`: `a5 04 29 01 8f 83 21 00 a6 4b 20 96 b2 8f 80 21 00 ca d0 f6 ab 6b c2 20 22 e2 b8 81 68 68 68 68 e2 20 c2 10 6b 04 00 80 e0 00 04 e0 80 20 00 04 00 81 20 00`

### Packed-stream pointer references

| Stream | Stream offset | 24-bit pointer hits | 16-bit address-word hits in likely pointer region |
|---:|---:|---|---|
| 1 | `0x0C0000` | `0x001D34` (LoROM 00:9D34)→18:8000, `0x1DBD32` (LoROM 3B:BD32)→18:8000, `0x1EB893` (LoROM 3D:B893)→18:8000, `0x1EDDF7` (LoROM 3D:DDF7)→18:8000, `0x1F5443` (LoROM 3E:D443)→18:8000, `0x1FA30B` (LoROM 3F:A30B)→18:8000 | 1856 |
| 2 | `0x0C0183` | none | 19 |
| 3 | `0x0C1B4A` | none | 1 |
| 4 | `0x0C207E` | none | 6 |
| 5 | `0x0C470E` | none | 1 |
| 6 | `0x0C662E` | none | 1 |
| 7 | `0x0C7EDB` | none | 1 |
| 8 | `0x0C977C` | none | 1 |
| 9 | `0x0C9CD3` | none | 2 |
| 10 | `0x0CC1DF` | none | 6 |
| 11 | `0x0CD307` | none | 2 |
| 12 | `0x0D01D9` | none | 1 |
| 13 | `0x0D16AC` | `0x0ABA0A` (LoROM 15:BA0A)→9A:96AC | 3 |
| 14 | `0x0D2206` | `0x00691F` (LoROM 00:E91F)→1A:A206, `0x006AE8` (LoROM 00:EAE8)→1A:A206 | 29 |
| 15 | `0x0D3BEC` | none | 14 |
| 16 | `0x0D43FC` | `0x0CD190` (LoROM 19:D190)→9A:C3FC | 7 |
| 17 | `0x0D6545` | none | 1 |
| 18 | `0x0D838B` | none | 53 |
| 19 | `0x0D8668` | none | 1 |
| 20 | `0x0D9F15` | none | 2 |
| 21 | `0x0DBCED` | none | 15 |
| 22 | `0x0DCDCB` | none | 25 |
| 23 | `0x0DE38D` | none | 6 |
| 24 | `0x0DE720` | `0x1A3585` (LoROM 34:B585)→9B:E720 | 6 |
| 25 | `0x0DFF01` | none | 400 |
| 26 | `0x0E1454` | none | 8 |
| 27 | `0x0E2F5E` | none | 2 |
| 28 | `0x0E45B8` | none | 1 |
| 29 | `0x0E50D8` | none | 4 |
| 30 | `0x0E6D41` | none | 17 |
| 31 | `0x0E7B63` | none | 2 |
| 32 | `0x0E9405` | none | 6 |
| 33 | `0x0EB1DA` | none | 3 |
| 34 | `0x0EB5D4` | none | 5 |
| 35 | `0x0ECD3F` | none | 17 |
| 36 | `0x0EDE54` | none | 3 |
| 37 | `0x0F0241` | none | 4 |
| 38 | `0x0F107B` | none | 1 |
| 39 | `0x0F152D` | none | 1 |
| 40 | `0x0F2AED` | none | 3 |
| 41 | `0x0F4756` | none | 1 |
| 42 | `0x0F7C2C` | none | 2 |
| 43 | `0x0F8CD5` | none | 3 |
| 44 | `0x0FA098` | none | 11 |
| 45 | `0x0FBB4C` | none | 6 |

## legacy-beta

Identified unpacker entry: `0x00B8F1` (LoROM 01:B8F1).

### Direct JSL callers

- `0x013322` (LoROM 02:B322), encoded target bank `81`: `a5 04 29 01 8f 83 21 00 a6 4b 20 93 b2 8f 80 21 00 ca d0 f6 ab 6b c2 20 22 f1 b8 81 68 68 68 68 e2 20 c2 10 6b 04 00 80 e0 00 04 e0 80 20 00 04 00 81 20 00`

### Packed-stream pointer references

| Stream | Stream offset | 24-bit pointer hits | 16-bit address-word hits in likely pointer region |
|---:|---:|---|---|
| 1 | `0x0C0000` | `0x001D34` (LoROM 00:9D34)→18:8000, `0x1DBD32` (LoROM 3B:BD32)→18:8000, `0x1EB893` (LoROM 3D:B893)→18:8000, `0x1EDDF7` (LoROM 3D:DDF7)→18:8000, `0x1F5443` (LoROM 3E:D443)→18:8000, `0x1FA30B` (LoROM 3F:A30B)→18:8000 | 1862 |
| 2 | `0x0C0183` | none | 19 |
| 3 | `0x0C1B4A` | none | 1 |
| 4 | `0x0C207E` | none | 6 |
| 5 | `0x0C46DA` | none | 4 |
| 6 | `0x0C65FA` | none | 3 |
| 7 | `0x0C7EA7` | none | 2 |
| 8 | `0x0C9748` | none | 1 |
| 9 | `0x0C9C9F` | none | 130 |
| 10 | `0x0CC1AB` | none | 2 |
| 11 | `0x0CD2D3` | none | 7 |
| 12 | `0x0D01A5` | `0x0AA4AC` (LoROM 15:A4AC)→9A:81A5 | 6 |
| 13 | `0x0D1678` | none | 1 |
| 14 | `0x0D21D2` | none | 1 |
| 15 | `0x0D3BB8` | none | 3 |
| 16 | `0x0D43C8` | none | 2 |
| 17 | `0x0D64E0` | none | 2 |
| 18 | `0x0D8326` | none | 1 |
| 19 | `0x0D8603` | none | 8 |
| 20 | `0x0D9EB0` | none | 2 |
| 21 | `0x0DBC7A` | none | 3 |
| 22 | `0x0DCD58` | none | 2 |
| 23 | `0x0DE31A` | none | 3 |
| 24 | `0x0DE6AD` | none | 2 |
| 25 | `0x0DFE8E` | none | 3 |
| 26 | `0x0E13E1` | none | 1 |
| 27 | `0x0E2E68` | none | 4 |
| 28 | `0x0E4497` | none | 5 |
| 29 | `0x0E4FB7` | none | 3 |
| 30 | `0x0E6C20` | none | 28 |
| 31 | `0x0E7A42` | none | 3 |
| 32 | `0x0E92E4` | none | 2 |
| 33 | `0x0EB0B9` | none | 5 |
| 34 | `0x0EB4B3` | none | 31 |
| 35 | `0x0ECC1E` | none | 20 |
| 36 | `0x0EDD2E` | none | 8 |
| 37 | `0x0F00CC` | none | 4 |
| 38 | `0x0F0F06` | none | 5 |
| 39 | `0x0F13B8` | none | 1 |
| 40 | `0x0F2978` | none | 6 |
| 41 | `0x0F45E1` | none | 3 |
| 42 | `0x0F7AB7` | none | 2 |
| 43 | `0x0F8B60` | none | 4 |
| 44 | `0x0F9F23` | none | 1 |
| 45 | `0x0FB9D7` | none | 4 |

## pal-prototype

Identified unpacker entry: `0x00B8D1` (LoROM 01:B8D1).

### Direct JSL callers

- `0x01330F` (LoROM 02:B30F), encoded target bank `81`: `a5 04 29 01 8f 83 21 00 a6 4b 20 80 b2 8f 80 21 00 ca d0 f6 ab 6b c2 20 22 d1 b8 81 68 68 68 68 e2 20 c2 10 6b 04 00 80 e0 00 04 e0 80 20 00 04 00 81 20 00`

### Packed-stream pointer references

| Stream | Stream offset | 24-bit pointer hits | 16-bit address-word hits in likely pointer region |
|---:|---:|---|---|
| 1 | `0x0C0000` | `0x001D2B` (LoROM 00:9D2B)→18:8000, `0x1DBD32` (LoROM 3B:BD32)→18:8000, `0x1EB893` (LoROM 3D:B893)→18:8000, `0x1EDDF7` (LoROM 3D:DDF7)→18:8000, `0x1F5443` (LoROM 3E:D443)→18:8000, `0x1FA30B` (LoROM 3F:A30B)→18:8000 | 1824 |
| 2 | `0x0C0183` | none | 19 |
| 3 | `0x0C1B4A` | none | 1 |
| 4 | `0x0C207E` | none | 6 |
| 5 | `0x0C46DA` | none | 4 |
| 6 | `0x0C65FA` | none | 3 |
| 7 | `0x0C7EA7` | none | 2 |
| 8 | `0x0C9748` | none | 1 |
| 9 | `0x0C9C9F` | none | 131 |
| 10 | `0x0CC1AB` | none | 2 |
| 11 | `0x0CD2D3` | none | 7 |
| 12 | `0x0D01A5` | `0x0AA4AC` (LoROM 15:A4AC)→9A:81A5 | 6 |
| 13 | `0x0D1678` | none | 1 |
| 14 | `0x0D21D2` | none | 1 |
| 15 | `0x0D3BB8` | none | 2 |
| 16 | `0x0D43C8` | none | 1 |
| 17 | `0x0D64E0` | none | 2 |
| 18 | `0x0D8326` | none | 1 |
| 19 | `0x0D8603` | none | 8 |
| 20 | `0x0D9EB0` | none | 2 |
| 21 | `0x0DBC7A` | none | 3 |
| 22 | `0x0DCD58` | none | 2 |
| 23 | `0x0DE31A` | none | 3 |
| 24 | `0x0DE6AD` | none | 2 |
| 25 | `0x0DFE8E` | none | 3 |
| 26 | `0x0E13E1` | none | 1 |
| 27 | `0x0E2E68` | none | 4 |
| 28 | `0x0E4497` | none | 5 |
| 29 | `0x0E4FB7` | none | 2 |
| 30 | `0x0E6C20` | none | 28 |
| 31 | `0x0E7A42` | none | 3 |
| 32 | `0x0E92E4` | none | 2 |
| 33 | `0x0EB0B9` | none | 5 |
| 34 | `0x0EB4B3` | none | 31 |
| 35 | `0x0ECC1E` | none | 20 |
| 36 | `0x0EDD2E` | none | 8 |
| 37 | `0x0F00CC` | none | 4 |
| 38 | `0x0F0F06` | none | 5 |
| 39 | `0x0F13B8` | none | 1 |
| 40 | `0x0F2978` | none | 5 |
| 41 | `0x0F45E1` | none | 4 |
| 42 | `0x0F7AB7` | none | 5 |
| 43 | `0x0F8B60` | none | 4 |
| 44 | `0x0F9F23` | none | 1 |
| 45 | `0x0FB9D7` | none | 4 |

