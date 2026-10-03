# +24 Widescreen host materializer acceptance

Retained from native workflow run `37097604758`, artifact `widescreen-native-hook-evidence` (artifact id `11265150778`, SHA-256 `124ec1c4dae6ed88c73508e0ac74cc492877a5a3992b05b617cf6c746e348a07`).

The accepted +8 guest path still supplies column +1. +24 retains columns +2 and +3 exclusively in host-owned presentation state and materializes both directly from the live `7F:000F` coarse-sector table and `7F:800F` packed-surface fine records. No future-stock data is read by the runtime provider and no additional guest `$03xx` lane is introduced.

- accepted +8 regression: **true**
- accepted +16 regression: **true**
- +24 guest preparation events: **617**
- +24 host-owned columns: **1,234**
- same-view independently comparable rows: **1,197**
- exact same-view payload matches: **1,197 / 1,197**
- vertical-view-transition rows: **37**
- unmatched oracle rows: **0**
- provider misses: **0**
- two host columns for every preparation: **true**
- complete adjacent ring chain: **true**
- protected state equal: **true**
- deterministic cleanup: **true**

Rows whose later-stock control samples a different effective fine-Y viewport remain explicitly classified as vertical-view transitions rather than being forced into false equality. The independent later-stock run is acceptance-only.

This removes the previous one-host-column storage cap. The architecture is validated through +24, but this result does not yet establish the final 16:9 capacity ceiling.
