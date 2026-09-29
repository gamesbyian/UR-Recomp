#!/usr/bin/env python3
"""Validate and summarize the external-evidence worklist."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


ALLOWED_VALUE = {"critical", "high", "medium", "low"}
ALLOWED_COST = {"low", "medium", "high"}
ALLOWED_STATUS = {
    "ready",
    "local-reproduction-pending",
    "acquisition-needed",
    "archival-hunt",
    "author-pivot",
    "context-only",
    "complete",
}
ALLOWED_ARTIFACT_STATE = {
    "none",
    "available-public",
    "mirrored",
    "dead-link",
    "metadata-only",
    "unknown",
}

CATALOG_ID_RE = re.compile(r'^\s*-\s+id:\s*"?([^"\s#]+)"?\s*

def _need_string(obj: dict, key: str, where: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}.{key} must be a non-empty string")
    return value


def _need_string_list(
    obj: dict, key: str, where: str, *, allow_empty: bool = False
) -> list[str]:
    value = obj.get(key)
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ValueError(
            f"{where}.{key} must be {'a' if allow_empty else 'a non-empty'} list"
        )
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{where}.{key} entries must be non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{where}.{key} contains duplicates")
    return value


def catalog_source_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CATALOG_ID_RE.match(line)
        if match:
            ids.add(match.group(1))
    if not ids:
        raise ValueError(f"no source ids found in catalog: {path}")
    return ids


def validate(data: dict, known_source_ids: set[str] | None = None) -> list[dict]:
    if data.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    leads = data.get("leads")
    if not isinstance(leads, list) or not leads:
        raise ValueError("leads must be a non-empty list")

    seen: set[str] = set()
    for index, lead in enumerate(leads):
        where = f"leads[{index}]"
        if not isinstance(lead, dict):
            raise ValueError(f"{where} must be an object")
        lead_id = _need_string(lead, "id", where)
        if lead_id in seen:
            raise ValueError(f"duplicate lead id: {lead_id}")
        seen.add(lead_id)

        value = _need_string(lead, "value", where)
        cost = _need_string(lead, "cost", where)
        status = _need_string(lead, "status", where)
        if value not in ALLOWED_VALUE:
            raise ValueError(f"{where}.value invalid: {value}")
        if cost not in ALLOWED_COST:
            raise ValueError(f"{where}.cost invalid: {cost}")
        if status not in ALLOWED_STATUS:
            raise ValueError(f"{where}.status invalid: {status}")

        source_ids = _need_string_list(lead, "source_ids", where)
        if known_source_ids is not None:
            missing_sources = sorted(set(source_ids) - known_source_ids)
            if missing_sources:
                raise ValueError(
                    f"{where}.source_ids contains unknown catalog id(s): "
                    + ", ".join(missing_sources)
                )
        _need_string(lead, "question", where)
        _need_string(lead, "next_discriminator", where)
        _need_string_list(lead, "deliverables", where)
        _need_string_list(lead, "tags", where, allow_empty=True)

        artifact = lead.get("artifact_need")
        if not isinstance(artifact, dict):
            raise ValueError(f"{where}.artifact_need must be an object")
        _need_string(artifact, "kind", f"{where}.artifact_need")
        state = _need_string(artifact, "state", f"{where}.artifact_need")
        if state not in ALLOWED_ARTIFACT_STATE:
            raise ValueError(f"{where}.artifact_need.state invalid: {state}")
        user_action = artifact.get("user_action_required")
        if not isinstance(user_action, bool):
            raise ValueError(
                f"{where}.artifact_need.user_action_required must be boolean"
            )
        request = artifact.get("request", "")
        if not isinstance(request, str):
            raise ValueError(f"{where}.artifact_need.request must be a string")
        if user_action and not request.strip():
            raise ValueError(
                f"{where}.artifact_need.request required when user action is required"
            )

    return leads


def summarize(leads: list[dict]) -> dict:
    by_status = Counter(lead["status"] for lead in leads)
    by_value = Counter(lead["value"] for lead in leads)
    manual = [
        {
            "id": lead["id"],
            "kind": lead["artifact_need"]["kind"],
            "request": lead["artifact_need"]["request"],
        }
        for lead in leads
        if lead["artifact_need"]["user_action_required"]
    ]
    return {
        "lead_count": len(leads),
        "by_status": dict(sorted(by_status.items())),
        "by_value": dict(sorted(by_value.items())),
        "manual_action_count": len(manual),
        "manual_actions": manual,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("references/evidence-worklist.json"),
    )
    ap.add_argument(
        "--catalog",
        type=Path,
        default=Path("references/catalog.yml"),
        help="source catalog used to verify every worklist source id",
    )
    ap.add_argument("--json", action="store_true", help="print machine-readable summary")
    args = ap.parse_args()

    data = json.loads(args.path.read_text(encoding="utf-8"))
    leads = validate(data, catalog_source_ids(args.catalog))
    summary = summarize(leads)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"External evidence worklist valid: {summary['lead_count']} lead(s)")
        print(
            "Status:",
            ", ".join(f"{k}={v}" for k, v in summary["by_status"].items()),
        )
        print(
            "Value:",
            ", ".join(f"{k}={v}" for k, v in summary["by_value"].items()),
        )
        print(f"Manual user actions: {summary['manual_action_count']}")
        for item in summary["manual_actions"]:
            print(f"  {item['id']}: {item['request']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
)


def _need_string(obj: dict, key: str, where: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}.{key} must be a non-empty string")
    return value


def _need_string_list(
    obj: dict, key: str, where: str, *, allow_empty: bool = False
) -> list[str]:
    value = obj.get(key)
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ValueError(
            f"{where}.{key} must be {'a' if allow_empty else 'a non-empty'} list"
        )
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{where}.{key} entries must be non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{where}.{key} contains duplicates")
    return value


def validate(data: dict) -> list[dict]:
    if data.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    leads = data.get("leads")
    if not isinstance(leads, list) or not leads:
        raise ValueError("leads must be a non-empty list")

    seen: set[str] = set()
    for index, lead in enumerate(leads):
        where = f"leads[{index}]"
        if not isinstance(lead, dict):
            raise ValueError(f"{where} must be an object")
        lead_id = _need_string(lead, "id", where)
        if lead_id in seen:
            raise ValueError(f"duplicate lead id: {lead_id}")
        seen.add(lead_id)

        value = _need_string(lead, "value", where)
        cost = _need_string(lead, "cost", where)
        status = _need_string(lead, "status", where)
        if value not in ALLOWED_VALUE:
            raise ValueError(f"{where}.value invalid: {value}")
        if cost not in ALLOWED_COST:
            raise ValueError(f"{where}.cost invalid: {cost}")
        if status not in ALLOWED_STATUS:
            raise ValueError(f"{where}.status invalid: {status}")

        _need_string_list(lead, "source_ids", where)
        _need_string(lead, "question", where)
        _need_string(lead, "next_discriminator", where)
        _need_string_list(lead, "deliverables", where)
        _need_string_list(lead, "tags", where, allow_empty=True)

        artifact = lead.get("artifact_need")
        if not isinstance(artifact, dict):
            raise ValueError(f"{where}.artifact_need must be an object")
        _need_string(artifact, "kind", f"{where}.artifact_need")
        state = _need_string(artifact, "state", f"{where}.artifact_need")
        if state not in ALLOWED_ARTIFACT_STATE:
            raise ValueError(f"{where}.artifact_need.state invalid: {state}")
        user_action = artifact.get("user_action_required")
        if not isinstance(user_action, bool):
            raise ValueError(
                f"{where}.artifact_need.user_action_required must be boolean"
            )
        request = artifact.get("request", "")
        if not isinstance(request, str):
            raise ValueError(f"{where}.artifact_need.request must be a string")
        if user_action and not request.strip():
            raise ValueError(
                f"{where}.artifact_need.request required when user action is required"
            )

    return leads


def summarize(leads: list[dict]) -> dict:
    by_status = Counter(lead["status"] for lead in leads)
    by_value = Counter(lead["value"] for lead in leads)
    manual = [
        {
            "id": lead["id"],
            "kind": lead["artifact_need"]["kind"],
            "request": lead["artifact_need"]["request"],
        }
        for lead in leads
        if lead["artifact_need"]["user_action_required"]
    ]
    return {
        "lead_count": len(leads),
        "by_status": dict(sorted(by_status.items())),
        "by_value": dict(sorted(by_value.items())),
        "manual_action_count": len(manual),
        "manual_actions": manual,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("references/evidence-worklist.json"),
    )
    ap.add_argument("--json", action="store_true", help="print machine-readable summary")
    args = ap.parse_args()

    data = json.loads(args.path.read_text(encoding="utf-8"))
    leads = validate(data)
    summary = summarize(leads)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"External evidence worklist valid: {summary['lead_count']} lead(s)")
        print(
            "Status:",
            ", ".join(f"{k}={v}" for k, v in summary["by_status"].items()),
        )
        print(
            "Value:",
            ", ".join(f"{k}={v}" for k, v in summary["by_value"].items()),
        )
        print(f"Manual user actions: {summary['manual_action_count']}")
        for item in summary["manual_actions"]:
            print(f"  {item['id']}: {item['request']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
