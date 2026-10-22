"""Source-bound RF081 next-capture priorities from sparse opposite-state brackets.

Recover the H26 Agent 2 bounded-transition decision while reusing the merged
QA01 archive validator. This is a producer-request aid, not evidence of a
complete original/native event, monotonic divergence, or semantic phase match.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from zipfile import ZipFile

from qa01_sparse_transition_bounds import (
    PAIR, RF081_SHA256, TOTAL_SCENE_FRAMES, audit, transition_bounds,
)


def prioritize(samples: list[tuple[int, bool]], last_frame: int) -> dict:
    """Rank unobserved frames bracketed by *different* measured endpoint states.

    An opposite-state pair guarantees an odd number of changes, but neither
    locates the first change nor excludes additional changes. An unbounded
    suffix has no right endpoint and is never used as a first-change probe.
    """
    bounds = transition_bounds(samples, last_frame)
    transitions = []
    for (lo, left), (hi, right) in zip(samples, samples[1:]):
        if left == right:
            continue
        gap = hi - lo - 1
        transitions.append({
            "from": lo,
            "to": hi,
            "from_nonexact": left,
            "to_nonexact": right,
            "unobserved": gap,
            "first_possible_transition": lo + 1,
            "next_probe": lo + 1 if gap else None,
        })
    actionable = [row for row in transitions if row["next_probe"] is not None]
    first = actionable[0] if actionable else None
    onset = next((row for row in actionable
                  if not row["from_nonexact"] and row["to_nonexact"]), None)
    if len(transitions) != len(bounds["opposite_state_brackets"]):
        raise ValueError("transition bracket census disagrees with QA01 bounds")
    return {
        "schema": "qa01-opposite-state-probe-priority/1",
        "scene_pairs": len(samples),
        "first_observed_nonexact_frame": next((frame for frame, wrong in samples
                                               if wrong), None),
        "opposite_state_brackets": len(transitions),
        "brackets_with_unobserved_frames": len(actionable),
        "earliest_bounded_probe": first["next_probe"] if first else None,
        "earliest_bounded_interval": [first["from"], first["to"]] if first else None,
        "next_onset_probe": onset["next_probe"] if onset else None,
        "unbounded_suffix_after_last_sample": bounds["unconstrained_suffix_frame_count"],
        "unbounded_suffix_can_localize_first_transition": False,
        "transition_brackets": transitions,
        "assume_monotonicity": False,
        "new_guest_observations": 0,
        "complete_event_credit": 0,
    }


def audit_archive(path: Path) -> dict:
    """Require the exact authentic 41-pair RF081 archive before prioritizing."""
    baseline = audit(path)  # verifies archive SHA, members, 128-KiB pairs and 41 samples
    samples = []
    with ZipFile(path) as archive:
        for name in archive.namelist():
            match = PAIR.fullmatch(name)
            if match:
                frame = int(match.group(1))
                native = name.replace("/ref/", "/native/", 1)
                samples.append((frame, archive.read(name) != archive.read(native)))
    samples.sort()
    result = prioritize(samples, TOTAL_SCENE_FRAMES)
    if (result["scene_pairs"] != baseline["sample_count"] or
            result["opposite_state_brackets"] != len(baseline["opposite_state_brackets"]) or
            result["first_observed_nonexact_frame"] != baseline["first_nonexact_sample"]):
        raise ValueError("archive transition state disagrees with authenticated census")
    result["archive_sha256"] = RF081_SHA256
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: qa01_opposite_state_probe_priority.py AUTHENTIC_RF081_ZIP")
    print(json.dumps(audit_archive(Path(sys.argv[1])), indent=2))
