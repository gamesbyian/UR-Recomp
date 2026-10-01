# Frontend/text command dispatcher at 80:C3C8

This note resolves the valid indirect-target set behind one of SNESRecomp's three unresolved guest dispatch sites.

## Dispatch mechanics

`80:C3AB` is a byte-stream interpreter. At `80:C3AF` it reads one byte from the stream. Bytes below `0xEE` follow the ordinary character/tile path. Bytes at or above the control threshold are transformed as:

```
index = ((command ^ 0xFF) & 0xFF) * 2
target = word[80:C3CB + index]
JMP target
```

For the valid command domain `0xFF..0xEF`, the table contains 17 ordinary bank-80 ROM targets. The project-owned decoder `tools/analyze_frontend_text_dispatch.py` reproduces the table directly from the canonical ROM.

| Command | Target | Mechanically established role |
|---|---|---|
| `FF` | `80:C440` | terminate/return from the current interpreted stream |
| `FE` | `80:C481` | set layout cursor `$9F = row*32 + column` from two immediate bytes |
| `FD` | `80:C445` | dereference a 16-bit value pointer, convert it through `83:8BE7`, then interpret generated text from DP `$0002` |
| `FC` | `80:C4A7` | compute a centered horizontal position from following text, stopping at `FF/FB`; `EF` consumes an extra parameter while scanning |
| `FB` | `80:C3AF` | consume command and continue interpretation without additional work |
| `FA` | `80:C534` | read a 16-bit stream pointer and recursively interpret that nested stream |
| `F9` | `80:C546` | load a one-byte tile/attribute selector into DP `$B0` after shifting it into high tile-attribute bits |
| `F8` | `80:C5C2` | indirect argument form of formatter/copy family A; dereference a word, call `80:9B2F`, then interpret the generated buffer at `$00DC` |
| `F7` | `80:C617` | indirect argument form of formatter/copy family B; dereference a word, call `80:9B55`, then interpret `$00DC` |
| `F6` | `80:C66C` | indirect argument form of formatter/copy family C; dereference a word, call `80:9B79`, then interpret `$00DC` |
| `F5` | `80:C5BA` | immediate/direct argument form of formatter/copy family A via `80:9B2F` |
| `F4` | `80:C60F` | immediate/direct argument form of formatter/copy family B via `80:9B55` |
| `F3` | `80:C664` | immediate/direct argument form of formatter/copy family C via `80:9B79` |
| `F2` | `80:C4EF` | alternate centered-position scan, stopping at `FF/FB/5F` |
| `F1` | `80:C6AA` | dereference a word, format it through `83:8C7B`, then interpret the generated buffer at `$00FF` |
| `F0` | `80:C463` | same numeric conversion path as `FD`, but interpret from DP `$0005` rather than `$0002` |
| `EF` | `80:C6C4` | store a compact layout/cursor coordinate derived from `$9F` into one of eight records under `$0A00` |

The formatter families are deliberately named by mechanics rather than guessed user-facing meaning. `80:9B2F`, `80:9B55`, and `80:9B79` all select/copy formatted text-like data into the shared `$00DC` buffer through `00:0199`, but their exact UI nouns are not yet needed by the product plan.

## The `EE` boundary

`EE` passes the parser's `CMP #$EE` threshold, but indexing one slot beyond the valid table reads word `0x20E2` from executable bytes immediately following the table. That is not a valid bank-80 ROM handler target.

Surrounding formatter paths explicitly test for `EE` and consume it before recursively re-entering `80:C3AB`. The current best interpretation is therefore:

- `FF..EF` are the valid direct dispatch commands;
- `EE` is an escape/sentinel whose exclusion from the dispatch path depends on caller/parser invariants;
- SNESRecomp's unresolved indirect classification is understandable because its static analysis lacks that semantic range proof.

This is a bounded analyzer gap, not an unknown target explosion.

## Why this matters

Historical replay trace `36795810324` dynamically executes `80:C3C8` during frontend construction, so this is not dead code. The recovered table closes the target-enumeration problem for the valid command domain and turns the remaining work into ordinary semantic labeling rather than control-flow discovery.

The next useful evidence is only whatever handler semantics are needed by frontend modernization or by a concrete fidelity discrepancy. There is no value in exhaustively naming every string-formatting variant merely for completeness.
