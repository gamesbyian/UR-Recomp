# QA01/07: RF079 actual BIT return and BPL outcome, genuine bounded Zoo case

**19 October 2026. Independent source-archive judgment: HOLD, 0/45 USA and 0/12 Windows.** This is a new research **binary/source execution epoch**, downstream of the independently qualified [original RF076 fetched-PC](QA01-RF076-ORIGINAL-FETCH-NMI-INDEPENDENT-20261019.md) and [nine native NMI](QA01-RF076-NATIVE-NINE-NMI-INDEPENDENT-20261019.md) archive findings. The older 78-pair race images must **not** be silently transplanted into this experiment.

## Exact original research identity

Agent 1's **temporary, unmerged** [RF079 PR #2003](https://github.com/gamesbyian/UR-Recomp/pull/2003) produced completed single-case [run 39347619428](https://github.com/gamesbyian/UR-Recomp/actions/runs/39347619428). Independently reopened the genuine **199-member** case ZIP, artifact **12232740002**, original SHA256 `2721255d5f642422e414ec42db68d950f19382cd9b061e7e71846acd102c82e1`, and **11-member** compiled-original/native executable ZIP, artifact **12232261218**, original SHA256 `3566cf6b3d9e1abf054e3e86420087c4590544ff4650b07286c1c9efc5745086`. Both archives passed member CRCs and carried **byte-identical actual SHA256SUMS manifests**, including native ELF `c088ad8954df577ebffad84aa8d28d1e7e028385f74e2c64fd7e7dfbe0b3560e` and original Snes9x core `4b2c7391e3b4fb5b5bf1f2b7968b6aefe1c746229c54f3ebb0814fcc49325089`. Exact case source checkout is `71b0e217b747295a58a343567c8c3f6e1bddf2f7`.

Original replay log SHA256 `bf36108b5fa45bd01e3be4983b7602b9b722bfc6d40d9a7b2da39ffdec59ae37`, native replay SHA256 `105902f7dbcc8fe3ba2f3aebc6e29637c2eee769bf1dcc24773eca596e47fbd7`. These identify actual guest executions, not rewritten physics or a Windows candidate. This disposable case intentionally did not execute the whole standard Zoo raw 78-mesh or post-result cold Windows durability campaign.

## Independent native/original first-two-frame classification

Reopened raw actual replay text, verifying **12,958 contiguous original `QA01RF079ORIG` post-dispatch rows** (6,479 BIT / 6,479 BPL) and **60,819 contiguous native `QA01RF047NATIVE` rows**, including **6,483 direct-page `bit_real_return`** and **6,483 corresponding `bpl_actual_input`** rows. Neither stream has its bounded truncation marker. There remain **75 mixed physical native RF044/RF047 lines** (73 `read`, two `compiled_rti`) in this newer binary epoch.

| Source-local observation near actual NMI | 1017 divergent host label | 1018 comparison label |
| --- | --- | --- |
| Original first selected opcode after NMI | `82D4F0` (BPL `10`) | `82D4EE` (BIT `24`) |
| Original immediately observed branch/flag behavior | BPL with **N=0** jumps back to BIT; subsequent BIT yields **Nbyte=FF, N=1** and next BPL falls through to `82D4F2` | BIT yields **Nbyte=FF, N=1**, next BPL falls through to `82D4F2` |
| Native first selected opcode after handler | `82D4EE` BIT | `82D4EE` BIT |
| Native **actual returned** paced DP read | `D=0000`, `addr=0057`, **FF** | `D=0000`, `addr=0057`, **FF** |
| Native actual next BPL sampled N | **1**, `bitReadSeen=1`; fallthrough `82D4F2` | **1**, `bitReadSeen=1`; fallthrough `82D4F2` |

The original `Nbyte` is the post-dispatch *already-computed 65816 Negative operand state*, not an independently instrumented original physical direct-page bus read. It is evidence of the executed BIT's effect and next BPL decision, **not direct original consumed-byte equality with the native paced bus read**. The extra original N=0 branch at 1017 is an **intraframe execution-order observation**, not evidence that either guest took a different eventual loop-exit path. After the original's additional BPL→BIT cycle, both source-local traces independently reach `N=1` and a `BPL` fallthrough to `82D4F2`. That is **bounded selected branch-outcome convergence**.

The original sample population includes **3,228 Nbyte=00 BIT/BPL pairs** in host label 1017 and **3,249** at 1018, followed by one observed **Nbyte=FF BIT/BPL pair** per frame. The native actual paced BIT return recorded `00` **3,229** times at 1017 and **3,252** times at 1018, followed by one `FF` read and its N=1 BPL input in each. Different counts and distinct original/native host clock domains must not be normalized away as parity or assigned an inferred instruction shift.

## Executed QA verification and original archive continuity

The [independent archive-only run 39350208853](https://github.com/gamesbyian/UR-Recomp/actions/runs/39350208853) **passed** against the exact genuine provider source case and executable ZIP, including **84 ROM-free QA/adversarial tests**, contiguous physical row census and positive source-local BIT/BPL branch observations, while explicitly retaining `0/45` and `0/12`. It produced the 90-day [original-byte preservation artifact 12233500139](https://github.com/gamesbyian/UR-Recomp/actions/runs/39350208853/artifacts/12233500139), GitHub-wrapper SHA256 `f13f7c26e2accd4605443026c00e2a1be287e7bd1ed7d62df4adf3cd09c3d016`, expiring **2027-01-18**. QA independently downloaded, reopened and CRC-checked this wrapper; its nested original case SHA256 remains `2721255d...` and real binaries SHA256 `3566cf6b...`. The existing QA workflow now verifies the wrapper **and both inner-original hashes**, compares the present provider ZIP byte-for-byte, and after **2026-10-27** may use only the exact pinned original nested bytes. The actual expired-provider branch has not been exercised. A green archive audit certifies evidence, never a gameplay event.

## What is still missing

This case **does not identify a first actually consumed differing game-state byte at equivalent original/native instruction times**. In particular, neither a later native `D+0x57=FF` read, a source-computed negative flag nor four matching host-frame labels proves instruction-level parity of all intervening memory writes. Continuous USA course-state, unsampled checkpoints, completed event acceptance, product result publication, clean Windows PE/NV storage and physical release QA are separate requirements.

The minimal next discriminator, if needed, is a **same-epoch source-original actual DP bus-read capture**, paired to the native already-returned `FF` at the precisely identified BIT instruction, with source-local branch ordering/writes retained. Keep this research factual and bounded; don't patch gameplay timing or accept `1/45` from correlated source observations. **Verdict HOLD, 0/45 USA / 0/12 Windows.**
