# Independent Windows candidate disposition: 2026-10-10

Scope: QA evidence handoff, **not** a release gate promotion. Read `docs/RELEASE-QUALITY-LEDGER.json` for the authoritative current QA-01..12 statuses. This receipt records the cheapest available reuse candidate and specifically distinguishes build evidence from player acceptance.

## Inspected provenance

- Inspected `main`: `82cbdfbba776563ef57b1ed30b2aaaa277616538` (2026-10-11 05:03 UTC). No exact-head hosted Windows artifact was established by this audit.
- Most recent **observed successful main Windows native smoke** in the inspected Actions history: [run 38095271085](https://github.com/gamesbyian/UR-Recomp/actions/runs/38095271085), source `1afe05edee2617c6a5b8cf67fce806fbfe939bf2`, workflow completed successfully. This is an **older source revision**, not the inspected main.
- That run produced `ur-recomp-windows-x64-portable` artifact **11685513517**, size 3,391,958 bytes, expires 2026-10-17, Actions outer-artifact digest `sha256:f487a049fe19ed1df745d8916cc21ae070b815ea7e169d5e9bc68d2c1a1f77a4`. It also produced `windows-native-smoke` artifact 11685768139. The Actions **outer ZIP transport digest is not the embedded portable release ZIP SHA-256**, and must never populate `candidate.zip_sha256`.
- Run job steps include Windows package assembly, stock-PowerShell archive verification, packaged boot and result checks, controller-only root/modal and default-Return Restart audio probes, user-data refresh/migration and diagnostics. These show bounded **hosted runner** contracts on the older source revision, not certified physical input, audio, graphics, complete 1P/2P results or fresh-process player journey on this main.
- GitHub Actions artifacts do not authorize distributing the proprietary ROM. Keep ROM-bearing archives private in accordance with repository policy.

## Reuse protocol and blockers

1. **No ledger gate promoted**: current ledger has candidate commit/ZIP hash `null`, no admitted L4/L5 witnesses and physical Windows unverified. Older CI completion is not a release pass and a job artifact digest cannot substitute for the real release ZIP digest.
2. Product lane must first nominate one exact integrated Windows binary + inner ZIP checksum and demonstrate a real controller-first profile/racer → native 1P/2P → actual settled result → Records + reentry path. QA must independently witness the same pinned binary and user root. Do not rebuild once per QA gate.
3. Reuse `tools/Test-URRecompPortable.ps1`, `docs/QA-PLAYER-JOURNEYS.md`, existing Windows smoke/process fixtures, `docs/WINDOWS-CLEAN-MACHINE-ACCEPTANCE.md` and the original/native course oracle. First targeted L4: separate-process Records survival after a **newly played** result, two-pad participant/result authenticity, held-button pause and return, and post-crash unchanged incumbent profile/SRAM.
4. Independently sample real dissimilar physical Windows systems for L5 controller, output/audio latency, devices, clean startup, readability and prolonged use. Hosted `Expand-Archive` and dummy audio cannot establish this.
5. The ledger validator now rejects invented release decisions, nonboolean physical flags, unpinned release decisions, unsupported L5 pass claims, undated witnesses, unreviewed waivers and unsupported failed-gate assertions. Its passing result verifies bookkeeping only. For a waiver supply `waiver_reason`, `waiver_approved_by`, and timezone-aware `waiver_approved_at`; for a witness use a timezone-aware `tested_at` and the **inner portable ZIP** SHA-256.

**Stop/revisit:** Reinspect after a product owner nominates a specific exact source SHA + ZIP checksum and fresh-process integrated route. Do not repeatedly rerun the older smoke or promote unexecuted journeys. Release blockers and gate status remain with their owning product/gameplay/graphics lanes and the independent ledger, respectively.
