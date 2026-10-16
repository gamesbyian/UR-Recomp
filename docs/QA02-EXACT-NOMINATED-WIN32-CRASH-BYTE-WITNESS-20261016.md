# QA-02 original nominated Win32 crash: independent actual byte witness

**2026-10-16 | P0 #1214 | Reproduced failure on immutable original Windows candidate | No release pass.**

## Candidate and executable provenance

- Exact nominated source: 11501a15dea38fa912335cfc63103ce3a7208001.
- Original ROM-free ZIP SHA256: 5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7.
- Original executable SHA256: 0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9.
- Genuine Windows Actions run: https://github.com/gamesbyian/UR-Recomp/actions/runs/38848852832 ; independent QA PR: https://github.com/gamesbyian/UR-Recomp/pull/1688.
- Original retained nominated owner artifact ID 12016101293, run 38828519791. Verified original exact ZIP, member manifest and executable before launch. Existing original Baldosa 2P race and existing QA fixture were reused, no substitute game executable. Fixture EXE SHA256 bc4727177f2cf2e0041808194d448f56907641ea06da6ae65b9e8dfac948892b; source race script SHA256 4e714899f53c3bbe501bbfcacf91dd549989c9beb7c2cf6265b13eb687142ec6. Correct original USA ROM SHA256 859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478.
- Complete original twelve-member byte snapshot Actions artifact ID **12024617002**, outer ZIP SHA256 **e70055be446d0afec493cde8ac004273e05425bae5acd3d874cd32e1b6da131a**, expires **2026-10-30 04:11:16 UTC**. Actual disposable test data kept in Actions, never committed to repository. Byte audit: ../analysis/evidence/qa02-exact-nominated-38848852832-win32-crash-byte-audit.json.

## Genuine process-cut reproduction

Same original Windows executable plays guest to frame 1952, opens real native Pause/Quit, successfully returns from its original RtlWriteSram and immediately calls opt-in _Exit(86) before publishing the typed checkpoint. The separate fresh Windows process without fault injection returns 7 before starting any guest frame with UR-BALDOSA-SAVE-MISMATCH: Named racer SRAM differs from committed profile data; selected_profile_sram_not_initialized. Neither typed nor raw is silently replaced by startup. This is a genuine abrupt Windows process exit, NOT external taskkill /F, power-cut or torn-write proof.

QA independently downloaded the actual artifact, verified whole ZIP digest and all 12 CRCs, rehashed every raw and typed file, decoded the real UR-HOST-PROFILE/5 generation-1 stock_sram (8192-byte hex), and established stock_sram equals full raw BEFORE, but not full raw AFTER. The raw difference is **28 real changed bytes**, with offsets 3707, 3708, 3709, 3710, 3711, 3712, 3713, 3714, 3811, 3812, 3889, 3903, 3904, 3905, 3906, 3907, 3908, 3909, 3910, 4032, 4036, 4040, 4044, 4048, 4052, 4056, 4273, 8191. Exact old/new hex pairs are in the JSON byte audit.

| Source file | Old SHA256 | New SHA256 | Changes |
| --- | --- | --- | --- |
| raw SRAM (8192 bytes) | bd9571f85e1b7ddfcf2b6913d5f3556c27ecadf65d353afbac29876e7d111c10 | 2f3009bb2436e3862e045df7f12da4d37845b83ada491cbc80cbef3a098f80d8 | 28 |
| typed profile (16525 bytes) | 1f98e49d51691816a9cd544c6fe71a5f74c3447933a7db6a8cf4e659921775b0 | 1f98e49d51691816a9cd544c6fe71a5f74c3447933a7db6a8cf4e659921775b0 | 0 |
| global selector (241 bytes) | eb0d0bd6c37dfa57766faff9e70f57d1730cabca36426d2863553256bbe87956 | eb0d0bd6c37dfa57766faff9e70f57d1730cabca36426d2863553256bbe87956 | 0 |
| roster catalog (44 bytes) | 75c0dcef43c3209a4f8793eae5ca035a535348412d3b8b807797fe7f176b1476 | 75c0dcef43c3209a4f8793eae5ca035a535348412d3b8b807797fe7f176b1476 | 0 |

The previously committed typed profile, selector and catalog are byte-identical after the process death and cold refusal. The raw save has 28 changed bytes. The user cannot resume this named profile until a deliberate safe recovery mechanism exists. Historical merged #1273 and original nominated run 38813101482 reported this same fault but lacked archived raw/typed bytes; this new downloaded artifact fills that specific evidence gap, without retroactively treating those reports as independent byte witnesses.

## Independent QA decision and Modern-owner handoff

Under the authoritative ledger definition, QA-02 is **failed** on the exact nominated Windows candidate: a reproducible written recovery requirement fails. The pass witness list is empty; **0/12 accepted release passes**, **0/45 USA original/native complete event acceptance**, no physical pad/audio/4K approval and no public release. The existing issue https://github.com/gamesbyian/UR-Recomp/issues/1214 remains owned by Modern/persistence, not independent QA.

**Minimum owner correction test:** seed an authentic 8192-byte named raw save exactly identical to the typed generation-1 stock SRAM, alongside independent second-profile data. Kill the same actual Windows executable between successful original raw write and typed commit after live guest change. Archive full old/new raw + typed + selector/catalog bytes. Following cold restart, prove an **explicit, consent-respecting recoverable old/new choice** (or genuinely safe transactional rollback) with valid playable progress, preserving both raw generations and the last-good typed state; reject any silent promotion of unknown newer raw, overwriting last good data or fabricated guest credit. Repeat fresh restarts and a second concurrent process. Assert no duplicate completed .urrun/.urmatch, ghost, PB, tournament receipt/award, and no unrelated profile mutation. Test failure at staging, raw I/O, typed publication and finalization with real Windows denied/full or missing storage and stale/corrupt catalog. Modern owner must change transaction/recovery implementation; QA does not edit product-owned files.

**Unverified here:** external OS taskkill, power interruption, actual NTFS sector tear, full/damaged disk, simultaneous player instances, completed-event duplicate sidecar exclusion and full J-02/J-07/J-08 cross-feature recovery, physical controllers, audio, display/4K, UI comprehension or complete original/native scoring. A safe refusal is not a successful recovery.

**Deferred human-only checklist:** when possible, run unchanged source-pinned ZIP with verified private USA ROM on clean physical Windows hardware, with two identifiable real controllers, audible guest/music effects, GPU/display settings including 4K, legible root UI, first-profile creation, source-earned two-player Records and Quit/cold reentry, plus actual controller disconnect/rebind. Preserve device identities and evidence. Do not count semantic SDL runner CI as these L5 witnesses.

Three-project preflight: existing UR native Windows harness and candidate verifier, pinned Baldosa original native SRAM path, and Malmazuke reference patterns only. No new framework, additional game candidate or duplicated Modern ownership.
