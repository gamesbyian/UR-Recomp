# WIDE-07 authentic five-bit normalization: zero residual (2026-11-17)

## Executed witness

- GitHub-hosted run: https://github.com/gamesbyian/UR-Recomp/actions/runs/44027943031
- Exact experiment source: `12bded310def4303865551f98eee00942e1bb2fd`, branch `experiments/wide07-fivebit-real-20261117`
- Command: `bash experiments/run.sh` (standing `script_linux` hosted experiment).
- Retained evidence: https://github.com/gamesbyian/UR-Recomp/actions/runs/44027943031/artifacts/14304176694 ; ZIP SHA-256 `035542a152d2128100ae0bcf2db365e47a52ae115d3fbfe144b847564a710d30`; expires 2026-12-01.
- Source frame artifacts: original-USA `14184488104`, native `14181849776`; producer source SHAs previously recorded in the genuine green-channel evidence: original `05701c1d19389e90c86b8294a78e4d2ede95183b`, native `150a0199853b514928803b552e6fd73b642e0ede`. These are historical producer identities, not the current experiment checkout.
- Both framebuffers 256×224 = 57,344 pixels, actual decoded source bytes. The hosted log contains the JSON classification and per-pixel witnesses.

## Exact observed comparison

| Original capture / guest frame | Native capture / guest frame | Raw green mismatches | Native five-bit compatible pixels | Residual after comparison-only five-bit→six-bit normalization |
| --- | --- | ---: | ---: | ---: |
| 899 / 1935 | 899 / 1945 | 55,571 | 57,344 | **0** |
| 902 / 1938 | 900 / 1948 | 55,570 | 57,344 | **0** |

The native green values are five-bit compatible at every pixel in both real frames. Original green values are compatible with six-bit RGB565 expansion at every pixel. The experiment's explicit mapping of native five-bit green to the hypothesized six-bit original output representation removes all measured green differences; residual-coordinate arrays are empty. Example at (0,0): native green 165, original green 166. Earlier real-byte comparisons measured zero red/blue differences.

**Interpretation:** this is strong evidence that the apparent 55k-pixel discrepancy arises from the differing producer/output green-channel expansion conventions. It is not proof that the underlying original/native renderer internals or game behavior are equal. No renderer change is justified merely to make capture formats agree.

## Remaining discriminators and next executable work

1. Trace source conversion paths for original Snes9x RGB565→BGRX8888 and native snesrecomp→BGRX8888; confirm exactly where five-bit green is expanded and whether comparison-only normalization matches the intended output contracts. Preserve original source output and compare in a canonical, documented colour space.
2. **Resolve phase and input registration:** original guest frames 1935→1938 versus native 1945→1948, and capture indices 899→902 versus 899→900. Establish common input-timeline and guest-clock registration before interpreting spatial agreement as behavior parity.
3. Run fresh matched-clock moving-course original/native capture pairs, then extend to the complete USA course with independently checked event/finish criteria. Do not award course credit on these two checkpoints.
4. If the real producer code proves a bug rather than merely different output conventions, apply the smallest source fix and rerun the authentic comparison. If source acquisition is blocked, switch to RF095/Zoo actual PCM clock/output-stage registration.

**Acceptance remains 0/45 USA courses.** The workflow success and zero normalized residual are bounded evidence, not a completed course.
