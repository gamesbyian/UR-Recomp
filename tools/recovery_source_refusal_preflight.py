#!/usr/bin/env python3
"""Offline negative-only preflight for previously refused recovery publication.

Cross-reference a proposed Git blob against *supplied* explicit refusal records.
The records must have been fetched and reviewed separately, including issue
comments: this is not a discovery client, an authorization oracle, or a GitHub
publishing tool. A clear lookup NEVER grants permission to publish.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

SHA40 = re.compile(r"[0-9a-f]{40}\Z")
DRIVE_ID = re.compile(r"[A-Za-z0-9_-]{15,}\Z")
SOURCE_SHA_FIELDS = (
    "source_member_git_blob_sha", "source_git_blob_sha", "proposed_blob_sha", "intended_postimage_blob_sha",
    "postimage_blob_sha", "source_blob_sha", "proposed_git_blob_sha",
)
PATH_FIELDS = ("attempted_target", "target_path", "path")
ARCHIVE_FIELDS = (
    "source_zip_drive_id", "source_archive_drive_id", "drive_archive_id",
    "stage_archive_drive_id", "archive_drive_id", "vault_file_id",
)
DENIAL_CLASSIFICATIONS = frozenset((
    "explicit_safety_refusal", "explicit_safety_denial", "explicit_policy_denial",
    "explicit_tool_safety_refusal", "explicit_policy_refusal",
))


def git_blob(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _denied(incident: dict) -> bool:
    classification = str(incident.get("classification") or incident.get("failure_class") or "")
    label = classification.lower().replace("-", "_")
    if label in DENIAL_CLASSIFICATIONS:
        return True
    return any(word in str(incident.get(key, "")).lower()
               for key in ("raw_error", "original_error", "error")
               for word in ("blocked by openai's safety checks", "explicit safety refusal"))


def _observed_values(incident: dict, fields: tuple[str, ...]) -> set[str]:
    return {incident[k] for k in fields
            if type(incident.get(k)) is str and incident[k]}


def check(candidate: dict, incidents: list[dict]) -> dict:
    """Return negative holds/review hints, *never* positive publication approval."""
    if type(candidate) is not dict or not isinstance(candidate.get("source_blob_sha"), str) \
            or not SHA40.fullmatch(candidate["source_blob_sha"]):
        raise ValueError("candidate requires exact source Git blob SHA")
    path = candidate.get("target_path")
    archive = candidate.get("source_archive_drive_id")
    if (type(path) is not str or not path or path.startswith("/") or
            "\\" in path or any(seg in ("", ".", "..") for seg in path.split("/"))):
        raise ValueError("candidate requires normalized repository-relative path")
    if archive is not None and (type(archive) is not str or not DRIVE_ID.fullmatch(archive)):
        raise ValueError("invalid source archive Drive identity")
    if type(incidents) is not list:
        raise ValueError("incidents must be the explicitly supplied source records")

    matches, related, unknown, seen = [], [], [], set()
    for index, incident in enumerate(incidents):
        if type(incident) is not dict:
            unknown.append({"index": index, "reason": "nonobject incident"})
            continue
        identity = incident.get("incident_id")
        if type(identity) is not str or not identity or identity in seen:
            unknown.append({"index": index, "reason": "missing or duplicate incident identity"})
            continue
        seen.add(identity)
        if not _denied(incident):
            continue
        operation = incident.get("original_operation")
        operation = operation if type(operation) is dict else {}
        paths = _observed_values(incident, PATH_FIELDS) | _observed_values(operation, ("path",))
        blobs = _observed_values(incident, SOURCE_SHA_FIELDS)
        if type(operation.get("content")) is str:
            blobs.add(git_blob(operation["content"]))
        archive_ids = _observed_values(incident, ARCHIVE_FIELDS)
        reasons = []
        if candidate["source_blob_sha"] in blobs:
            reasons.append("identical refused source bytes")
        if path in paths:
            reasons.append("identical refused target path")
        record = {"incident_id": identity, "reasons": reasons}
        if reasons:
            matches.append(record)
        elif archive is not None and archive in archive_ids:
            related.append({"incident_id": identity, "reason": "shared archive, member not established"})
        elif not blobs and not paths and not archive_ids:
            unknown.append({"index": index, "reason": "denial without source/path/archive locator"})

    decision = ("HOLD_KNOWN_REFUSAL" if matches else
                "REVIEW_INCOMPLETE_RECORDS" if unknown else
                "REVIEW_SHARED_ARCHIVE" if related else
                "NO_MATCH_NONEXHAUSTIVE")
    return {"schema": "ur-recovery-source-refusal-preflight/1",
            "decision": decision, "incidents_checked": len(incidents),
            "exact_refusal_matches": matches, "shared_archive_reviews": related,
            "incomplete_incidents": unknown,
            "manual_source_and_incident_review_required": True,
            "automatic_publication_authorized": False,
            "release_gate_credit": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True,
                        help="JSON object with source_blob_sha, target_path, optional source_archive_drive_id")
    parser.add_argument("--incidents", type=Path, required=True,
                        help="JSON array of independently downloaded explicit incident records")
    args = parser.parse_args()
    result = check(json.loads(args.candidate.read_text(encoding="utf-8")),
                   json.loads(args.incidents.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True, indent=2))
    if result["decision"] != "NO_MATCH_NONEXHAUSTIVE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
