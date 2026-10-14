# QA-12: first actual created-2P raw saved bytes in a genuine Windows artifact

**Independent exact source-byte inspection, not a final release pass.** After the six-native-process source-scored MIKE/MARTIN Records journey merged, Modern [#1536](https://github.com/gamesbyian/UR-Recomp/pull/1536) retained an actual bounded CI-created raw `.urrun/.urmatch` pair and both player profiles in its [green Windows workflow 38543163396](https://github.com/gamesbyian/UR-Recomp/actions/runs/38543163396), product PR head `18c3f69beee365de556cd7e5886a4c80609a54d7`. Independent QA downloaded the true Windows Actions artifact **11883577178**: 59,266 bytes, complete ZIP SHA-256 `74220d8956a77449527928fc00acb83eeb451289f531cc58072a00e30151265f`.

This positive archive **actually contains** source report, all six real native game-process logs, an exact bounded `ci-owned-raw-artifacts/manifest.json`, the player selector/catalog, original anonymous bootstrap 8-KiB save, **both** privately named profiles' full 8-KiB SRAM files and 16-KiB typed mirrors, and the one canonical newly source-scored `.urrun` / `.urrun.urmatch` pair. No ROM, bundled executable, private human save directory or arbitrary extra file is in the raw subtree. Full independently computed per-member SHA-256s and exact game source identities are retained in [this machine-readable QA review](../analysis/evidence/baldosa-win32-38543163396-native-created-2p-raw-byte-review.json).

## Independently decoded identities, source and transaction

The first-created player is MIKE, original source rider **0**, with raw 8,192-byte SRAM digest `adabbeb16a3292ccc0f4c4958b3c7016fa8025dc86182ae8c4ef6edbd81bc73f`. The distinct second-created player is MARTIN, source rider **2**, with raw 8,192-byte SRAM digest `48a8a5e15104a1bb05780bafa61ca5ff32dcf5da0c3a0427ae67cc4e430573a9`. The player catalog bytes consist of the exact two named records `mike|0|MIKE` and `martin|2|MARTIN`. Both typed profile `stock_sram` values decode to exactly their corresponding saved SRAM. The final selected host state is MARTIN, consistent with the separate genuine native gamepad-semantic MIKE→MARTIN UI switch and MARTIN's last fresh native Records process.

The exact exported run basename is `run-0001791970844282-0000.urrun`, SHA-256 `346296f664ccf37fd0310666a60d837269a6d1627b4f28162ad051d6c66c8a41`, internal canonical source FNV checksum **`01b72ad6fb9b9a2a`**. The matched `.urmatch` sidecar SHA-256 is `e1440b455b617a1726ccf17aa7a2e7dc96af7faabe302d9006693923125259c4`, with its **own** checksum `d214a7509ef52d81` and embedded run checksum equal to `01b72ad6fb9b9a2a`.

The independently decoded `URRUN 1` has `uniracers-usa`, exact required retail ROM SHA, pinned Baldosa build compatibility, `course:01`, mode `race-2p`, **2,231 original-native input frames** in **five** canonical nonoverlapping spans involving both seats, and elapsed ticks **1,654**. The sidecar independently encodes result **MARTIN (P2) WIN**, source scores MIKE **27.61s** / MARTIN **27.57s**, rider bytes 0/2 and matching lower-case profile hex IDs `mike` and `martin`. This agrees with the same-run source guest result and independent fourth/sixth native read-only Records (MIKE LOSS / MARTIN WIN).

Previously QA possessed only producer-reported run/match hashes. Those two actual files are **now present** and their SHA and internal formats can be independently recomputed from ZIP bytes. The archive still contains **one final pair snapshot**, not separately archived complete pre/post-viewer copies, so independent before/after byte immutability is not itself proven merely by a producer's reported hash map.

## New bounded independent reader

`tools/check_baldosa_win32_created_pair_raw_qa.py` strictly binds these raw files to **the same ZIP's exact six-process source-report and logs**. It refuses ambiguous/duplicate run basenames, wrong path prefixes, partial profiles, unsupported/extra files outside the strict known Windows source-group inventory and raw subtree (without awarding other groups any credit), symlinked raw archive members, wrong sizes or manifest hashes, inconsistent original SRAM/typed mirrors and player catalog, canonical run/match bad FNV checksums, unsafe/reordered run input spans, misbound source clock/winner/course/participant or any producer release credit. It accepts only exact disposable user-root source format and remains independent of Modern's writer. Usage on the unmodified downloaded real Actions ZIP:

```sh
python3 tools/check_baldosa_win32_created_pair_raw_qa.py \
  --runtime /path/to/real-artifact-11883577178.zip
```

ROM-free adversarial unit tests mutate and rehash fixture manifests to ensure a superficially consistent producer SHA does not mask a wrong actual saved rider or race. Those synthetic tests are **not** new original race execution or physical Windows evidence.

## Remaining release boundaries

**Positive independent gate progress:** bounded raw profile/selector/SRAM/first-created source run+match **byte-format and source-identity agreement**. **Still unverified:** original-USA vs native full course scored event comparator (**0/45**), real two-controller hardware, real audio device, full moving Original/HD/Widescreen/4K acceptance, disk-full and crash-before-receipt/SAVE PENDING/concurrent profile/reparse-root OS failures, final nominated merged-main Windows executable ZIP and packaged no-argument first-run journey. The separate Windows source-root issue [#1533](https://github.com/gamesbyian/UR-Recomp/issues/1533) remains active until an exact Windows negative test and owner repair establish absolute path validation.

The authoritative release ledger gate statuses remain unchanged and candidate source/ZIP null; source-owned success is **not L4/L5 physical acceptance**. No ROM or synthetic player SRAM bytes are committed to the repository, only non-sensitive SHA/decoded field summaries.


## 2026-10-14 same real 52-member archive reread after the #1549 rejection was detected

Independent QA downloaded **the original** real #1536 Actions artifact 11883577178 again, verified complete 59,266-byte ZIP SHA-256 \`74220d8956a77449527928fc00acb83eeb451289f531cc58072a00e30151265f\`, and enumerated all **52** members. The correct Windows archive contains multiple *previously source-qualified, independent product log groups* alongside exactly 7 created-pair source files and 10 bounded CI-owned raw files (1 manifest plus 9 raw members). **The initial #1549 whole-ZIP equals-created-group check was wrong and would reject the real archive.** The follow-up QA fix keeps unknown outer members excluded through the existing recognized Windows source-member inventory, while leaving each other group to its separate validator.

The separately re-read **actual byte payload**, not a synthesized test, confirms all 9 raw manifest member sizes and SHA-256s, both 8192-byte private SRAM rider offsets MIKE 0 / MARTIN 2, the canonical source run SHA \`346296f664ccf37fd0310666a60d837269a6d1627b4f28162ad051d6c66c8a41\` / independently recomputed FNV \`01b72ad6fb9b9a2a\`, matched sidecar SHA \`e1440b455b617a1726ccf17aa7a2e7dc96af7faabe302d9006693923125259c4\` / FNV \`d214a7509ef52d81\`, and source settled rider 0/2 P2 WIN result at f4378. Fresh MIKE LOSS and MARTIN WIN native Records logs plus exact MIKE→MARTIN next-process selector log are physically present. This **reconfirms earlier #1548 independent raw acceptance** without awarding new release credit; a full command-level rerun of the corrected reader remains subject to the repo's exact-head unit regression/CI.

No new pre-Records first snapshot existed in this historical source ZIP; original/native 45-event parity, physical input/audio, final merged Windows release EXE and OS crash/disk fault remain unverified.
