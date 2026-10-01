# Retrospective semantic propagation pass — 2026-09-30

This pass applies the project's semantic-propagation rule to two already-known high-value anchors: `Race_UpdateRacersFrame` at `82:89B9` and `Course_LoadAndMaterialize` / the recovered course-address evidence.

## 1. Racer-frame update fan-out

Nitrodon's recovered bank-82 listing shows `82:89B9..9384` as an explicit marshal → shared-workspace simulation → writeback pipeline.

### Confirmed current-player workspace structure

For player 1, the routine copies persistent state into the shared `$0Fxx` workspace, runs the common simulation helpers, then copies results back. When player 2 is active it repeats the same pattern with paired player-2 storage.

High-value exact correspondences:

| Shared/current-player field | Player 1 persistent | Player 2 persistent | Evidence |
|---|---:|---:|---|
| position X | `0411` via DP `A5` | `0413` via DP `A5` | copy-in at `8A9E/8FA6`, writeback at `8DA4/9292` |
| position Y | `0415` via DP `A7` | `0417` via DP `A7` | `8A99/8FA1`, `8D9F/928D` |
| X velocity | `04B7` → `0F9F` | `04B9` → `0F9F` | `8B84/908C`, `8E84/9372` |
| Y velocity | `04BB` → `0FA1` | `04BD` → `0FA1` | `8B8A/9092`, `8E8A/9378` |
| pitch | `04C7` → `0F49` | `04C9` → `0F49` | `8A7B/8F83`, `8D81/926F` |
| faced direction | `0BA1` → `0F47` | `0BA3` → `0F47` | `8A75/8F7D`, `8D7B/9269` |
| track angle | `0B68` → `0F0D` | `0B6A` → `0F0D` | `89C7/8ECF` |
| air time | `0545` → `0F29` | `0547` → `0F29` | `8A1B/8F23` |
| Z rotation state | `0DFD` → `0F57` | `0DFF` → `0F57` | `8AAF/8FB7`, `8DAF/929D` |
| boost meter | `11CF` → `11CD` | `11D1` → `11CD` | `8BA2/8EB1`, writeback `8CF1/91D9` |

The current-player selector is set explicitly to `0` for P1 at `82:8C22-8C24` and `2` for P2 at `82:910C-910E`, proving the established `0FEF` selector semantics.

### Consequences

1. The recovered P2 position/speed fields are no longer just historical-label + adjacency inferences. They participate in the exact same simulation workspace as the already dynamically verified P1 fields.
2. The boost model is closed at the storage-boundary level: `11CD` is unambiguously the shared working value and `11CF/11D1` are the persistent P1/P2 meters.
3. `0547` is the paired P2 air-time field because it is copied into the same `0F29` workspace consumed by the stunt pipeline that uses P1 `0545`.
4. `0B68/0B6A` are paired per-player track-angle fields at the simulation boundary.
5. The old historical label conflict around `0F63` is narrowed decisively. The routine loads P1 `7E:211E` into `0F63` and P2 `7E:2120` into the same `0F63` workspace slot. Therefore `0F63` is shared current-player workspace, not stable player-specific storage. Its physical meaning remains open.
6. Several other `$0Fxx` values can now be attacked by paired-storage inference instead of isolated writer hunting. This should be used selectively when one of those fields blocks collision, stunt, camera, widescreen, or fidelity work.

## 2. Course-address fan-out

Nitrodon's recovered `ROM addresses.txt` lists:

- `188000`: Dragster
- `188183`: Zoom Zoo
- `1894BA`: Bowl
- `18A07E`: Switcher
- `1A9678`: Jumps

Interpreting these as SNES LoROM CPU addresses gives file offsets:

- `18:8000` → `0x0C0000`
- `18:8183` → `0x0C0183`
- `18:A07E` → `0x0C207E`
- `1A:9678` → `0x0D1678`

Those are exact RNC stream starts in the canonical manifest:

- stream 1 `0x0C0000`
- stream 2 `0x0C0183`
- stream 4 `0x0C207E`
- stream 13 `0x0D1678`

The Bowl entry `18:94BA` maps to `0x0C14BA`, which lies inside stream 2 and is not an RNC header. However stream 3 begins at file offset `0x0C1B4A`, whose LoROM CPU address is `18:9B4A`. The historical text is therefore strongly consistent with a simple transposition typo, `1894BA` → `189B4A`.

### Consequences

This independently confirms five stream/course identities from recovered historical reverse-engineering material:

| Stream | RNC file offset | LoROM CPU address | Course |
|---:|---:|---:|---|
| 1 | `0x0C0000` | `18:8000` | Dragster |
| 2 | `0x0C0183` | `18:8183` | Zoom Zoo |
| 3 | `0x0C1B4A` | `18:9B4A` | Bowl, with one-character-order typo in recovered note |
| 4 | `0x0C207E` | `18:A07E` | Switcher |
| 13 | `0x0D1678` | `1A:9678` | Jumps |

This is stronger than the previous provisional order-only mapping because it comes from an independent historical address map and lands on exact packed RNC boundaries.

### Follow-up value

- Promote these five course identities to confirmed for the USA build.
- Use them as anchors when validating the remaining stream-order/name mapping.
- Treat historical ROM addresses elsewhere as potential SNES CPU addresses first, converting through LoROM mapping before assuming they are file offsets.
- Do not spend effort proving the Bowl typo beyond the exact boundary match unless contradictory evidence appears.

## Stop rule

The two passes already produced concrete reusable knowledge. Further recursive expansion is deferred until a live fidelity/course/rendering question points at one of the newly exposed paired fields or stream identities.
