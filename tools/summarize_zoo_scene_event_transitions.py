#!/usr/bin/env python3
"""Analyze observed event-state changes in a paired original/native Zoo window.

Inputs are POSTFRAME guest state. A progression change between two samples
is a bounded observation, NOT evidence that the current postframe contact
triggered the handler. In the USA main race loop, course-object dispatch
precedes the next contact/surface sampler. One-frame prior stored contact
is a *candidate* dispatch source only; same-frame 0F09 PC observation is
still required for causality.

Keep this detector independent of position/velocity comparisons so an
earlier motion drift does not conceal later checkpoint/lap disagreements.
"""
from __future__ import annotations

from typing import Any

PROGRESS_FIELDS = ("p1_next_checkpoint", "p1_finish_gate",
                   "p1_laps_remaining")
CONTACT_FIELD = "p1_stored_contact"
BOOST_FIELD = "p1_boost"
TIMER_FIELDS = ("timer_minutes_raw", "timer_tens_raw",
                "timer_seconds_raw", "timer_tenths_raw",
                "timer_subtick_raw")


class EventEvidenceError(ValueError):
    pass


def surface_slot(word: int) -> int | None:
    """Decode the same packed C000 slot selector observed in the USA game."""
    if type(word) is not int or not 0 <= word <= 0xFFFF:
        raise EventEvidenceError("stored contact word must be an unsigned u16")
    if not (word & 0x03FF):
        return None
    return ((word & 0x000F) >> 1) + ((word & 0x03F0) >> 2)


def _active(row: dict) -> bool:
    return row.get("in_race") == 1 and row.get("track_id") == 1


def _required(row: dict, keys: tuple[str, ...]) -> None:
    for key in keys:
        if type(row.get(key)) is not int:
            raise EventEvidenceError(f"missing/inconsistent event-state field: {key}")


def observed_transitions(rows: list[dict]) -> dict:
    """Summarize each between-snapshot state mutation without inventing PCs."""
    if not rows:
        raise EventEvidenceError("empty Zoo scene checkpoints")
    for i, row in enumerate(rows):
        _required(row, ("relative_frame", "in_race", "track_id"))
        if row["relative_frame"] < 0:
            raise EventEvidenceError("guest-relative frame must be nonnegative")
        if i and row["relative_frame"] <= rows[i-1]["relative_frame"]:
            raise EventEvidenceError("event samples are not strictly chronological")
    first_exit = next((row["relative_frame"] for row in rows if not _active(row)), None)
    active = []
    for row in rows:
        if not _active(row):
            break
        _required(row, (*PROGRESS_FIELDS, CONTACT_FIELD, BOOST_FIELD))
        active.append(row)
    progress = []
    contacts = []
    for previous, current in zip(active, active[1:]):
        interval = current["relative_frame"] - previous["relative_frame"]
        changed = {field: {"before": previous[field], "after": current[field]}
                   for field in PROGRESS_FIELDS
                   if previous[field] != current[field]}
        if changed:
            progress.append({
                "interval_start": previous["relative_frame"],
                "interval_end": current["relative_frame"],
                "interval_guest_frames": interval,
                "observation_resolution": (
                    "adjacent_postframe_only" if interval == 1
                    else "sparse_interval_may_contain_multiple_events"
                ),
                "progress_changed": changed,
                "previous_postframe_stored_contact": previous[CONTACT_FIELD],
                "previous_postframe_contact_slot_candidate": surface_slot(
                    previous[CONTACT_FIELD]),
                "next_postframe_stored_contact": current[CONTACT_FIELD],
                "next_postframe_contact_slot": surface_slot(
                    current[CONTACT_FIELD]),
                "phase_limit": (
                    "USA object dispatch precedes new contact sampling. "
                    "Previous postframe contact is a dispatch INPUT "
                    "candidate, not an observed handler PC/causal proof."
                ),
            })
        if previous[CONTACT_FIELD] != current[CONTACT_FIELD]:
            contacts.append({
                "interval_start": previous["relative_frame"],
                "interval_end": current["relative_frame"],
                "interval_guest_frames": interval,
                "from_word": previous[CONTACT_FIELD],
                "to_word": current[CONTACT_FIELD],
                "from_slot": surface_slot(previous[CONTACT_FIELD]),
                "to_slot": surface_slot(current[CONTACT_FIELD]),
            })
    return {
        "observed_active_samples": len(active),
        "first_nonactive_relative_frame": first_exit,
        "progression_change_intervals": progress,
        "stored_contact_change_intervals": contacts,
        "progression_change_interval_count": len(progress),
        "stored_contact_change_interval_count": len(contacts),
        "scope": (
            "Original/native POSTFRAME WRAM state only; sparse intervals "
            "cannot localize a transition to one frame; adjacent frames "
            "cannot identify the executed handler or contact-point cell."
        ),
    }


