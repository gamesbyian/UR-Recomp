# Shared route and evidence spine: interoperability contract

Part of the [three-project apparatus synthesis](THREE-PROJECT-APPARATUS-SYNTHESIS-20261010.md). **Design target, not an accepted implementation or a new release gate.** Extend `tools/evidence_contract.py` and `tools/tool_interop.json`; do not build a new emulator/route runner or third management registry.

```text
CANONICAL USA ROM + VERIFIED SRAM SEED + OBSERVED P1/P2 INPUT
                               |
                     immutable route receipt
                               |
          +--------------------+---------------------+
          |                    |                     |
  original emulator(s)  Baldosa-native guest  Windows Modern host
  CPU/frame/PPU truth    state + Tier-2 costs  input + UI + storage
          |                    |                     |
          +----- independently hashed raw witnesses -+
                               |
              UR comparison and source provenance
          |                    |                     |
  gameplay QA-01/07      render QA-08        product/QA-02
  clocks, results,       source OBJ, 342,     profiles, .urrun,
  progression, stack     4K, authored HD      SRAM, 2P, recovery
          |                    |                     |
          +------ separate assertions and reviews ---+
                               |
                  release-quality ledger
                        /           \
          canonical technical     validated
          reference discoveries   footage input
```

**Baldosa** may attach USA matching-assembly descriptions, M/X variants and AOT/instruction costs. **malmazuke** may attach PAL research, static map, original effective-address and DMA causality. **UR** supplies original USA ROM/oracle evidence and the only release/product acceptance. An annotation is never allowed to edit or overrule the original witness. Cross-regional function/address candidates retain `candidate` status until separately verified.

## Minimal receipt for one real event

| Family | Must record | Why |
| --- | --- | --- |
| Target identity | Original USA ROM SHA-256/edition; original emulator core/version/patch digest; native guest/generated-program/config digest; Modern host commit/ZIP hash; toolchain | A core/build/region change invalidates a prior comparison |
| **Actual consumed input** | Original route file hash; normalized per-frame P1/P2 mask digest **from runtime-observed input**; controller map, frame origin, seeded SRAM preimage and deterministic seed | A script existing in Git does not prove it was played; Tier-2 identity does not itself bind the script |
| Clock and end | Original CPU frame/cycle and native guest frame/cycle as separate domains; independent event alignment; countdown, start, source finish, settled result/progression and exit | No off-by-one frame relabeling or shortened-run parity |
| Observations | Named WRAM/stack/register checkpoints; SRAM, VRAM, CGRAM, OAM and framebuffer witnesses with hashes and byte lengths; `not_captured` where absent | No invented PPU latch, missing NMI or pixel authority |
| Domain verdicts | Separate gameplay original/native, graphics source/HD, Modern product/records, input/audio/hardware and media continuity assertions with independent reviewers | No checksum or attractive footage automatically passing product QA |
| Retention and provenance | Immutable artifact digest, generating command, source revision, ROM and fixture identity, active consumers and regeneration status | Enable safe malmazuke-style replay and evidence reuse |

### Decision interface

Produce an advisory `route_receipt` with `source_identity`, `consumed_inputs`, `clock_domains`, `raw_witnesses` and `producer_run_ids`. Each independent owner attaches an ordinary `evidence_contract.py` envelope keyed by this receipt. The release ledger alone can promote source-proven acceptance. If the receipt lacks a verified observed input stream or has incompatible build/ROM identity, **fail closed**: the report may be preserved as a diagnostic but cannot assert original/native parity. Do not require passing presentation or persistence for a research-only causal observation; conversely do not call a playable Windows user journey complete without those gates.

Start from **one existing complete USA route** and original Snes9x/Baldosa fixture. Derive normalized P1/P2 input with existing `tools/controller_input.py` / replay adapters; persist both original and candidate runtime observations with independent clock alignment. The first acceptance experiment must deliberately fail on wrong ROM, seed, input receipt, truncated endpoint, missing comparison frame and stale native binary. Only after one real full event validates the chain should the system fan out to whole-course coverage, candidate build caching, seeded fuzz or source annotation promotion.

### No new authority or duplicate work

- `docs/WORK-QUEUE.md` and `AGENTS.md`: current owners and work.
- `docs/PROJECT-PLAN.md`: product and reference goals.
- `tools/tool_interop.json`: source/consumer connections and verification status.
- `tools/evidence_contract.py`: structured assertion transport, not final gate.
- `docs/RELEASE-QUALITY-LEDGER.json`: candidate-bound gate decisions.
- `docs/SYMBOLS.md`: reviewed project canonical original symbols.
- Pinned imported source/catalog/manifests: forensic input, not permission to publish or link code.

**Real-route pilot not yet performed.** Current Baldosa Tier-2 and malmazuke PPU/DMA adapters have bounded tests, not a verified common live capture.
