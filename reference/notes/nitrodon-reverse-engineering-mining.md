# Nitrodon reverse-engineering reconciliation

Recovered 2026-09-30 from the nine-file workspace preserved under `reference/imported/reverse-engineering/nitrodon/`.

This document distinguishes direct historical annotations, static deductions checked against the listed instructions, and still-open semantics. Nitrodon's names are not treated as infallible specification, but many are independently corroborated by ROM-side writer scans and deterministic USJO experiments already in this repository.

## Highest-value reconciliations

- `7E:042F` is best modeled as **player-1 tabletop duration/progress**, not an accumulated completed-tabletop counter. Nitrodon labels it "tabletop duration"; bank 82 increments it at `02:9582`, requires a value >= 3 to emit the Tabletop message at `02:9C87-9C92`, and clears it during stunt finalization. This explains the already-observed native/reference `0→1→2→3→4→0` transient.
- `7E:11F9` and `7E:11FD` are **16-bit player-1 roll and flip counters**. The game uses quarter-turn progress words at `7E:1201` and `7E:1205`; reaching four increments the corresponding completed-stunt count. A 3/4 partial may be credited on landing.
- `7E:0F61` is **current-player half-twist count**. The landing routine divides it by two to obtain full twists, caps the result at four, and uses the result for messaging/scoring.
- `7E:11CD` is a **shared current-player boost working value**, not the stable player-1 slot. Nitrodon's map gives `7E:11CF` and `7E:11D1` as player-1/player-2 boost meters. Bank 82 treats `11CD` as a word, zeroes it on wipeout, subtracts 16 in an off-screen penalty path, and clamps one boost-update path to `0x0180`.
- `7E:0F9F/0FA1` are the shared **current-player X/Y velocity working pair**. Bank 81 applies a matrix transform to the pair and writes the results back; bank 82 uses them throughout movement, boost and gravity handling.
- `7E:0545` is more specifically a player-1 **time-in-air** slot. Nitrodon records a maximum of nine frames; the game reads it as a word while historical Lua reads its low byte.

## Stunt finalization pipeline

The focused disassembly `stunts.txt` corresponds to the bank-82 routine beginning at `02:9A42`. The code selects the current player through `7E:0FEF`; tracks quarter-turn progress for roll/flip and complete counts; converts half-twists into full twists; evaluates Z-flips and tabletop duration; emits Wipeout, Head Bounce, Tabletop and stunt-count messages through `01:C5AF`; builds a stunt-combination index; consults a 625-byte table beginning at `02:9DAA`; emits praise/feedback when the table permits it; then clears transient stunt state.

## Exact stunt-combination encoding

The three word tables immediately before the 625-byte matrix are `0,125,250,375,500`, `0,25,50,75,100`, and `0,5,10,15,20`. Z-flips are added directly. Therefore the game constructs:

`index = 125*flips + 25*rolls + 5*twists + zflips`

Each dimension is capped to 0..4, so this is a base-5 encoding of four stunt dimensions covering exactly 625 combinations. The table at `02:9DAA..A01A` is therefore an exact four-dimensional stunt-combination response matrix. Values `FE` and `FF` act as special sentinels in the observed selection path; their exact distinction remains unresolved.

## Movement and boost landmarks

- `02:A968` is a clear current-player vertical-acceleration routine. It caps downward velocity below `0x0200`; upward motion receives +19 per update, while downward acceleration is `19 - floor(Yvel/32)`, then added to Y velocity.
- The path beginning around `02:A6F1` handles speed/boost constraints. When off-screen, horizontal speed is pulled toward zero and boost can be reduced by 16. Another path clamps boost to `0x0180` before deriving a speed bound.
- `02:A89D` is another boost-decrement store whose amount is table-driven from bank 80. Its enabling mask/state still needs semantic naming.
- `02:AA6E` decodes raw controller bits into normalized per-button/per-direction fields.

## Race, camera and course leads

Nitrodon's RAM map adds several high-leverage fields: `7E:1199/119B` next checkpoint; `7E:119D/119F` finish-line gate with zero reported as "can cross finish line"; `7E:0EF1/0EF3` laps remaining; `7E:12AF` current stunt-track score; `7E:0419/041B` and `041D/041F` camera positions; `7E:04F5` player-1 camera X velocity; `7E:0B68/0B6A` per-player track angle; `7E:0CBB..0D0D` paired cyclic message queues; `7E:1501..150E` per-player screen positions; and `7F:000F+` probable active track-sector data consistent with bank-81 sector lookup code.

`ROM addresses.txt` records historical map-data landmarks at ROM offsets `188000` (Dragster), `188183` (Zoom Zoo), `1894BA` (Bowl), `18A07E` (Switcher), and `1A9678` (Jumps). These should be reconciled against the already-decoded RNC/course model rather than assumed to be raw course starts.

## Bounce/collision trace

`bounce tracelog.txt` is a period execution trace through bank-81 collision/transform machinery. It repeatedly exercises coefficient loads around `01:9E51-9F14` and the velocity transform around `01:9546-961B`. Its strongest immediate value is as a historical trace fixture for future collision/bounce reconstruction; the loaded tables/pointers still need interpretation before semantic naming.

## Promotion policy

Promoted now because source plus ROM/static/dynamic evidence agree: tabletop duration/progress interpretation; 16-bit roll/flip/Z-flip/tabletop slot widths; current-player velocity/boost distinction; current-player selector; roll/flip quarter-progress fields; and stunt-finalizer, vertical-acceleration and input-decoder landmarks.

Retained as leads: exact meaning of `7E:123F`, `0F69`, `0F4F`, and several collision fields; exact meaning of `FE` vs `FF` in the 625-byte stunt table; precise boost units; exact relationship between historical map offsets and RNC payloads; and the bounce trace's coefficient/table identities.
