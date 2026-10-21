# UR-Recomp recovery entrypoint

**Purpose:** reconcile the Google Drive [Agent Recovery Vault](https://drive.google.com/drive/folders/1AAZyC49ZXFY81GB0hI31CAJnUd6iKcTn) with current GitHub `main` without losing unique source, negative evidence, rejected publication history or owner/physical acceptance obligations.

## Inventory (append-only, by exact Drive ID)

- [Initial 340-ID census](UR-VAULT-INVENTORY-20261020.tsv) and [baseline decisions](VAULT-RECONCILIATION-20261020.md)
- [H23 14-ID supplement](UR-VAULT-DELTA-H23-20261020.tsv) and [H23 evidence](VAULT-H23-ADDENDUM-20261020.md)
- [H24/H25 25-ID supplement](UR-VAULT-DELTA-H24-H25-20261021.tsv) and [archive/test adjudication](VAULT-H24-H25-RECONCILIATION-20261021.md)
- [Late H25 14-ID supplement](UR-VAULT-DELTA-H25-20261021.tsv), [87-ZIP 3,740-member content census](VAULT-87-ZIP-CONTENT-CENSUS-20261021.md)
- [Six new folder IDs and required recursive traversal](VAULT-RECURSIVE-LAYOUT-20261021.md). At that checkpoint the 393 files remained in root and the new folders were empty; **do not use root-only listing as a permanent total**.

These are checkpoint inventories, not a static live count. File moves preserve the Drive ID. The two historical same-name H10 ZIPs have different Drive IDs even though separately verified byte-identical. Never use filename or folder placement as an integration/delete verdict.

## Integrated by exact source or bounded semantics

- [#2089](https://github.com/gamesbyian/UR-Recomp/pull/2089) **MERGED** at `a3ae40508915889ff22ba728f0243d4a40d6959b`: fresh-main six-file Windows Records exporter/CI recovery, successful exact-head unit/hygiene/native Windows checks, and 6/6 source blobs equal to the former [#2060](https://github.com/gamesbyian/UR-Recomp/pull/2060), now **CLOSED UNMERGED** as superseded. H25 staging-race/name hardening held; no physical Windows gate.
- [#2071](https://github.com/gamesbyian/UR-Recomp/pull/2071) OBJ-depth evidence-only verifier and controls, **merged**.
- [#2072](https://github.com/gamesbyian/UR-Recomp/pull/2072) overflow-safe Modern text layout and tests, **merged**.
- [#2073](https://github.com/gamesbyian/UR-Recomp/pull/2073) original Dragster result witness and tests, **merged**; [#2074](https://github.com/gamesbyian/UR-Recomp/pull/2074) ties it to marshal authority without same-input parity, **merged**.
- [#2078](https://github.com/gamesbyian/UR-Recomp/pull/2078) RF081 sparse WRAM/SRAM census, **merged**; [#2081](https://github.com/gamesbyian/UR-Recomp/pull/2081) nine-frame NMI sequence-gap analyzer and [#2082](https://github.com/gamesbyian/UR-Recomp/pull/2082) selected-PC candidate census, **merged**, each with source-exact archived Git blobs and ROM-free regression tests.
- [#1711](https://github.com/gamesbyian/UR-Recomp/issues/1711) owns individual historic PR-less ref dispositions, including byte-identical code, semantically superior current implementations, recovered tests and intentional holds. **Do not bulk cherry-pick or delete historical refs.**

## Active holds and release boundaries

- [#2075](https://github.com/gamesbyian/UR-Recomp/issues/2075) ZIP portability verifier Win32 aliases/Unicode;
  [#2076](https://github.com/gamesbyian/UR-Recomp/issues/2076) QA04 validated-path/reopened-file TOCTOU.
- [#1996](https://github.com/gamesbyian/UR-Recomp/pull/1996) QA08 chromatic/source-PPU provenance remains draft/HOLD, with an earlier explicit source-publication safety denial. Do not retry denied writes or stack old composites.
- H24/H25 P2P signed SQLite trust, UHD raster-comparison, presented-frame/audio and CI merge-epoch source proposals remain **research-only** unless an independently authorized owner publishes narrow current-head source plus tests.
- No complete original/native USA events, physical Windows acceptance, release gate or art likeness approval was granted by this archive audit. Do not infer it from a synthetic test or folder named `Integrated`.

## Every artifact needs a disposition

For each exact Drive ID and useful inner member, record one of: **source-exact integrated (commit+blob+tests), semantically superseded (evidence), preserved research/negative finding, source publication denied (do not bypass), physically pending, or unreviewed**. A complete SHA member manifest proves preservation, not current-source integration. Never delete until a separate per-ID review shows zero unique dependencies and identifies authoritative retained copies. If an item has not received that review, **keep it**.

This is a living index for future recovery passes. When the vault changes, first traverse the root and all nested folders, then add a new immutable ID delta rather than overwriting historic snapshots.
