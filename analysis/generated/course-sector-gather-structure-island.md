# Course-sector neighborhood gather structural island

USA 81:8A4A..8B94 is the function immediately upstream of the existing course-surface sampler. It converts the current X/Y coordinates into coarse 64-unit sector coordinates, gathers the neighboring sector entries, selects a local payload, and fills the $0260..$0272 workspace consumed by the next stage.

| Build | Range | Shift | Similarity | Opcodes | Operands | Unreached/data |
|---|---|---:|---:|---:|---:|---:|
| usa-retail | 81:8A4A..81:8B94 | +0 | 1.000 | 168 | 163 | 0 |
| pal-prototype-1994-11-29 | 81:8A2A..81:8B74 | -32 | 0.994 | 168 | 163 | 0 |
| europe-retail | 81:8A2A..81:8B74 | -32 | 0.961 | 168 | 163 | 0 |
| legacy-beta | 81:8A4A..81:8B94 | +0 | 1.000 | 168 | 163 | 0 |

Boundary: 81:8B94 is the RTS; 81:8B95 begins the already-censused surface sampler.

The label is intentionally structural. It describes the observed sector-neighborhood/dataflow role without claiming that every $7F000F/$7F800F field is semantically decoded.