def first_field_disagreement(
    reference: list[dict], native: list[dict], fields: tuple[str, ...]
) -> dict | None:
    if len(reference) != len(native) or not reference:
        raise EventEvidenceError("reference/native sample counts differ")
    previous = -1
    for ref, nat in zip(reference, native):
        frame = ref.get("relative_frame")
        if type(frame) is not int or frame <= previous:
            raise EventEvidenceError("invalid reference guest-relative checkpoint order")
        if frame != nat.get("relative_frame"):
            raise EventEvidenceError("reference/native frame phases differ")
        previous = frame
        if not _active(ref) or not _active(nat):
            return {
                "relative_frame": frame,
                "classification": "scene_not_pairwise_active",
                "reference": {"in_race": ref.get("in_race"), "track_id": ref.get("track_id")},
                "native": {"in_race": nat.get("in_race"), "track_id": nat.get("track_id")},
            }
        _required(ref, fields)
        _required(nat, fields)
        changed = [k for k in fields if ref[k] != nat[k]]
        if changed:
            return {
                "relative_frame": frame,
                "classification": "observed_field_disagreement",
                "fields": changed,
                "reference": {k: ref[k] for k in changed},
                "native": {k: nat[k] for k in changed},
            }
    return None


def observed_start_phase(rows: list[dict]) -> dict:
    """Bound race-flag versus first P1 horizontal X change / stopwatch tick.

    A horizontal-X change is NOT first physical motion. In the historic
    original Snes9x Zoo race, P1 vertical motion occurs during countdown.
    The first observed X deviation and stopwatch tick instead delimit
    original release/horizontal travel and live clock activation.
    """
    if not rows:
        raise EventEvidenceError("empty start-phase rows")
    active = []
    for row in rows:
        if not _active(row):
            break
        _required(row, ("relative_frame", "p1_x", *TIMER_FIELDS))
        for name in TIMER_FIELDS:
            if not 0 <= row[name] <= 255:
                raise EventEvidenceError("timer digit out of byte range")
        active.append(row)
    if not active:
        return {
            "initial_active_frame": None,
            "first_p1_x_change_interval": None,
            "first_nonzero_timer_interval": None,
        }
    start = active[0]
    start_x = start["p1_x"]
    timer_initial = tuple(start[x] for x in TIMER_FIELDS)
    x_change = None
    tick = None
    for previous, current in zip(active, active[1:]):
        if current["relative_frame"] <= previous["relative_frame"]:
            raise EventEvidenceError("start-phase frames are not chronological")
        if x_change is None and current["p1_x"] != start_x:
            x_change = [previous["relative_frame"], current["relative_frame"]]
        if tick is None and any(current[name] != 0 for name in TIMER_FIELDS):
            tick = [previous["relative_frame"], current["relative_frame"]]
    return {
        "initial_active_frame": start["relative_frame"],
        "initial_p1_x": start_x,
        "initial_timer_raw": list(timer_initial),
        "first_p1_x_change_interval": x_change,
        "first_nonzero_timer_interval": tick,
        "qualifier": (
            "Sampled postframe windows only. First P1 X displacement is "
            "horizontal onset, NOT first vertical motion or proof of Go HUD. "
            "Exact frame requires adjacent observations including the change."
        ),
    }


def paired_event_diagnostics(reference: list[dict], native: list[dict]) -> dict:
    original = observed_transitions(reference)
    recomp = observed_transitions(native)
    return {
        "schema_version": 1,
        "source_scope": "bounded guest-relative POSTFRAME original/native samples",
        "reference_observed": original,
        "native_observed": recomp,
        "first_progression_state_disagreement": first_field_disagreement(
            reference, native, PROGRESS_FIELDS
        ),
        "first_stored_contact_disagreement": first_field_disagreement(
            reference, native, (CONTACT_FIELD,)
        ),
        "first_boost_disagreement": first_field_disagreement(
            reference, native, (BOOST_FIELD,)
        ),
        "first_stopwatch_disagreement": first_field_disagreement(
            reference, native, TIMER_FIELDS
        ),
        "reference_start_phase": observed_start_phase(reference),
        "native_start_phase": observed_start_phase(native),
        "authority_limit": (
            "Separate diagnostics preserve event-state disagreements after "
            "earlier motion divergence. Equality at sampled frames or an "
            "empty event list is NOT proof of full checkpoints, laps, finish "
            "or no transient events between sparse samples. Only original "
            "PC/handler capture can adjudicate instruction-time causality."
        ),
    }
