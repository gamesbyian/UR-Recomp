# Widescreen host-materializer depth acceptance

Retained from native workflow run `37100420673`, artifact `widescreen-native-hook-evidence` (artifact id `11266750089`, SHA-256 `528c730955d6df09f2014a6e11775bc764e284e7e66cbe47766dcd4c6b821e44`).

Column +1 remains on the accepted +8 guest path. Every deeper column is host-owned and is materialized directly from the live `7F:000F` coarse-sector table and `7F:800F` packed-surface fine records. No future-stock data is read by the runtime provider and no additional guest `$03xx` lane is introduced.

- +16: 1 host column, 617 rows, **599/599** same-view exact
- +24: 2 host columns, 1,234 rows, **1,197/1,197** same-view exact
- +32: 3 host columns, 1,851 rows, **1,796/1,796** same-view exact
- +48: 5 host columns, 3,085 rows, **2,989/2,989** same-view exact
- +64: 7 host columns, 4,319 rows, **4,180/4,180** same-view exact

Every tested margin has zero unmatched oracle rows, zero provider misses, complete ring adjacency, deterministic cleanup and protected-state equality. Rows crossing a different future fine-Y viewport are explicitly classified as vertical-view transitions rather than forced into equality.

The +32 sweep exposed one previously hidden inactive-vertical-lane off-by-one. Stock behavior there uses the unrounded camera cell `camY >> 4`; the materializer and analyzer now preserve that rule.

The materializer is therefore validated through the repository's current +64 probe depth. This does **not** define the final 16:9 source width because pixel-aspect policy remains unresolved.
