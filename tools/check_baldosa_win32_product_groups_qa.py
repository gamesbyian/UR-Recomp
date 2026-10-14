#!/usr/bin/env python3
"""Independent bounded admission of merged Modern Windows source-log groups.

Run only inside the already nominated ROM-free Actions runtime wrapper.
The five/six native process groups are distinct contracts. A fixture-selected
fifth process can never substitute for a real UI selector sixth process.
No raw .urrun/.urmatch bytes or physical pads are in these source groups.
"""
from __future__ import annotations

import hashlib
import zipfile

from check_baldosa_win32_created_pair_records_qa import (
    audit as audit_created_pair,
    FILES as CREATED_FIVE_FILES,
    UI_FILES as CREATED_SIX_FILES,
    PREFIX as CREATED_PREFIX,
)
from check_baldosa_win32_existing_profile_selector_qa import (
    audit as audit_selector,
    FILES as SELECTOR_FILES,
    PREFIX as SELECTOR_PREFIX,
)

FIVE_CREATED = tuple(CREATED_PREFIX + name for name in CREATED_FIVE_FILES)
SIX_CREATED = tuple(CREATED_PREFIX + name for name in CREATED_SIX_FILES)
SELECTOR = tuple(SELECTOR_PREFIX + name for name in SELECTOR_FILES)
ALLOWED_MEMBERS = frozenset(SIX_CREATED + SELECTOR)
MAX_REPORT = 64 * 1024
MAX_LOG = 2 * 1024 * 1024


def audit_extra_hosted_groups(archive: zipfile.ZipFile) -> dict:
    """Require all-or-none for every source group and pass exact raw bytes."""
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise ValueError("duplicate real Win32 source group archive members")
    name_set = set(names)
    created_present = set(SIX_CREATED) & name_set
    selected_present = set(SELECTOR) & name_set
    if created_present:
        # The first five-game result includes the report and both viewers,
        # while a sixth standalone UI process upgrades (never replaces) it.
        if created_present == set(SIX_CREATED):
            created_names = SIX_CREATED
            ui = True
        elif created_present == set(FIVE_CREATED):
            created_names = FIVE_CREATED
            ui = False
        else:
            raise ValueError("incomplete or ambiguous created P1/P2 source process group")
    else:
        created_names, ui = (), False
    if selected_present and selected_present != set(SELECTOR):
        raise ValueError("incomplete controller-existing-profile source process group")
    selector_names = SELECTOR if selected_present else ()

    def read(group: tuple[str, ...]) -> list[bytes]:
        result = []
        for index, name in enumerate(group):
            info = archive.getinfo(name)
            limit = MAX_REPORT if index == 0 else MAX_LOG
            # Even exact allowlisted filenames must not hide private saves,
            # symlinks or a compressed ZIP bomb.
            if (info.is_dir() or not 0 < info.file_size <= limit
                    or (info.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError("linked/oversized product Windows source group member")
            contents = archive.read(info)
            if len(contents) != info.file_size:
                raise ValueError("short decompressed product source group member")
            result.append(contents)
        return result

    metrics = {
        "hosted_real_six_native_process_ui_created_pair_and_both_records_log_consistent": False,
        "hosted_real_five_native_process_backend_selected_pair_log_consistent": False,
        "hosted_real_existing_p1_switch_both_directions_log_consistent": False,
        "hosted_user_created_pair_run_match_bytes_rehashed": False,
        "hosted_product_group_physical_joysticks_accepted": False,
        "hosted_product_group_original_event_parity_accepted": False,
        "hosted_product_group_release_gate_credit": 0,
    }
    if created_names:
        product = audit_created_pair(*read(created_names))
        if product.get("release_gate_credit") != 0:
            raise ValueError("nonzero created player release gate asserted")
        expected_ui = product.get(
            "martin_selection_via_real_native_ui_controller_semantics")
        if expected_ui is not ui:
            raise ValueError("reported existing P1 UI is unbound to source artifact")
        metrics["hosted_real_six_native_process_ui_created_pair_and_both_records_log_consistent"] = ui
        metrics["hosted_real_five_native_process_backend_selected_pair_log_consistent"] = not ui
        metrics["hosted_created_pair_actual_native_source_result_host"] = product["source_result_host"]
        metrics["hosted_created_pair_source_riders"] = product["source_rider_pair"]
        metrics["hosted_created_pair_report_sha256"] = hashlib.sha256(
            archive.read(created_names[0])).hexdigest()
        metrics["hosted_created_pair_original_run_and_match_bytes_unavailable"] = True
    if selector_names:
        selection = audit_selector(*read(selector_names))
        if selection.get("release_gate_credit") != 0:
            raise ValueError("nonzero selector standalone release gate asserted")
        metrics["hosted_real_existing_p1_switch_both_directions_log_consistent"] = bool(
            selection["p1_source_switch_mike_to_andrew_then_back_to_mike_observed"])
        metrics["hosted_existing_p1_source_report_sha256"] = hashlib.sha256(
            archive.read(selector_names[0])).hexdigest()
    return metrics
