# Object/collision structural island: 81:82E2..84D1

Boundaries come from direct long-entry calls, explicit RTS/RTL instructions, the indexed indirect dispatch at `81:831B`, and four-ROM structural alignment.

| Region | Kind | Size | USA | PAL prototype | Europe | Legacy beta |
|---|---|---:|---|---|---|---|
| long_entry_wrapper | code | 4 | 81:82E2..81:82E5 (+0, sim 1.000; op 2, data/unreached 0) | 81:82C5..81:82C8 (-29, sim 0.750; op 2, data/unreached 0) | 81:82B7..81:82BA (-43, sim 0.750; op 2, data/unreached 0) | 81:82E2..81:82E5 (+0, sim 1.000; op 2, data/unreached 0) |
| dispatcher_head | code | 58 | 81:82E6..81:831F (+0, sim 1.000; op 26, data/unreached 0) | 81:82C9..81:8302 (-29, sim 0.914; op 26, data/unreached 0) | 81:82BB..81:82F4 (-43, sim 0.862; op 26, data/unreached 0) | 81:82E6..81:831F (+0, sim 1.000; op 26, data/unreached 0) |
| handler_pointer_prefix | data | 30 | 81:8320..81:833D (+0, sim 1.000; op 0, data/unreached 30) | 81:8303..81:8320 (-29, sim 0.500; op 0, data/unreached 30) | 81:82F5..81:8312 (-43, sim 0.500; op 0, data/unreached 30) | 81:8320..81:833D (+0, sim 1.000; op 0, data/unreached 30) |
| dispatcher_tail | code | 3 | 81:833E..81:8340 (+0, sim 1.000; op 2, data/unreached 0) | 81:8321..81:8323 (-29, sim 1.000; op 2, data/unreached 0) | 81:8313..81:8315 (-43, sim 1.000; op 2, data/unreached 0) | 81:833E..81:8340 (+0, sim 1.000; op 2, data/unreached 0) |
| handler_8341 | code | 49 | 81:8341..81:8371 (+0, sim 1.000; op 22, data/unreached 0) | 81:8324..81:8354 (-29, sim 0.898; op 22, data/unreached 0) | 81:831B..81:834B (-38, sim 0.857; op 22, data/unreached 0) | 81:8341..81:8371 (+0, sim 1.000; op 22, data/unreached 0) |
| lookup_8372 | data | 50 | 81:8372..81:83A3 (+0, sim 1.000; op 0, data/unreached 50) | 81:8355..81:8386 (-29, sim 1.000; op 0, data/unreached 50) | 81:834C..81:837D (-38, sim 1.000; op 0, data/unreached 50) | 81:8372..81:83A3 (+0, sim 1.000; op 0, data/unreached 50) |
| handler_83A4 | code | 302 | 81:83A4..81:84D1 (+0, sim 1.000; op 119, data/unreached 0) | 81:8387..81:84B4 (-29, sim 0.871; op 119, data/unreached 0) | 81:837E..81:84AB (-38, sim 0.828; op 119, data/unreached 0) | 81:83A4..81:84D1 (+0, sim 1.000; op 119, data/unreached 0) |

## Post-dispatch gap

- usa-retail: none
- pal-prototype-1994-11-29: none
- europe-retail: 81:8316..81:831A (5 bytes): c2 30 ad 2f 0f
- legacy-beta: none

## Embedded handler table

- 30 bytes / 15 little-endian words.
- USA entries: 0000 8745 8785 8515 857D 87EB 8970 89B9 8A17 84D2 8050 84D2 84DB 83A4 8341
- PAL prototype entries: 0000 8725 8765 84F5 855D 87CB 8950 8999 89F7 84B5 8050 84B5 84BB 8387 8324
- Europe entries: 0000 871C 875C 84EC 8554 87C2 8950 8999 89F7 84AC 8050 84AC 84B2 837E 8316
- `JSR ($8320,X)` proves these words are an embedded handler-pointer prefix. Because the guard is only `X < 0x003C`, do **not** treat the 30-byte prefix as the complete indirect domain without a tighter X-value proof.

## Lookup table after handler_8341

- 50 bytes / 25 signed words.
- USA signed values: 0 2 5 5 7 7 5 5 3 -3 -5 -5 -7 -7 -5 -5 -2 2 5 5 7 7 5 5 3
- The next executable entry begins at `81:83A4`; linear disassembly beginning at `83A3` is a one-byte code/data boundary error.
