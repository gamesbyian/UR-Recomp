#!/usr/bin/env python3
"""Read-only, fail-closed consumer of durable Vault intake artifacts.

A blob mismatch is a review lead, NEVER authorization to publish or evidence
of an absent behavior. The human-maintained recovery register owns dispositions.
This program neither downloads source nor mutates GitHub or Drive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ID = re.compile(r"[A-Za-z0-9_-]{10,128}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
CHECKPOINT = "ur-vault-recurring-checkpoint/1"
QUEUE = "ur-vault-integration-candidates/1"
REGISTRY = "ur-recovery-registry/1"
LEDGER = "ur-vault-member-dispositions/1"
VALID_STATES = {"merged", "superseded", "held", "engineering", "evidence_only",
                "unresolved", "rejected"}
# The five scheduled generalists select work from the same ranked board.
# Live conflicting writes and independent review still govern eligibility.
SHARED_POOL = "shared_ranked_pool"
SOURCE_SCOPES = ("incoming", "evidence")
SOURCE_FILES = ("checkpoint.json", "queue.json", "report.json")


def source_run_receipts(path: Path, roots: dict[str, Path]) -> dict:
    """Identify exact restored intake bytes and their selected Actions runs.

    The download loop supplies these run IDs. Local content hashes are not
    remote artifact authentication, source publication or release evidence.
    """
    by_scope = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"(incoming|evidence) source run: ([1-9][0-9]{0,14})", line)
        if not match:
            raise ValueError("invalid Vault source-run receipt line")
        scope, run_id = match.groups()
        if scope in by_scope:
            raise ValueError("duplicate Vault source-run scope")
        if scope not in roots:
            raise ValueError("unavailable Vault source-run scope")
        hashes = {name: hashlib.sha256((roots[scope] / name).read_bytes()).hexdigest()
                  for name in SOURCE_FILES}
        by_scope[scope] = {
            "source_run_id": int(run_id),
            "source_run_url": f"https://github.com/gamesbyian/UR-Recomp/actions/runs/{run_id}",
            "input_sha256": hashes,
        }
    if set(by_scope) != set(SOURCE_SCOPES):
        raise ValueError("missing Incoming or Evidence Vault source-run receipt")
    return {scope: by_scope[scope] for scope in SOURCE_SCOPES}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def member_key(scope: str, file_id: str, archive: str, member: str, digest: str) -> str:
    raw = json.dumps([scope, file_id, archive, member, digest],
                     separators=(",", ":"), ensure_ascii=True)
    return "vm1-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def validate_artifacts(scope: str, root: Path):
    """Input must be a complete, consistent, named folder artifact."""
    if not root.is_dir():
        raise ValueError(f"missing {scope} artifact directory")
    ck, queue, report = (load(root / filename) for filename in
                         ("checkpoint.json", "queue.json", "report.json"))
    if ck.get("schema") != CHECKPOINT or queue.get("schema") != QUEUE:
        raise ValueError(f"{scope}: incompatible checkpoint/queue")
    if report.get("schema") != "ur-vault-recurring-intake/1":
        raise ValueError(f"{scope}: incompatible report")
    if not isinstance(ck.get("items"), dict) or not isinstance(queue.get("needs_engineering_review"), list):
        raise ValueError(f"{scope}: malformed artifact")
    if scope == "incoming" and "1cdovDqle9IRYKX2lCt513mtWge75HywX" not in report.get("folder", ""):
        raise ValueError("incoming artifact has wrong source folder")
    if scope == "evidence" and "1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2" not in report.get("folder", ""):
        raise ValueError("evidence artifact has wrong source folder")
    for fid, item in ck["items"].items():
        if not ID.fullmatch(fid) or not isinstance(item, dict) or not SHA.fullmatch(str(item.get("sha256", ""))):
            raise ValueError(f"{scope}: malformed verified item")
        for lead in item.get("review_leads", []):
            if (not isinstance(lead, dict) or lead.get("status") != "unmatched_needs_review"
                    or not SHA.fullmatch(str(lead.get("sha256", "")))
                    or lead.get("kind") not in ("patch", "source_or_test")
                    or not isinstance(lead.get("member"), str)
                    or len(lead["member"]) > 512
                    or not isinstance(lead.get("bytes"), int)):
                raise ValueError(f"{scope}: malformed member fingerprint")
    for lead in queue["needs_engineering_review"]:
        fid = lead.get("id")
        if fid not in ck["items"] or lead.get("sha256") != ck["items"][fid]["sha256"]:
            raise ValueError(f"{scope}: stale or mixed queue/checkpoint")
    return ck, queue, report


def read_registry(path: Path):
    data = load(path)
    if data.get("schema") != REGISTRY or not isinstance(data.get("candidates"), list):
        raise ValueError("invalid historical recovery register")
    result = {}
    for row in data["candidates"]:
        fid = row.get("drive_id")
        if fid:
            result.setdefault(fid, []).append(row)
    return result


def read_ledger(path: Path):
    if not path.exists():
        raise ValueError("authoritative member ledger missing; refusing guessed dispositions")
    data = load(path)
    if data.get("schema") != LEDGER or not isinstance(data.get("items"), list):
        raise ValueError("invalid member disposition ledger")
    result = {}
    for item in data["items"]:
        key = item.get("candidate_id")
        if (not isinstance(key, str) or not re.fullmatch(r"vm1-[0-9a-f]{24}", key)
                or key in result or item.get("state") not in VALID_STATES):
            raise ValueError("invalid or duplicate ledger record")
        result[key] = item
    return result


def read_github(path: Path):
    data = load(path)
    if not isinstance(data.get("prs"), list):
        raise ValueError("GitHub PR snapshot unavailable")
    by_number = {}
    for row in data["prs"]:
        if not isinstance(row.get("number"), int):
            raise ValueError("invalid PR number")
        by_number[row["number"]] = row
    return by_number


def classify(candidate, record, archive_records, prs):
    fid = candidate["drive_id"]
    key = candidate["candidate_id"]
    matches = [p for p in prs.values() if not p.get("merged_at") and p.get("state") == "OPEN"
               and (key in str(p.get("body") or "") or
                    ("vault-member-sha256:" + candidate["member_sha256"]) in str(p.get("body") or ""))]
    if len(matches) > 1:
        return "duplicate_pr_collision", "Several active PRs claim identical source", SHARED_POOL, matches
    if record:
        # A human disposition cannot claim a different retained archive under
        # a valid-looking member key. Require every stated identity field to
        # agree with the independently checkpointed member.
        identity = {
            "scope": candidate["scope"],
            "drive_id": candidate["drive_id"],
            "archive_sha256": candidate["archive_sha256"],
            "member": candidate["member"],
            "member_sha256": candidate["member_sha256"],
        }
        for field, expected in identity.items():
            if field in record and record[field] != expected:
                return ("identity_conflict",
                        "Ledger " + field + " contradicts verified checkpoint fingerprint",
                        SHARED_POOL, matches)
        state = record["state"]
        reason = str(record.get("reason") or "").strip()
        if state in {"held", "rejected"}:
            if not reason:
                return "unresolved", "Hold has no recorded reason", SHARED_POOL, matches
            return "held", reason, SHARED_POOL, matches
        if state == "merged":
            pr = prs.get(record.get("pr"))
            if (pr and pr.get("merged_at") and pr.get("merge_commit_sha")
                    and pr["merge_commit_sha"] == record.get("merge_commit")
                    and record.get("tests") and record.get("source_path")
                    and record.get("evidence")
                    and record.get("archive_sha256") == candidate["archive_sha256"]
                    and record.get("member_sha256") == candidate["member_sha256"]):
                return "merged", "Exact member linked to verified merged PR and tests", SHARED_POOL, matches
            return "merge_unverified", "Reverify PR, merge SHA, archive/member hashes, provenance, source path and tests", SHARED_POOL, matches
        if state == "superseded":
            if record.get("source_path") and record.get("evidence") and record.get("tests"):
                return "superseded", reason or "Per-member semantic evidence recorded", SHARED_POOL, matches
            return "unresolved", "Supersession lacks source/test evidence", SHARED_POOL, matches
        if state == "evidence_only":
            return "evidence_only", reason or "Non-adoptable retained evidence", SHARED_POOL, matches
        if state == "engineering":
            if matches:
                return "open_pr", "Review existing PR at its current head", SHARED_POOL, matches
            if (record.get("provenance_verified") is True and record.get("publication_authorized") is True
                    and record.get("source_path") and record.get("reason")):
                return "queued_engineering", reason, SHARED_POOL, matches
            return "unresolved", "Engineering route missing provenance, destination or authorization", SHARED_POOL, matches
        return "unresolved", reason or "Pending semantic classification", SHARED_POOL, matches
    if matches:
        return "open_pr_unverified", "Existing PR claims member; verify provenance and disposition", SHARED_POOL, matches
    if any(a.get("state") == "blocked" for a in archive_records):
        return "held", "Historical archive-level block; per-member review required", SHARED_POOL, matches
    return "needs_semantic_review", "Unmatched blob; semantic comparison and publication review required", SHARED_POOL, matches


def assemble(incoming: Path, evidence: Path, registry: Path, ledger: Path,
             github: Path):
    archives = read_registry(registry)
    decisions = read_ledger(ledger)
    prs = read_github(github)
    records, status, errors, seen = [], {}, [], set()
    for scope, root in (("incoming", incoming), ("evidence", evidence)):
        checkpoint, queue, report = validate_artifacts(scope, root)
        scope_status = {"scope": scope, "run_time": report.get("scanned_at"),
                        "verified": len(checkpoint["items"]), "processed": len(report.get("processed", [])),
                        "errors": len(report.get("errors", [])),
                        "remaining_due": report.get("remaining_due"),
                        "cooldowns": len(queue.get("retry_cooldown", []))}
        status[scope] = scope_status
        for error in report.get("errors", []):
            errors.append({"scope": scope, "drive_id": error.get("id"),
                           "type": "inspection_failure"})
        for cooling in queue.get("retry_cooldown", []):
            errors.append({"scope": scope, "drive_id": cooling.get("id"),
                           "type": "retry_cooldown", "retry_after": cooling.get("retry_after")})
        for pending in queue.get("needs_first_audit", []):
            if pending.get("id") not in checkpoint["items"]:
                errors.append({"scope": scope, "drive_id": pending.get("id"),
                               "type": "awaiting_first_archive_audit"})
        missing_listing = set(report.get("absent_from_current_listing", []))
        for fid in sorted(missing_listing):
            errors.append({"scope": scope, "drive_id": fid,
                           "type": "absent_from_current_public_listing"})
        for fid, item in sorted(checkpoint["items"].items()):
            if item.get("review_leads_filtered_or_truncated", 0):
                errors.append({"scope": scope, "drive_id": fid,
                               "type": "unrepresented_member_leads",
                               "count": item["review_leads_filtered_or_truncated"]})
            for lead in item.get("review_leads", []):
                key = member_key(scope, fid, item["sha256"], lead["member"], lead["sha256"])
                seen.add(key)
                c = {"candidate_id": key, "scope": scope, "drive_id": fid,
                     "archive_sha256": item["sha256"], "member": lead["member"],
                     "member_sha256": lead["sha256"], "member_bytes": lead["bytes"],
                     "kind": lead["kind"],
                     "source": "https://drive.google.com/file/d/" + fid + "/view"}
                state, reason, owner, claims = classify(c, decisions.get(key), archives.get(fid, []), prs)
                c.update({"state": state, "reason": reason, "owner": owner,
                          "prs": [p["number"] for p in claims],
                          "related_registry": [r.get("candidate_id") for r in archives.get(fid, [])]})
                if fid in missing_listing:
                    c["source_currently_listed"] = False
                    if c["state"] in ("queued_engineering", "open_pr"):
                        c["state"] = "unavailable_source_hold"
                        c["reason"] = "Previously verified source absent from latest listing; reverify original"
                        c["owner"] = SHARED_POOL
                else:
                    c["source_currently_listed"] = True
                if key in decisions:
                    c["disposition"] = decisions[key]
                records.append(c)
        # Legacy checkpoints may not yet expose member fingerprint metadata.
        for lead in queue["needs_engineering_review"]:
            item = checkpoint["items"][lead["id"]]
            if (item.get("unmatched_or_unexamined", 0) > 0 and
                    not item.get("review_leads")):
                errors.append({"scope": scope, "drive_id": lead["id"],
                               "type": "unfingerprinted_legacy_review_lead"})
    # Identical content across separate archive IDs is one exact-byte review
    # candidate, not multiple engineering assignments. Retain every source ID.
    canonical = {}
    for row in sorted(records, key=lambda c: c["candidate_id"]):
        fingerprint = row["member_sha256"]
        original = canonical.get(fingerprint)
        if original and row["state"] in ("needs_semantic_review", "queued_engineering"):
            row["state"] = "duplicate_review_lead"
            row["owner"] = SHARED_POOL
            row["reason"] = "Exact member SHA-256 already tracked as " + original
            row["duplicate_of"] = original
        else:
            canonical.setdefault(fingerprint, row["candidate_id"])
    # Stage preparation is an inert manifest, limited to two authorized
    # engineering leads. It cannot self-assert the human rights checkbox.
    folder_urls = {
        "incoming": "https://drive.google.com/drive/folders/1cdovDqle9IRYKX2lCt513mtWge75HywX",
        "evidence": "https://drive.google.com/drive/folders/1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2",
    }
    staging = []
    for c in sorted(records, key=lambda row: row["candidate_id"]):
        if c["state"] != "queued_engineering" or len(staging) == 2:
            continue
        staging.append({
            "candidate_id": c["candidate_id"], "owner": SHARED_POOL,
            "drive_file_id": c["drive_id"], "folder_url": folder_urls[c["scope"]],
            "archive_sha256": c["archive_sha256"],
            "expected_archive_sha256": c["archive_sha256"],
            "member": c["member"],
            "stage_member": c["member"],
            "member_sha256": c["member_sha256"],
            "stage_member_sha256": c["member_sha256"],
            "source_destination": c["disposition"]["source_path"],
            "manual_workflow": "https://github.com/gamesbyian/UR-Recomp/actions/workflows/vault-direct-intake.yml",
            "download_all": False, "stage_sources": True,
            "entire_archive_review_required": False,
            "source_member_review_required": True,
            "staging_may_include_other_unmatched_source_members": False,
            "confirm_source_review": "verify_selected_member_rights_and_archive_publication_holds",
            "dispatch_automatically": False,
        })
    orphan = sorted(set(decisions) - seen)
    counts = {name: sum(c["state"] == name for c in records)
              for name in sorted({c["state"] for c in records})}
    return {"schema": "ur-vault-actionable-review/1", "status": status,
            "counts": counts, "records": records, "staging_handoff": staging,
            "exceptions": errors,
            "dispositions_not_in_current_artifacts": orphan,
            "automatic_publication_authorized": False,
            "automatic_merges": 0, "source_bytes_published": 0}


def render(doc, max_rows=35):
    lines = ["# Vault actionable review", "",
             "Metadata only. **No source staged, PR opened or release gate credited.**",
             "Review leads are *not* evidence of missing functionality.", ""]
    for s in doc["status"].values():
        lines.append(f"- {s['scope']}: {s['verified']} verified in checkpoint, "
                     f"{s['processed']} inspected this run, {s['errors']} errors; "
                     f"{s['remaining_due']} due")
    if doc.get("source_artifacts"):
        lines += ["", "## Exact intake input ancestry", ""]
        for scope, source in doc["source_artifacts"].items():
            lines.append(f"- {scope}: {source['source_run_url']}; "
                         + "; ".join(f"{name} sha256 {digest}"
                                     for name, digest in source["input_sha256"].items()))
        lines.append("Locally hashed restored bytes; not independent remote attestation.")
    lines += ["", "## Per-member disposition", ""]
    for k, v in doc["counts"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Bounded actionable candidates", ""]
    priority = {"identity_conflict": 0, "duplicate_pr_collision": 0,
                "merge_unverified": 1,
                "open_pr": 2, "queued_engineering": 3,
                "open_pr_unverified": 4, "needs_semantic_review": 5,
                "unresolved": 6, "held": 7}
    actionable = sorted(doc["records"], key=lambda c: (priority.get(c["state"], 9),
                                                          c["candidate_id"]))
    for c in actionable[:max_rows]:
        path = c["member"].replace("|", "/").replace("\n", " ")
        prs = ", ".join(
            f"https://github.com/gamesbyian/UR-Recomp/pull/{n} "
            f"(checks: https://github.com/gamesbyian/UR-Recomp/pull/{n}/checks)"
            for n in c["prs"])
        lines.append(f"- \`{c['candidate_id']}\` **{c['state']}** "
                     f"[Drive {c['drive_id']}]({c['source']}) "
                     f"\`{path[:100]}\` sha256 \`{c['member_sha256'][:16]}\` "
                     f"| owner: {c['owner']} | {c['reason'][:140]}"
                     + (f" | {prs}" if prs else ""))
    if len(actionable) > max_rows:
        lines.append(f"- {len(actionable) - max_rows} further members in JSON artifact.")
    lines += ["", f"Manual, reviewed staging handoffs: {len(doc['staging_handoff'])} (max 2)"]
    for handoff in doc["staging_handoff"]:
        lines.append(f"- {handoff['candidate_id']}: {handoff['manual_workflow']} "
                     f"| Drive ID {handoff['drive_file_id']} "
                     f"| member {handoff['stage_member'][:100]} "
                     f"| SHA-256 {handoff['stage_member_sha256']} "
                     f"| selected-source rights confirmation required")
    lines += ["", f"Unresolved intake/cooldown/legacy exceptions: {len(doc['exceptions'])}",
              f"Older ledger IDs absent from available checkpoint fingerprints: "
              f"{len(doc['dispositions_not_in_current_artifacts'])}. Preserve them; do not delete.",
              "", "Coordinate in https://github.com/gamesbyian/UR-Recomp/issues/2468; "
                  "original disposition evidence in issue #2088."]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--incoming", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--registry", type=Path, default=Path("docs/recovery/agent-candidates.json"))
    p.add_argument("--ledger", type=Path, default=Path("docs/recovery/vault-member-dispositions.json"))
    p.add_argument("--github", type=Path, required=True)
    p.add_argument("--sources", type=Path, help="per-folder Actions run IDs from intake restoration")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    doc = assemble(args.incoming, args.evidence, args.registry, args.ledger, args.github)
    if args.sources is not None:
        doc["source_artifacts"] = source_run_receipts(
            args.sources, {"incoming": args.incoming, "evidence": args.evidence})
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "actionable.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    (args.out / "actionable.md").write_text(render(doc))
    print(render(doc, max_rows=12))


if __name__ == "__main__":
    main()
