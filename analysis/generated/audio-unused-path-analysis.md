# Unused-song audio path analysis

This reconciles extended ROM audio blocks, CPU setup calls, package tables,
preserved SPC snapshots, and the live first-race APU transfer.

| Extended selector | SPC byte match | Setup call exists | Known package pair |
|---|---|---|---|
| `0x38` | Demo Race | true | true |
| `0x39` | Title Screen | true | true |
| `0x3A` | Celebration | true | true |
| `0x3B` | Unused Song 1 | false | false |
| `0x3C` | none | true | true |
| `0x3D` | Unused Song 2 | false | false |
| `0x3E` | 1st Race | true | true |
| `0x3F` | 2nd Race | true | true |
| `0x40` | 5th Race | true | true |
| `0x41` | 3rd Race | true | true |
| `0x42` | 4th Race | true | true |

## Closed reachability facts

`0x3B` and `0x3D` are the only gaps in the otherwise populated `0x38..0x42`
song-selector range. They respectively byte-match **Unused Song 1** and **Unused Song 2**
at APU `0x1D00`, yet neither has an ordinary `JSL $82:807E` setup call.

The known package family contains six 64-byte tables. Five have direct callers.
`03:FB95` is the sole orphan. It is a strict, slot-preserving subset of called
Celebration table `03:FAD5`, replacing base blocks 0x07, 0x15, 0x29 with `FF`.

## Reachable song/package architecture

The known direct setup/package pairs already disprove any one-song/one-package model:

| Selector | Preserved SPC identity | Package table |
|---|---|---|
| `0x38` | Demo Race | `03:FB15` |
| `0x39` | Title Screen | `03:FBD5` |
| `0x3A` | Celebration | `03:FAD5` |
| `0x3B` | Unused Song 1 | none |
| `0x3C` | unidentified in preserved SPC set | `03:FC15` |
| `0x3D` | Unused Song 2 | none |
| `0x3E` | 1st Race | `03:FB55` |
| `0x3F` | 2nd Race | `03:FB55` |
| `0x40` | 5th Race | `03:FB55` |
| `0x41` | 3rd Race | `03:FB55` |
| `0x42` | 4th Race | `03:FB55` |

Most importantly, selectors `0x3E..0x42`, which map to all five numbered race songs,
share the single package table `03:FB55`. Package reuse is therefore an established
retail design pattern, not a special assumption introduced for the unused songs.

## Package reuse is a live hypothesis, not a fallback

The legacy detailed correlation file covers **3** package blocks,
but the promoted full-corpus signature artifact covers all `0x00..0x31`. Block `0x00`
is only 22 bytes, below the 32-byte minimum match length; it is the sole mechanically
untestable package block.

After excluding only that untestable block, the full signatures reproduce every known
reachable package mapping exactly: Title=`03:FBD5`, Demo=`03:FB15`,
Celebration=`03:FAD5`, and all five numbered races=`03:FB55`.

The same calculation gives **Unused Song 1 = `03:FB15`** and
**Unused Song 2 = `03:FB55`**. In other words, the unused SPCs carry the exact same
correlatable package-block signatures as Demo Race and the numbered-race family,
respectively. Independent live transfer evidence further corroborates FB55 for Unused
Song 2.

SPC RAM can retain prior data, so controlled reconstruction remains useful for causal
confirmation, but the package attribution is now strongly evidence-backed rather than a
three-marker ranking.

## Counterfactual result: 0x3D + 03:FB55 is not sufficient

Run `37067407565` tested the smallest direct reconstruction implied by the package
correlation: change only the reachable `0x3E` selector byte to `0x3D` while keeping
its existing `03:FB55` package setup intact.

The patched ROM changed exactly one byte and reached the first-race audio transfer
successfully. The observed APU-port transcript contained four counter-contiguous
data segments of 767, 41, 2,120 and 416 bytes. The final two total 2,536 bytes,
exactly the framed length of the preserved Unused Song 2 record, but they are not
that record: 2,525 of 2,536 bytes differ, with neither a common prefix nor suffix.

Durable evidence:
`analysis/generated/audio-unused-song2-fb55-counterfactual-negative-2026-10-02.json`.

This rules out the **one-byte selector substitution** as a sufficient reconstruction.
It does not invalidate the strong `03:FB55` package-signature correlation; instead it
shows that additional dormant setup state, sequencing, preloaded APU state or another
control parameter is required.

## Next discriminator

Do not repeat `0x3D + 03:FB55` unchanged. Prefer either:

1. identify the setup/control-state difference between the preserved Unused Song 2
   snapshot and the reachable `0x3E + 03:FB55` path; or
2. run the independent `0x3B + 03:FB15` reconstruction, retaining
   `0x3B + 03:FC15` as the near-twin-sequence control and `0x3B + 03:FB95` as the
   orphan-table control.
