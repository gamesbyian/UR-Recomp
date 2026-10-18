# Independent original packaged Windows R/T recovery, 2026-10-17

**Disposition: accepted bounded hosted Win32 R/T source-byte witness, no QA release gate.** This is a read-only consumer result from original downloaded GitHub Actions artifacts, *not* a human operator trial, real Windows disk-full/partial-write test, electrical interruption, merged-main release package, or physical gamepad/audio/UHD verification.

## Exact tested provenance

- Product draft [#1713](https://github.com/gamesbyian/UR-Recomp/pull/1713) head `895109142c583727e948088212dc4c7cecf526a3`; the exact **tested PR-merge source** is `be4e97e80369f1d008ef6350a755b1a03cf5d73a`, with parents `f94328b4fcd90e563c7581adcce381501f0f71fe` (then-main) and that exact Modern head. Genuine [Windows Actions 39065673609](https://github.com/gamesbyian/UR-Recomp/actions/runs/39065673609) **success**, including both original CMD R/T option execution/cold boots and the earlier Q unchanged-save path.
- Original R/T artifact **12113990003** outer SHA256 `3620825ab368a97775f38c8b8ca05f3713cd1036c04796a06ee471e218f7be14`: exactly **47** original Actions ZIP members, CRC clean, independently rehashed **34** original raw/typed/selector/catalog/manual-archive source binary objects including sizes and per-member receipt digests.
- Separately downloaded ROM-free candidate artifact **12112818574**, outer SHA256 `837ddb7b617d6ff847db2a2f512349c86cd6e324aa8570fcb09b087dffe4818d`. Original four-file ROM-free Windows package SHA256 `c781526090ecdac9e58ffa65d7674156326b1309934ceb6ec2a12edafbd59712`; executable SHA256 `df894e4ddf8441e944189223ffa6a9e0ba1794cd58fa8e5334c1106fa1bf81cf` (**20,327,424 bytes**, verified PE32+ AMD64), original CMD SHA256 `b61d6b3836e21da6dd91dc4bcbf5cff19a85df6f73f07ee2bcd29a377fc678c3`. Original same-run binding artifact **12113695880** outer SHA256 `b0de84cba6cdf310997889ce51599f35cb24da0006c1c4446c0dae552a065646`, agreed exactly with tested source, executable, all immutable manifest members and ZIP; neither ROM nor player saves were included.

## Independent source-byte findings

Both original Windows fixture cases created the same true original-format full **8,192-byte** raw-vs-typed discrepancy (**exactly one byte changed at offset 256**, original stock SRAM signature retained). Real extracted `run-baldosa-modern.cmd` each displayed the R/T/S/Q prompt once, logged the actual Win32 injected R or T input with injector exit zero, selected recovery exactly once and relaunched its actual packaged game to one real first frame. The test forcibly terminated the original command's *whole child process tree* after source first frame, not after an arbitrary assumed delay.

| Immutable receipt | R: explicitly trust genuine raw | T: explicitly restore committed typed |
|---|---|---|
| Initial raw | `9697d6e71aae0f1b57291b47d619e947b7a4847694182ee332131528e9fc0797` | Same initial raw |
| Final raw | **same initial raw**, no overwrite | `bd9571f85e1b7ddfcf2b6913d5f3556c27ecadf65d353afbac29876e7d111c10` |
| Initial typed | `1f98e49d51691816a9cd544c6fe71a5f74c3447933a7db6a8cf4e659921775b0` | Same initial typed |
| Final typed | `c196daefe69dc91d5e014fd8d0cc1bcfacbc21b40f3289f33e46e3f636beb340` | **same initial typed**, no overwrite |
| Full immutable manual recovery archive SHA256 | `c1f287877576f6cbcbebaa8caf0b95430ca346e8682576a53d5206234b60fbeb` | Same exact pre-repair bytes |

The manual archive was independently decoded *byte for byte*: `UR-BALDOSA-MANUAL-SRAM-RECOVERY/1\n` + exact old typed length + raw-present `1` + raw length `8192` + original **complete typed binary + original complete raw binary**. R publishes typed metadata matching unchanged guest raw; T restores exact committed raw while preserving the entire original typed file. Both preserved the selector and catalog completely, with no untrusted fallback. The first and **second separate original game cold-start** snapshots of raw/typed/selector/catalog were byte-for-byte unchanged from immediately after the respective repair, and no recovery menu was shown on either cold start.

Independent command using the unmodified archived source:

```sh
python tools/check_qa02_win32_interactive_rt_original.py \
  --zip original-artifact-12113990003.zip \
  --sha256 3620825ab368a97775f38c8b8ca05f3713cd1036c04796a06ee471e218f7be14 \
  --cmd-sha256 b61d6b3836e21da6dd91dc4bcbf5cff19a85df6f73f07ee2bcd29a377fc678c3
```

QA [#1786](https://github.com/gamesbyian/UR-Recomp/pull/1786) adds this independent fail-closed verifier and adversarial negative controls. The validator and repository hygiene unit checks passed at its exact head `041d6c166339df526eb984979be95f1c454d1b0f`; local independent archive audit also passed after the actual original ZIP/PE/CMD were downloaded.

**Remaining P0:** source-bound **S** option on three registered racers including unrelated damaged third, real two-process lock competition, actual NTFS denied/partial/full storage and cold restart, physical human choice/keyboard/two controller/audio/UHD, and finally a *single integrated merged-main Modern+graphics source* built into a fresh candidate. The prior immutable owner source `11501a15dea38fa912335cfc63103ce3a7208001` and ZIP `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7` remain distinct. Release ledger **0/12**; complete USA event census **0/45**.
