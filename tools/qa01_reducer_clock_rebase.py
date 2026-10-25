#!/usr/bin/env python3
"""Source-relative controller timeline transport into separately observed host clocks.

This is a file conversion, not evidence that either CPU polled the input.
"""
from __future__ import annotations
from controller_input import ControllerRun
from reduce_controller_fixture import encode


def paired_streams(runs: list[ControllerRun], reference_entry: int,
                   native_entry: int) -> tuple[bytes, bytes]:
    if (type(reference_entry) is not int or type(native_entry) is not int
            or not 0 <= reference_entry < 200000
            or not 0 <= native_entry < 200000):
        raise ValueError("paired guest clocks must be bounded independently measured frames")
    if not runs:
        raise ValueError("source controller route cannot be empty")
    if any(run.start < reference_entry for run in runs):
        raise ValueError("cannot shift unqualified pre-entry menu/controller inputs")
    if any(run.p2_mask for run in runs):
        raise ValueError("QA01 scene input shim currently qualifies only original P1 masks")
    offset = native_entry - reference_entry
    adapted = [ControllerRun(run.start + offset, run.duration, run.p1_mask)
               for run in runs]
    return encode(runs), encode(adapted)
