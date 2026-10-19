# QA01 RF062: logging control is not wrapper or cross-epoch causality

**19 October 2026. Independent source-authentic, ROM-free archival qualification.** Three distinct scientific questions must not be collapsed merely because they involve the same decoded native sound opcode `82:82F0` and byte `11:C774→D0`:

- Does enabling ten RF062 **runtime diagnostic log records** alter guest execution when using **the same native executable**? The genuine RF062 logging ON/OFF case answers a narrow portion of this positively.
- Does substituting one **compiled native read wrapper** alter generated code, CPU helper cadence, memory or sound outcomes? **Not yet qualified.** Disposable experiment #1975 correctly failed a generated-source-change gate before executing native cases; an unexecuted wrapper does not gain evidence from the logging experiment.
- Why did original/native source-epoch WRAM fidelity shift from **RF066 51/78 exact snapshots** to **RF062 46/78**, while the native paced-helper census shifted from historical **656** to newer **655**? Source-epoch raw comparisons show the mismatch but **cannot establish a cause** because both original and native compiled emulator binaries changed.

## Genuine immutable evidence inputs

`tools/qa01_rf062_evidence_factorization.py` reopens four actual case/binary ZIPs and chains existing **merged** independent reviewers. Every ZIP is checked against its fixed exact published SHA256 before interpreting the content:

| Source case | Archived artifact | Immutable SHA256 |
|---|---:|---|
| RF066 original/native Zoo [run 39219862021](https://github.com/gamesbyian/UR-Recomp/actions/runs/39219862021) | 12171791431 | `494737bb6a1c422141c40f7175883f212767c3d774ee63fb0ba82add78cb445f` |
| RF062 genuine executed native Zoo [run 39308179192](https://github.com/gamesbyian/UR-Recomp/actions/runs/39308179192) | 12214214743 | `b8287234d2fe515ee32b19b3d2a9b0e1bb58104b437de3a5cbe2e32e3af093ff` |
| RF062 real same-native-binary logging OFF/ON [run 39315208102](https://github.com/gamesbyian/UR-Recomp/actions/runs/39315208102) | 12219402017 | `b94660b8ffb0cfb1cd35ec9fe3a3c1c8c6b44a46d865272b8cfdad2e62078cbd` |
| RF062 actual executed original/native binary archive for logging experiment | 12218451896 | `83233faded8aa546025f59abe50c9ba29f109250f5bcafb2e20cdb5d7780bc37` |

It invokes `qa01_rf066_rf062_full_raw_crosswalk.audit` to independently reopen **all 388 complete original/native WRAM+SRAM images in each of the two source epochs**, verify identical source controller byte streams, and recompute both within-case 78-checkpoint full-WRAM unmasked difference totals. It invokes `qa01_rf062_same_binary_ab.archived` with the actual compiled binary ZIP to independently re-open the two ON/OFF logs, all four real source controller input files, both producer/source receipts and the **native executable SHA256 `31790cd408950ef20153031b5633f4045aa753368f6b94170ece607b5950a53a`**. That exact native executable SHA is rechecked independently against the RF062 executed-case producer. Finally it parses the ten actual `82:82F0` native RF062 records from the RF062 guest log using the existing strict helper-return consumer.

## What the evidence establishes, and what it does not

The genuine **same-executable** RF062 logging OFF/ON case independently produced **655/655 identical native RF054 paced helper read rows**, including all exact read-address, A/Y/D, direct-page context, order and native CPU master clocks, while the RF062 direct diagnostic records changed **0→10**. Both original/native supplied controller file bytes and source/movie/core/executable/script identities stayed the same. Within the bounded original/native gameplay mesh and successor observations, native RF062 **logging** did not perturb the observed CPU read trace. It does not show that changing the compiled read wrapper itself is harmless.

Conversely, the earlier RF066 versus later RF062 executions used the same original 2014 ROM/movie/controller bytes, and the original guest's retained full WRAM/SRAM stayed **194/194 images identical**; native SRAM stayed 97/97 identical. Yet **15/97 native WRAM images changed (77 byte occurrences)** and the original/native 78-point mesh went from **51 exact and 92 differing-byte occurrences → 46 exact and 104**. Crucially the original and native compiled executables both changed, so source-era drift or compiled-wrapper differences remain scientifically confounded. One real `82:82F0,11:C774→D0` read has been observed and remains a bounded read, not a first *differing* consumed byte nor a complete course proof.

The new independent verdict explicitly marks `historical_656_vs_655_missing_helper_attributed_to_logging=false`, `RF062_read_wrapper_replacement_noninterference_proven=false`, and `different_binary_epoch_native_Wram_change_cause_proven=false` even when the narrow runtime-logging control is positive. Synthetic tests mutate the same native binary SHA, source ROM, helper count, master-clock proof, source input controls, 388 raw-image population, observed native changed-byte counts and attempted wrapper/release promotion, all failing closed.

## Reproduce without guest execution

```bash
python3 tools/qa01_rf062_evidence_factorization.py \
  --rf066 /verified/RF066-zoo.zip \
  --rf062 /verified/RF062-native-zoo.zip \
  --ab-case /verified/RF062-logging-ab.zip \
  --ab-binaries /verified/RF062-logging-binaries.zip \
  --output /new/QA01-RF062-separate-controls.json
```

The lightweight `.github/workflows/qa01-rf062-evidence-factorization.yml` downloads exactly these already executed authentic cases and re-runs the same read-only four-ZIP validation, while retaining only a compact JSON. No binary is rebuilt or replayed by this qualification, and no large factory is authorized. The disposable wrapper-substitution experiment must first satisfy its separate **generated-source single-callsite identity** guard, then obtain a real same-binary-family native read/memory A/B before any wider claim is possible. Source-matched original/native opcode-phase parity, whole-race frames, Windows disk persistence and the first genuine USA complete event remain **HOLD, 0/45 accepted events and 0/12 release gates**.


**Guest input cross-case join:** In addition to the within-run original/native controller file equality, this review independently opens the **actual original and native input file bytes in the RF062 executed case**, hashes them and requires exact equality against the separately reopened guest-input digests from the RF062 same-native-binary logging OFF/ON case. This is a true cross-case byte check, not a guess that unchanged movie SHA implies identical transported input segments. Forged or altered guest input digests fail the independent verdict; no actual CPU joypad read equivalence is inferred.
