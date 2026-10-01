# Object/collision structural island: 81:82E2..84D1

This report recovers code/data structure across all four preserved builds.

## Recovered structure

The USA/beta island contains:

- long-entry wrapper `81:82E2..82E5`;
- dispatcher head `81:82E6..831F`;
- a 30-byte / 15-word **proven handler-pointer prefix** at `81:8320..833D`;
- dispatcher tail `81:833E..8340`;
- handler `81:8341..8371`;
- an exact 50-byte / 25-signed-word lookup table `81:8372..83A3`;
- next handler `81:83A4..84D1`.

The PAL prototype preserves the same sequence at shifted addresses.

## Embedded handler-pointer prefix

USA explicit pointer words:

`0000 8745 8785 8515 857D 87EB 8970 89B9 8A17 84D2 8050 84D2 84DB 83A4 8341`

PAL prototype:

`0000 8725 8765 84F5 855D 87CB 8950 8999 89F7 84B5 8050 84B5 84BB 8387 8324`

Europe retail:

`0000 871C 875C 84EC 8554 87C2 8950 8999 89F7 84AC 8050 84AC 84B2 837E 8316`

The indirect call is `JSR ($8320,X)` in USA. Because the dispatcher only proves `X < 0x003C`, these 15 words are a **proven pointer prefix**, not yet a proven complete indirect domain.

The pointer correspondence is nevertheless structurally powerful: the last entry targets the handler discussed below in every build.

## Europe-retail-only executable handler prologue

USA/beta target the relevant handler at `81:8341`; the PAL prototype targets `81:8324`; Europe retail targets **`81:8316`**.

Europe bytes at `81:8316..831A` are:

`C2 30 AD 2F 0F`

which decode as:

- `REP #$30`
- `LDA $0F2F`

The otherwise homologous body begins at `81:831B`, corresponding to USA `81:8341` and prototype `81:8324`.

Thus Europe retail did not insert padding between structural objects. It added a five-byte executable prologue to this handler after the surviving 1994-11-29 PAL prototype. The loaded value is immediately superseded by the homologous body, so the prologue appears semantically inert under ordinary WRAM-read behavior, but preserve that as an interpretation rather than deleting it from the structural model.

## Exact 25-word lookup table

USA `81:8372..83A3` is exactly 50 bytes / 25 signed words:

`0 2 5 5 7 7 5 5 3 -3 -5 -5 -7 -7 -5 -5 -2 2 5 5 7 7 5 5 3`

The table is byte-identical in all four builds. The next executable entry begins at USA `81:83A4` (prototype `8387`, Europe `837E`). This corrects the misleading linear decode that begins one byte early at `83A3`.

## Why this matters

This is the second independent subsystem where the four-ROM method recovers structure that a single linear disassembly obscures: embedded pointer data, exact lookup data, corrected code/data boundaries, and a prototype→retail executable addition.
