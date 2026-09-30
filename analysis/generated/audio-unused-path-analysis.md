# Unused-song audio path analysis

This reconciles three already-reproducible evidence surfaces: extended ROM audio blocks,
CPU setup calls, and 64-byte package-table callers.

| Extended selector | SPC byte match | Setup call exists | Known package pair |
|---|---|---|---|
| `0x38` | Demo Race | True | True |
| `0x39` | Title Screen | True | True |
| `0x3A` | Celebration | True | True |
| `0x3B` | Unused Song 1 | False | False |
| `0x3C` | none | True | True |
| `0x3D` | Unused Song 2 | False | False |
| `0x3E` | 1st Race | True | True |
| `0x3F` | 2nd Race | True | True |
| `0x40` | 5th Race | True | True |
| `0x41` | 3rd Race | True | True |
| `0x42` | 4th Race | True | True |

## Closed reachability facts

`0x3B` and `0x3D` are the only gaps in the otherwise populated `0x38..0x42`
song-selector range. They respectively byte-match **Unused Song 1** and **Unused Song 2**
at APU `0x1D00`, yet neither has an ordinary `JSL $82:807E` setup call. The scanner
also finds no hidden immediate `LDX #$003B/#$003D` setup form and no unbound setup-wrapper
calls.

The known package family contains six 64-byte tables. Five have direct callers.
`03:FB95` is the sole orphan.

## What 03:FB95 is

`03:FB95` is a strict, slot-preserving subset of called table `03:FAD5`, the table
paired with selector `0x3A` whose extended block matches **Celebration**. The tables
differ at exactly three slots: `03:FB95` replaces base blocks 0x07, 0x15, 0x29 with `FF`.

That makes `03:FB95` a strong **structural candidate** for a removed audio path, and
`0x3B / Unused Song 1` is the natural first pairing to test because both the selector
and table are orphaned. It is not yet proof that the original code paired them.

## Important negative result

There is only one orphan package table but two unreachable song selectors, so a one-orphan-table-per-song model is ruled out. More positively, the live first-race `03:FB55` transfer reconstructs APU RAM `$B0E0-$BDE0`; that complete 3,329-byte region is byte-identical at the same offsets in the preserved **Unused Song 2** SPC. `03:FB55` is therefore the leading **reused-package** candidate for `0x3D`.

## Next discriminator

The useful next experiment is a controlled reconstruction, not more pattern searching:
invoke the ordinary setup path with selector `0x3B` and package table `03:FB95` in a
reference harness, then compare resulting APU RAM to the preserved Unused Song 1 SPC.
Test `0x3D + 03:FB55` as the leading reused-package model rather than inventing a seventh table.
