# USJO v8 unresolved-WRAM writer scan

Source workflow run: `36769525945`  
Artifact: `uniracers-targeted-wram-store-sites` (artifact `11121794448`)  
Artifact digest: `sha256:f43d857bbfa382a0532c2e49680512c8ad334b0f9f316b65b85ef19fa838b57d`

This is a byte-pattern candidate scan, not authoritative disassembly. Coherent candidates in the known gameplay-code region are useful static landmarks; dynamic writers or bounded disassembly must still establish semantics.

| WRAM | Candidate count | High-value bank-02 candidates |
|---|---:|---|
| `7E:042B` | 3 | `02:94AB STA $042B,X`; `02:96D0 STA $042B,Y`; `02:9D82 STA $042B,X` |
| `7E:042F` | 15 | `02:94AE STA $042F,X`; `02:9582 INC $042F,X`; `02:9D85 STA $042F,X` |
| `7E:0DFD` | 2 | `02:8DB2 STY $0DFD` |
| `7E:0F57` | 7 | `02:8AB2 STY`; `02:8FBA STY`; `02:A424/A432/A461 STA`; `02:A491 STZ $0F57` |
| `7E:0F61` | 9 | `02:8BDB/90C5 STY`; `02:949C/9D73/A3F4 STA`; `02:A46E INC $0F61` |
| `7E:11CD` | 9 | `02:8BA5 STY`; `02:8EB4/9BA6/A768/A89D STA $11CD` |
| `7E:11F9` | 5 | `02:949F/9A9D/9D76 STA $11F9,X`; `02:9B27/9BB7 INC $11F9,X` |
| `7E:11FD` | 6 | `02:94A2/9AA0/9D79 STA $11FD,X`; `02:9B41/9BF6 INC $11FD,X` |

## Boost-meter width result

The `7E:11CD` candidates contain coherent word-oriented code. Most decisively, context around `02:9BA6` is:

`C2 20 A9 00 00 8D CD 11`

That decodes as `REP #$20; LDA #$0000; STA $11CD`, explicitly storing a 16-bit zero. Other nearby sequences load, subtract a 16-bit immediate, and store back to `$11CD`. This resolves the historical width question in favor of a 16-bit game field.

USJO v8's `memory.readbyte(0x7E11CD)` is therefore best understood as an intentional low-byte sample. The script only uses `realboostmeter == 0` as a gate and does not use that byte as the boost magnitude in its candidate score.

## Next static/dynamic targets

The stunt-counter candidates cluster strongly in bank 02 and include plausible increment instructions, especially `02:A46E` for twist, `02:9582` for tabletop, `02:9B27/9BB7` for roll, and `02:9B41/9BF6` for flip. Bounded disassembly around these sites is the cheapest next step before launching new runtime traces.

## Paired working-state structure

The Z-state and twist candidates are not just isolated stores.

- `02:8AB2` contains `LDY $0DFD; STY $0F57`.
- `02:8FBA` contains the paired `LDY $0DFF; STY $0F57`.
- `02:8DB2` copies `LDY $0F57; STY $0DFD`.

That establishes `$0F57` as shared current-player working state fed from paired persistent racer slots `$0DFD/$0DFF`, rather than stable player-1-only storage.

The twist field has the same general shape: `02:8BDB` and `02:90C5` copy distinct player-specific sources into `$0F61`, while `02:A46E` conditionally increments `$0F61`. The historical/player-1 label remains operationally useful for single-player TAS work, but the storage role is better described as current-player working twist count.

## Counter semantics

Several candidate contexts are sufficiently coherent to support static counter semantics:

- Z-flip: around `02:96D0`, `LDA $042B,Y; INC A; STA $042B,Y`.
- Tabletop: `02:9582`, `INC $042F,X`.
- Twist: `02:A46E`, conditional `INC $0F61`.
- Roll: `02:9B27` and `02:9BB7`, `INC $11F9,X`.
- Flip: `02:9B41` and `02:9BF6`, `INC $11FD,X`.

These static findings corroborate the recovered USJO/TAS labels and justify stronger symbol confidence, while event-causal runtime fixtures remain useful before treating exact transition timing as closed.

