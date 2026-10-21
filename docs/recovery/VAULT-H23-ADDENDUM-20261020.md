# UR-Recomp H23 recovery addendum (2026-10-20 UTC)

This addendum extends the [original 340-file intake](UR-VAULT-INVENTORY-20261020.tsv) with [14 additional exact Drive records](UR-VAULT-DELTA-H23-20261020.tsv). A new Drive listing returned **354 top-level files**. It is a static observation: five hourly agents may create additional files after this checkpoint. All new files are retained.

## Byte-verified H23 recovery containers

- Agent 4 H23, Drive ID `1h-h_S5i15Shi2ZyY7BjxJIayjKmJwInJ`, outer SHA-256 `0b9d7b6d108101103e5977e0db0957a55716c9e747e620ea4994b5dbe3ae2e71`: 33 ZIP entries, 32 declared payloads. Every payload hash in `MANIFEST.json` matches; no unlisted payload, duplicate ZIP name or CRC failure. The sources remain proposals.
- Agent 5 H23, Drive ID `1E7lAeheTxRvy6V9VotgeKEkSprEl24f0`, outer SHA-256 `10495a558c337b30dc223216966e771f9f52eec34161a3dfa0d5353b640734fc`: 44 ZIP entries, 43 declared payloads. Every `ARCHIVE-MANIFEST.json` entry matches; no unlisted payload, duplicate ZIP name or CRC failure. Source publication of the QA08 composite was explicitly safety-denied; no retry or alternate route is authorized by this addendum.

## Current findings requiring narrowly scoped decisions

1. **Modern Windows/exporter (#2060):** earned-run CI output moved outside source journey in commit `ee55e82`; unit/hygiene/hosted-Windows workflows green. New independent *workflow path contract* regression tests have now been committed to the PR branch (commit `0a758b38`). Conservative DOS-device handling (`CON .urrun`, root `CONIN$`/`CONOUT$`), surrogate encoding order and final merge-tree qualification still need source/owner review. Older patches target superseded blobs; do not blindly stack.
2. **QA04:** Agent 4 identifies a path preflight hardlink, symlink-root, control-character and UTF-16 validation gap in an isolated helper. Agent 5 H23 produces a C1/DEL negative control against the historical helper. Neither establishes physical Windows acceptance and previously refused comparable publications are not to be retried or disguised.
3. **QA08:** Independent read of SHA-pinned source archive `10bd91c7be06e3ac832675f2b5268bf179a2b03b5f07dcf8fd632fad18372ec2` finds 88 FINAL observations across 11 frames, but only **four distinct** `selected_rgb555/RGB8` combinations, each repeated 22 times: `4a52/138,138,138`, `56b5/161,161,161`, `4210/123,123,123`, `4631/130,130,130`. Brightness 14 matches all four; only four independent colour stimuli are exercised. This source-model consistency is neither original/native effective-PPU consumption nor a shipping pixel fix. The finding was filed on held PR #1996.
4. **QA06:** Synthetic full-coverage RGBA comparator and precise 4K/PAR geometry references still require actual host screenshots, source raster coverage and artistic approval. Current 4× character-likeness veto remains.
5. **Records/video and P2P:** Synthetic presented-frame identity, PCM/device clock and SQLite signed-anchor validation pilots remain outside the shipping tap/network and durable trust boundary. No MP4, direct P2P or rollback-safe monotonic authority has been proved.

## Safety and retention

No file deletions; no replay/guest logic changes; no acceptances granted. Old overlap, failed experiment evidence, synthetic mocks, and previously rejected patch attempts remain available and distinguishable in the vault. Promote only independent tests and exact-head reviewed code changes through normal PR/CI, and preserve original archive hashes, source-blob preimages and negative evidence.
