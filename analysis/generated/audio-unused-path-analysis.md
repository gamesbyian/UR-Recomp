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

## Package reuse is a live hypothesis, not a fallback

Three base package blocks already have SPC correlations: `0x07`, `0x15`, and
`0x29`. Unused Song 1 contains `0x15` and `0x29` but not `0x07`. Among the six
tables, that three-marker pattern is matched exactly by 0x03FB15.
Notably, orphan `03:FB95` omits all three markers, so its orphan status alone is no
longer enough to make it the preferred pairing.

Unused Song 2 contains `0x15` but not `0x07` or `0x29`. The three-marker pattern is
matched exactly by 0x03FB55, 0x03FBD5. Existing runtime evidence
breaks that tie in favor of `03:FB55`: the live first-race FB55 transfer reconstructs
APU RAM `$B0E0-$BDE0`, and that complete 3,329-byte region is byte-identical at the
same offsets in Unused Song 2.

Marker presence can reflect retained APU RAM from earlier package loads, so these are
candidate rankings, not causal proof.

## Next discriminator

Controlled reconstruction should now test **four** targeted combinations rather than
assuming the orphan table wins:

1. `0x3B + 03:FB15` against Unused Song 1.
2. `0x3B + 03:FB95` against Unused Song 1.
3. `0x3D + 03:FB55` against Unused Song 2.
4. `0x3D + 03:FBD5` as the remaining three-marker tie control.

A broader all-0x00..0x31 block-to-SPC correlation would further sharpen package ranking
before any executable patch is promoted.
