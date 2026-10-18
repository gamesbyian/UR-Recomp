#!/usr/bin/env python3
"""Game-scoped candidate: consume the first HDMA transfer in Uniracers' PPU.

The *real* original Snes9x / native Baldosa source-size RGB5 experiments
(2026-10-14, PRs #1577/#1614) proved this advance for native 2P countdown
1856 and three distinct moving 2P post-GO frames 2192/2208/2224.
The old prime repeated the first HDMA table entry; this advances the
already-transferred table/descriptor once instead.

CANDIDATE ONLY until original/native 1P, transitions, results, Windows
presentation, effective PPU window/OAM and hardware checks are adjudicated.
Do not upstream this globally to SNESRecomp: Gundam Wing has an explicit
different mid-frame HDMA first-slot contract. Never alter guest instructions,
CPU/APU clocks, input, SRAM, or the Modern product.

Apply solely to an exact pinned, disposable gamesbyian/uniracers-recomp
checkout built as the Windows UniracersSNESRecomp title. The source transform
is *identical* to the already executed all-channel experiment, apart from
this candidate's comment. It refuses unrelated game/core revisions.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

try:
    from tools import qa08_patch_hdma_prime_counterfactual as source_trial
except ImportError:
    import qa08_patch_hdma_prime_counterfactual as source_trial

MARK = "UR_UNIRACERS_HDMA_FIRSTLINE_CANDIDATE"
GAME_REV = "10b864b9d14a7b7416dd909eb7b054c88faef101"
CORE_REV = "075fbe4c8e0d97b0013be541795c39cb644a9709"
RELATIVE = Path("snesrecomp/runner/src/snes/dma.c")
REPLACEMENT = """    /* UR_UNIRACERS_HDMA_FIRSTLINE_CANDIDATE: 2P original-source experiment.
     * The first HDMA transfer has already consumed A-bus bytes. Advance the
     * repetition counter / descriptor just as normal visible HDMA does.
     * Game-specific Windows candidate only; NOT a cross-game core fix.
     * 1P, transitions, result scenes and hardware remain independent gates. */
    ch->repCount--;
    ch->doTransfer = (ch->repCount & 0x80) != 0;
    if ((ch->repCount & 0x7f) == 0)
      dma_hdmaLoadDescriptor(dma, ch);
  }
}"""
OLD_LENGTH = "    int len = transferLength[ch->mode & 7];"


def patch_source(source: str) -> str:
    """Return exact experimental transfer semantics; fail closed on drift.

    Reconstructing the old body allows bytewise idempotence without blindly
    trusting a marker: partial changes, altered branch logic and competing
    selective experiments are rejected.
    """
    if MARK in source:
        if source.count(MARK) != 1 or source.count(REPLACEMENT) != 1:
            raise ValueError("candidate marker/body modified or duplicated")
        if source.count(OLD_LENGTH) < 1:
            raise ValueError("candidate first-line transfer length missing")
        # Re-create the unmodified pinned function and verify that the
        # canonical experiment would regenerate this *entire* candidate.
        start, rem = source.split(source_trial.FUNCTION, 1)
        body, tail = rem.split(source_trial.NEXT, 1)
        if body.count(OLD_LENGTH) != 1 or body.count(REPLACEMENT) != 1:
            raise ValueError("candidate first-line function drifted")
        recovered = (start + source_trial.FUNCTION
                     + body.replace(OLD_LENGTH, source_trial.OLD_SAVE, 1)
                           .replace(REPLACEMENT, source_trial.OLD_RESTORE, 1)
                     + source_trial.NEXT + tail)
        expected = (source_trial.patch_source(recovered)
                    .replace(source_trial.NEW_ADVANCE, REPLACEMENT, 1))
        if expected != source:
            raise ValueError("candidate first-line transform differs")
        return source

    if any(mark in source for mark in (
        source_trial.MARK, "UR_QA08_CH7_ONLY_PRIME_EXPERIMENT",
        "UR_QA08_CH57_ONLY_PRIME_EXPERIMENT",
    )):
        raise ValueError("competing HDMA first-line experiment already applied")
    experimental = source_trial.patch_source(source)
    if experimental.count(source_trial.NEW_ADVANCE) != 1:
        raise ValueError("canonical all-channel experimental body missing")
    return experimental.replace(source_trial.NEW_ADVANCE, REPLACEMENT, 1)


def pinned_revision(path: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def apply_game_candidate(game: Path, *, write: bool = False) -> Path:
    game = game.resolve()
    if pinned_revision(game) != GAME_REV:
        raise ValueError("unrecognized Uniracers game commit")
    core = game / "snesrecomp"
    if pinned_revision(core) != CORE_REV:
        raise ValueError("unrecognized SNESRecomp framework commit")
    if not (game / "src/gen/dispatch_v2.c").is_file():
        raise ValueError("expected generated Uniracers guest was not found")
    path = game / RELATIVE
    original = path.read_text(encoding="utf-8")
    changed = patch_source(original)
    if write and original != changed:
        path.write_text(changed, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--apply-candidate", action="store_true",
                        help="stage only in the exact pinned disposable Uniracers game checkout")
    args = parser.parse_args()
    try:
        path = apply_game_candidate(args.game, write=args.apply_candidate)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"UR_UNIRACERS_HDMA_FIRSTLINE_REJECTED: {exc}\n")
    print(f"UR_UNIRACERS_HDMA_FIRSTLINE_CANDIDATE "
          f"applied={int(args.apply_candidate)} file={path} "
          "2p_original_rgb5=verified 1p_transition_results=unverified "
          "cross_title_change=none release_approved=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
