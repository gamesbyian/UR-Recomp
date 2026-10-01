# Controlled SRAM medal discriminator

Generated from a clean recovered SRAM image, one deterministic stock Dragster completion, and the resulting emulator SRAM dump.

- SRAM size: 8192 bytes
- changed bytes: 11
- changed contiguous ranges: 8

## Changed ranges

| Start | End | Length |
|---:|---:|---:|
| `0x0230` | `0x0230` | 1 |
| `0x02B0` | `0x02B0` | 1 |
| `0x0422` | `0x0423` | 2 |
| `0x054E` | `0x0550` | 3 |
| `0x05E6` | `0x05E6` | 1 |
| `0x0740` | `0x0740` | 1 |
| `0x0743` | `0x0743` | 1 |
| `0x10A7` | `0x10A7` | 1 |

## Byte changes

| Offset | Before | After |
|---:|---:|---:|
| `0x0230` | `0x00` | `0x01` |
| `0x02B0` | `0x00` | `0x01` |
| `0x0422` | `0x60` | `0x28` |
| `0x0423` | `0xEA` | `0x0B` |
| `0x054E` | `0x00` | `0xC8` |
| `0x054F` | `0xDD` | `0xFD` |
| `0x0550` | `0x10` | `0x00` |
| `0x05E6` | `0xB0` | `0xA0` |
| `0x0740` | `0x00` | `0x88` |
| `0x0743` | `0x04` | `0x15` |
| `0x10A7` | `0x07` | `0x0D` |

## Comparison with recovered all-silver snapshots

- all_silvers_no_hunter: 0/11 changed offsets equal the recovered snapshot value; whole-image differences 356.
- all_silvers_with_hunter: 0/11 changed offsets equal the recovered snapshot value; whole-image differences 356.
