# Course resource descriptor / WRAM-port copy structural island

USA `82:B293..B32E` is the compact helper cluster called by the recovered course loader. It parses five-byte resource descriptors through DP pointer `$4F`, exposes descriptor length/source metadata through `$4B/$4D`, and copies the selected stream through the SNES WRAM data port `$2180`.

| Region | Size | USA | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|---|
| stream_byte_reader | 22 | 82:B293..82:B2A8 (+0; sim 1.000; op 15; other 0) | 82:B280..82:B295 (-19; sim 1.000; op 15; other 0) | 82:B296..82:B2AB (+3; sim 1.000; op 15; other 0) | 82:B293..82:B2A8 (+0; sim 1.000; op 15; other 0) |
| descriptor_long_entry | 4 | 82:B2A9..82:B2AC (+0; sim 1.000; op 2; other 0) | 82:B296..82:B299 (-19; sim 0.750; op 2; other 0) | 82:B2AC..82:B2AF (+3; sim 0.750; op 2; other 0) | 82:B2A9..82:B2AC (+0; sim 1.000; op 2; other 0) |
| descriptor_decode | 45 | 82:B2AD..82:B2D9 (+0; sim 1.000; op 28; other 0) | 82:B29A..82:B2C6 (-19; sim 1.000; op 28; other 0) | 82:B2B0..82:B2DC (+3; sim 1.000; op 28; other 0) | 82:B2AD..82:B2D9 (+0; sim 1.000; op 28; other 0) |
| wram_port_copy | 85 | 82:B2DA..82:B32E (+0; sim 1.000; op 46; other 0) | 82:B2C7..82:B31B (-19; sim 0.965; op 46; other 0) | 82:B2DD..82:B331 (+3; sim 0.965; op 46; other 0) | 82:B2DA..82:B32E (+0; sim 1.000; op 46; other 0) |

## Structural interpretation

- `82:B2A9` is a long-entry wrapper over the shared descriptor decoder at `82:B2AD`.
- The decoder indexes a five-byte descriptor record, returns one byte in A, a word through Y, stores a word in DP `$4B`, and preserves the descriptor high-bit flag in DP `$4D`.
- `82:B2DA` saves the caller's WRAM destination, reuses the same descriptor decoder, programs `$2181..$2183`, and emits `$4B` bytes through `$2180` using the stream reader at `82:B293`.
- The selector is exact: `82:B2F6 CMP #$80; BEQ $B320` tests DP `$4D`, so `$4D == $80` diverts to `81:B8F1`, the preserved map/resource decompressor. Other descriptor values continue through the direct WRAM-port path.
- `82:B32F` is intentionally excluded: the preserved disassembly immediately changes character into table/data-like bytes.

This is a bounded structural result. The names describe observed dataflow and hardware effects, not a claim that every descriptor field's game-level meaning is known.
