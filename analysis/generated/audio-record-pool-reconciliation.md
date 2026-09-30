# Audio record-pool and unused-song reconciliation

The CPU audio path uses one contiguous length-prefixed record pool beginning at `10:8000`.
Two different ID domains had previously been easy to conflate:

- the six 64-byte package tables contain only IDs `0x00..0x31`;
- direct calls to `APU_UploadBlockById_Wrapper` use later IDs through at least `0x42`.

The extended correlation corpus parses records `0x32..0x42` from the same contiguous pool.
This means the `0x00..0x31` range is the **package-table block universe**, not a hard
upper bound on what `02:812A APU_ResolveBlockPointer` can resolve.

## Extended records

| ID | ROM CPU address | Payload bytes | Preserved SPC byte match | Direct setup call |
|---:|---|---:|---|---|
| `0x32` | `13:C6B0` | 4443 | none | yes |
| `0x33` | `13:D80D` | 4443 | none | yes |
| `0x34` | `13:E96A` | 302 | none | yes |
| `0x35` | `13:EA9A` | 625 | none | yes |
| `0x36` | `13:ED0D` | 1587 | none | yes |
| `0x37` | `13:F342` | 968 | none | yes |
| `0x38` | `13:F70C` | 2903 | Demo Race | yes |
| `0x39` | `14:8265` | 2204 | Title Screen | yes |
| `0x3A` | `14:8B03` | 1596 | Celebration | yes |
| `0x3B` | `14:9141` | 536 | Unused Song 1 | **no** |
| `0x3C` | `14:935B` | 536 | none in preserved SPC set | yes |
| `0x3D` | `14:9575` | 2536 | Unused Song 2 | **no** |
| `0x3E` | `14:9F5F` | 2461 | 1st Race | yes |
| `0x3F` | `14:A8FE` | 1857 | 2nd Race | yes |
| `0x40` | `14:B041` | 1985 | 5th Race | yes |
| `0x41` | `14:B804` | 2627 | 3rd Race | yes |
| `0x42` | `14:C249` | 1653 | 4th Race | yes |

For every identified song record, the trimmed ROM payload appears at APU `0x1D00`.
The two unused-song records are therefore ordinary members of the same serialized song
record family, distinguished by reachability rather than by a separate storage format.

A canonical-ROM framing probe (workflow run `36771852989`, artifact
`11124252015`, digest
`sha256:fec704011913ea724bacdc7c365f0b303ede62d5f9b2599c48f4bd4211aec49d`)
closes the four-byte-trim question mechanically. Every record `0x38..0x42` begins
with the same four bytes `00 04 00 1D`, i.e. little-endian words `0x0400` and
`0x1D00`. The second word exactly matches the APU address where the post-header bytes
appear in the preserved SPCs. Records `0x3B` and `0x3D` therefore use the same
ordinary song framing as all reachable songs in this range. The exact semantic role of
the first word `0x0400` remains to be named from code, but it is not unique to the
unused songs.

## Package table 03:FB95

The known six-table package family contains exactly one table with no direct
`JSL $82:82A5` caller: `03:FB95`.

It is a strict slot-preserving subset of `03:FAD5`, the package paired with selector
`0x3A` / Celebration. Only three slots differ:

- slot 29: `0x15 -> 0xFF`
- slot 33: `0x29 -> 0xFF`
- slot 49: `0x07 -> 0xFF`

This looks intentional rather than random corruption or padding. `03:FB95` remains important as the sole orphan package table, but it is no longer the preferred Unused Song 1 pairing on current evidence. Of the three base blocks already correlated against SPC RAM (`0x07`, `0x15`, `0x29`), Unused Song 1 contains `0x15` and `0x29` but not `0x07`. Called Demo package `03:FB15` has exactly that three-marker membership pattern, while `03:FB95` omits all three. Retained APU RAM prevents this marker match from being causal proof, so both `03:FB15` reuse and `03:FB95` orphan use remain reconstruction targets.

There is no second orphan package table for `0x3D` / Unused Song 2. Instead, the live first-race `03:FB55` package reconstructs APU RAM `$B0E0-$BDE0`, and that complete 3,329-byte region is byte-identical at the same offsets in the preserved Unused Song 2 SPC. This makes `03:FB55` the leading reused-package candidate for `0x3D` and shows that a unique package per song is not required.

## Next experiment

Reconstruct the ordinary two-stage CPU path for selector `0x3B` plus package
`03:FB95` in a reference harness and compare resulting APU RAM against the preserved
Unused Song 1 SPC. Then test `0x3D` against plausible **reused** package tables.

This is a narrow counterfactual reconstruction experiment. It should not become a new
production audio path unless the resulting APU state matches the preserved evidence.
