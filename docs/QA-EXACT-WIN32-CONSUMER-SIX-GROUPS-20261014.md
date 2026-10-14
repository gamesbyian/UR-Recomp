# QA-12: independently consume the *whole* real native Win32 evidence ZIP

The repository's independent `tools/verify_baldosa_romless_candidate_qa.py` formerly checked the bounded ROM-free package and old Windows guest traces but **rejected the first real complete six-native-game evidence** as containing extra filenames. This was an allowlist lag, not a new emulator or Modern product failure. Merely adding names as arbitrary allowed `.txt` files would risk admitting incomplete/forged or private uploads.

This QA-only change adds `tools/check_baldosa_win32_product_groups_qa.py` and a **fail-closed, exact allowlist** for three previously merged, separately source-reviewed families:

- Modern #1510's real **five-native-process** frontend-created MIKE 0/MARTIN 2, source-scored 2P, producer-reported one pair and fresh MIKE/MARTIN Records with a *test-only backend existing-P1 selector*. The report plus five logs must be present together and pass the already merged independent parser. Never count it as proof of human existing-profile selection.
- Modern #1522's real **six-native-process** native UI-selected version, distinguished by its additional `mike_ui_selects_martin/log.txt` and strict report field `p2_existing_profile_select_via_fixture_not_player_UI=false`. The actual X/A/B/A source-semantic selector stage, scored guest and both Records must pass the existing QA-12 source parser. This is the highest currently observed native integration level, still **not** a physical pad or full release gate pass.
- Modern #1513's standalone, genuinely native existing-P1 controller-semantic MIKE→ANDREW→MIKE next-boot selector, five native guest logs and one canonical report; source stale race lockout is independently checked. A separately created **nondefault ANDREW** first-racer trio is also now admitted under a bounded exact source/report contract. The nondefault ANDREW group carries no result/paired Records credit.

Each source group is **all-or-none**: a missing report, missing process, unexpectedly retained fixture handoff, altered source result, changed winner/time, duplicate member or unrecognized path rejects the entire archive. Every known log is limited to 2 MiB and report 64 KiB; symlinks and source claims of physical pads, full original/native parity or release credit reject. Arbitrary `.srm`, `.sfc`, player directory exports, files with suggestive extensions, duplicate and incomplete groups remain denied.

The exact externally obtained native Windows #1522 ROM-free candidate and same-run runtime proof can be replayed by independent QA using:

```bash
python3 tools/verify_baldosa_romless_candidate_qa.py \
  --actions-artifact /path/to/qa-1522-green-six-process-romless-wrapper.zip \
  --expected-actions-artifact-sha256 5094d68b89522b85b56c35e7bfa693bb9ebb2fb5976223e3d8dcadecc2daeb2f \
  --expected-source 8ba39e59d5b9e385e3ab99265a347c571ba7aa08 \
  --expected-zip-sha256 7d18497181af92bf887a40078176640b9eed459c76ec8b1b0b05b117bfacfc28 \
  --runtime-evidence /path/to/qa-1522-green-six-process-native-ui-windows-evidence.zip \
  --expected-runtime-evidence-sha256 7c4e1b941a12aeb2938782d4767b065cfcaa8364336aa92c560f74c9e6deb410
```

The `--expected-source` value in this command is **the embedded Baldosa AOT project revision**, not the merged `main` commit or a signed Windows release nomination. Provenance is candidate-limited. The actual 19.75 MiB AMD64 PE and all immutable files are hashed inside the **inner** ROM-free ZIP, separately from the outer Actions artifact. No ROM, private original save, or personal user data is required by the reviewer. A tool-positive source-log envelope is still `outcome=inconclusive`.

## Additional source-backed Windows launcher negative

Independently reading the exact same package identified a distinct current weakness, filed for the owning Modern implementation as [#1533](https://github.com/gamesbyian/UR-Recomp/issues/1533). The PowerShell preflight treats `[IO.Path]::IsPathRooted($d)` as if it meant fully-qualified, but Windows accepts rooted-relative drive inputs like `C:qa-relative` and root-relative inputs like `\qa-relative`. The call to `GetFullPath` then resolves against ambient drive/current working directory. The correct expected contract is that a caller-supplied save path be **fully qualified before normalization**, followed by reparse/package-escape checks. PowerShell 5.1/.NET Framework compatibility matters; modern .NET `Path.IsPathFullyQualified` is not guaranteed on that host. A Windows negative test is still needed. The independent ZIP checker reports `launcher_rejects_rooted_but_relative_user_root_verified=false` and `launcher_absolute_save_override_windows_negative_executed=false`, irrespective of any other benign static launcher tests. This does not establish a security exploit or actual data loss.

**Release gate stays closed:** no original/native complete scored course comparator accepted (**0/45**), no physical dual controllers, real audible sound, Original/HD/Widescreen 4K pixel acceptance, no independent byte decode of test-generated raw `.urrun/.urmatch`, no corrupt/redirected/concurrent catalog/SAVE PENDING/crash-before-receipt adversarial **same candidate** Windows execution, and no nominated merged-main final source/inner ZIP. Do not promote L4/L5 or infer physical hardware from SDL scripted native controls.
