# H26 Agent 2 nested recovery: bounded inspection checkpoint (2026-10-23)

This is a **research and preservation observation**, not new Windows/native
acceptance, source publication approval, or a claim that every recursive
archive member has been authenticated.

## Original bytes and manifest

Vault Evidence file ID: \`142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ\`
(\`20261021T0216Z-agent2-h26-five-line-recovery.zip\`).

- Exact original bytes: **28,106,236**
- SHA-256: \`601d6131f90b427f29c53d0cee5be69cb4bacde467fda45e45b8144d5b18be00\`
- Outer ZIP: 33 members, 28,874,394 declared expanded bytes.
- \`H26-ARCHIVE-MANIFEST.json\` declares 32 payloads; all 32 matched
  their exact filename, byte length and SHA-256. No missing/undeclared
  outer payloads were observed.
- Five nested Evidence ZIPs are present. The largest branch is
  \`evidence/agent2-h25.zip\` (24,645,725 bytes), which contains
  \`evidence/agent2-h24.zip\` (22,328,298 bytes).
- A selected path through H25 → H24 was CRC-checked and hash-verified,
  without recursively unpacking other branches. H25 ZIP SHA-256:
  \`eecc4d72fb55b0b2611828107d31b756e05609997279722b771eefa6e3af2c22\`;
  H24 ZIP SHA-256:
  \`46781fbac9597f5d372a46796ef26bb9549884c47b7116cd2a50fa01ad662b8a\`.
- The original total recursive content breaches the existing global
  128 MiB expanded-inspection budget. **Do not increase that budget
  merely to obtain a green global crosswalk.**

The separate [GitHub Actions outer CRC proof](https://github.com/gamesbyian/UR-Recomp/actions/runs/40027157602)
downloaded the identical 28,106,236-byte ZIP and verified 33 outer members.

## Recovered test execution

Using a temporary isolated directory, only explicitly selected original
source, referenced modules and the five preserved Evidence ZIPs were placed
under the archived paths. The QA06 block-consistency dependency was taken
from \`evidence/agent5-h25.zip\`, where it actually exists.

The original \`tests/test_h26.py\` test suite ran **9/9 passing normally
and 9/9 under Python \`-OO\`**. No game ROM, guest replay, physical
capture, Windows run or release gate was executed or credited.

## Comparison with fresh main

The following archived research is substantively represented on main:

- QA01 sparse opposite-state capture priority:
  \`tools/qa01_opposite_state_probe_priority.py\`.
- QA08 future chromatic probe limitations:
  \`tools/qa08_probe_robustness.py\` and the existing H26
  identifiability tests. No authentic chromatic pixel measurement has
  been added by recovering the old suite.
- QA06 false-positive when shifting entire source-pixel blocks:
  \`tools/qa06_source_shift_negative.py\` and
  \`tests/unit/test_qa06_source_shift_negative.py\`.
- Records post-check/prepublication mutation limitation:
  \`tests/unit/test_export_baldosa_earned_1p_run.py\`, including an
  existing synthetic just-before-publish mutation test.
- Archived QA06 dependencies \`qa06_original_block_consistency.py\`
  and \`qa06_raster_roi_reference.py\` are exact Git blobs already on
  main (\`a0c539c724e3fdf0e5776130f83c630a4690fad8\` and
  \`be9a26708135aebf618655038b836bc7c9ee40a4\`).

The H25 transitive-manifest finding remains historical provenance, not
independent gameplay proof. No unique, release-critical implementation
has been identified from the H26 top-level suite in this pass.
This is **not** a disposition of every member in each nested ZIP.

## Repeat a scoped nested inspection

Run \`tools/recovery_scoped_zip_audit.py\` using the real downloaded
file in a local environment. It never extracts or publishes member bytes.
It reports selected-member CRC/hash proof and explicitly says that
**unselected contents remain unverified**.

\`\`\`bash
python3 tools/recovery_scoped_zip_audit.py \
  --archive /tmp/20261021T0216Z-agent2-h26-five-line-recovery.zip \
  --expected-sha256 601d6131f90b427f29c53d0cee5be69cb4bacde467fda45e45b8144d5b18be00 \
  --member evidence/agent2-h25.zip \
  --member evidence/agent2-h24.zip

python3 tools/recovery_scoped_zip_audit.py \
  --archive /tmp/20261021T0216Z-agent2-h26-five-line-recovery.zip \
  --expected-sha256 601d6131f90b427f29c53d0cee5be69cb4bacde467fda45e45b8144d5b18be00 \
  --member evidence/agent5-h25.zip \
  --leaf work/qa06_original_block_consistency.py
\`\`\`

The second command verifies an exact selected source leaf and reports its
Git blob SHA without exposing its bytes. A hash match means byte identity,
**not** independent integration, provenance authorization or release QA.

Preserve the original Drive bundle. For integration decisions, compare
against the latest main and active PRs, and record any genuinely new
member individually in [issue #2088](https://github.com/gamesbyian/UR-Recomp/issues/2088).
