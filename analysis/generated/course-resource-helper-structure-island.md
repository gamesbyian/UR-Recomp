# Course/resource helper structural island

USA `82:B293..B32E` is the compact helper cluster reached from the recovered course materialization loader: a stream-byte reader, descriptor decoder/wrapper, and a resource transfer path that either writes directly through the SNES WRAM port or dispatches compressed resources to the map decompressor at `81:B8F1`. The next span at `82:B32F` is table/data in the preserved listing.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| stream_byte_reader | 22 | 82:B280..82:B295 (-19; sim 1.000; op 15; other 0) | 82:B296..82:B2AB (+3; sim 1.000; op 15; other 0) | 82:B293..82:B2A8 (+0; sim 1.000; op 15; other 0) |
| descriptor_wrapper_and_decoder | 49 | 82:B296..82:B2C6 (-19; sim 0.980; op 30; other 0) | 82:B2AC..82:B2DC (+3; sim 0.980; op 30; other 0) | 82:B2A9..82:B2D9 (+0; sim 1.000; op 30; other 0) |
| resource_transfer_or_decompress | 85 | 82:B2C7..82:B31B (-19; sim 0.965; op 46; other 0) | 82:B2DD..82:B331 (+3; sim 0.965; op 46; other 0) | 82:B2DA..82:B32E (+0; sim 1.000; op 46; other 0) |

## Accepted caller edges

- 82:E18C JSL → 82:B2DA from course-materialization
- 82:E1F5 JSL → 82:B2A9 from course-materialization

## Transfer/decompression split

- The normal path programs WRAM address registers `$2181..$2183` and streams bytes through `$2180`.
- When descriptor flag `$4D == $80`, the helper calls `81:B8F1`, the preserved map/resource decompressor, instead of taking the direct WRAM-stream path.
