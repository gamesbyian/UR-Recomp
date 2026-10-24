#!/usr/bin/env python3
"""Direct, read-only public Google Drive Vault intake via gdown v6.

No GitHub writes, Drive moves, automatic merge, release credit, or automatic
permission to publish. Only selected, ordinary text source is stageable.
The staged directory is intended for a *separately reviewed* handoff artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from urllib.parse import parse_qs, urlsplit
from zipfile import ZipFile

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from recovery_member_blob_crosswalk import crosswalk
from strict_vault_manifest import _portable_win32_component

DEFAULT_FOLDER = "https://drive.google.com/drive/folders/1cdovDqle9IRYKX2lCt513mtWge75HywX"
ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{15,}\Z")
SOURCE_EXTENSIONS = frozenset({
    ".py", ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp",
    ".rs", ".js", ".ts", ".tsx", ".sh", ".ps1", ".yml", ".yaml",
    ".cmake", ".patch", ".diff", ".toml",
})
DENIED_COMPONENTS = frozenset({
    ".git", ".ssh", ".aws", ".github", "secrets", "credentials",
    "rom", "roms", "media", "capture", "captures", "original", "reference",
    "__pycache__", "node_modules",
})
MAX_FILES = 500
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_SESSION_BYTES = 128 * 1024 * 1024
MAX_SOURCE_BYTES = 1 * 1024 * 1024
MAX_STAGED_BYTES = 16 * 1024 * 1024
MAX_REVIEW_LEADS = 256


def drive_id(url: str) -> str:
    """Accept only ordinary Drive file URLs, not arbitrary network destinations."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "drive.google.com":
        raise ValueError("download URL must use https://drive.google.com")
    match = re.search(r"/file/d/([A-Za-z0-9_-]+)(?:/|$)", parsed.path)
    raw_id = (match.group(1) if match else
              parse_qs(parsed.query).get("id", [None])[0])
    if not raw_id or not ID_PATTERN.fullmatch(raw_id):
        raise ValueError("missing or invalid Drive file ID")
    return raw_id


def safe_path(value: str) -> Path:
    if (not isinstance(value, str) or not value or value.startswith("/")
            or "\\" in value or "\x00" in value
            or unicodedata.normalize("NFC", value) != value):
        raise ValueError("unsafe file path")
    parts = value.split("/")
    if (any(part in ("", ".", "..") or
            not _portable_win32_component(part) for part in parts)
            or len(value) > 1024):
        raise ValueError("nonportable file path")
    return Path(*parts)


def list_public_folder(folder_url: str, *, runner=subprocess.run) -> list[dict]:
    parsed = urlsplit(folder_url)
    if (parsed.scheme != "https" or parsed.netloc != "drive.google.com"
            or not re.fullmatch(r"/drive/folders/[A-Za-z0-9_-]{15,}/?", parsed.path)):
        raise ValueError("expected a canonical Drive folder URL")
    completed = runner(["gdown", folder_url, "--json", "--quiet", "--no-cookies"],
                       capture_output=True, text=True, check=True, timeout=180)
    payload = json.loads(completed.stdout)
    if not isinstance(payload, list) or len(payload) > MAX_FILES:
        raise ValueError("invalid or oversized folder listing")
    seen_ids, seen_paths, entries = set(), set(), []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("invalid folder entry")
        file_id = drive_id(item.get("url", ""))
        path = safe_path(item.get("path", "")).as_posix()
        folded = path.casefold()
        if file_id in seen_ids or folded in seen_paths:
            raise ValueError("duplicate Drive ID or portable path collision")
        seen_ids.add(file_id)
        seen_paths.add(folded)
        entries.append({"id": file_id, "path": path, "url": item["url"]})
    return sorted(entries, key=lambda entry: (entry["path"], entry["id"]))


def safe_source_member(path: str, length: int) -> bool:
    try:
        parts = safe_path(path).parts
    except ValueError:
        return False
    return (
        0 <= length <= MAX_SOURCE_BYTES
        and Path(path).suffix.lower() in SOURCE_EXTENSIONS
        and not any(part.lower() in DENIED_COMPONENTS for part in parts)
        and not any(part.lower().startswith((".env", "private", "secret"))
                    for part in parts)
    )


def scan_zip(raw: bytes, tree: bytes, *, stage_root: Path | None = None) -> dict:
    """Reuse the repo's safety and exact-Git-blob inventory, then hash members."""
    analysis = crosswalk(raw, tree, max_depth=2)
    exact_members = {
        member["member"] for member in analysis["items"]
        if member.get("status") == "exact_git_blob_observed"
    }
    items, staged_count, staged_bytes = [], 0, 0
    with ZipFile(__import__("io").BytesIO(raw)) as archive:
        for info in archive.infolist():
            payload = archive.read(info)
            name = info.filename
            is_source = safe_source_member(name, len(payload))
            matching_main = name in exact_members
            staged = bool(stage_root and is_source and not matching_main)
            if staged:
                staged_bytes += len(payload)
                if staged_bytes > MAX_STAGED_BYTES:
                    raise ValueError("stage exceeds source byte budget")
                destination = stage_root / safe_path(name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    raise ValueError("duplicate stage destination")
                destination.write_bytes(payload)
                staged_count += 1
            items.append({
                "member": name, "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "source_like": is_source, "exact_on_main": matching_main,
                "staged": staged,
            })
    # Retain a bounded metadata-only handoff for unmatched first-party-looking
    # source. Never serialize raw source, denied/private paths or ZIP bytes.
    review_leads, omitted = [], 0
    for observed in analysis["items"]:
        if observed.get("status") != "unmatched_needs_review":
            continue
        member = observed["member"]
        leaf = member.rsplit("!/", 1)[-1]
        # The ancestor archive path must also be eligible for public metadata.
        components = member.replace("!/", "/").split("/")
        if (len(member) > 512 or
                any(part.lower() in DENIED_COMPONENTS or
                    part.lower().startswith((".env", "private", "secret"))
                    for part in components) or
                not safe_source_member(leaf, observed["bytes"])):
            omitted += 1
            continue
        review_leads.append({
            "member": member, "sha256": observed["member_sha256"],
            "bytes": observed["bytes"], "kind": observed["kind"],
            "status": "unmatched_needs_review",
        })
    review_leads.sort(key=lambda lead: (lead["kind"] == "patch",
                                        lead["member"].casefold(), lead["sha256"]))
    omitted += max(0, len(review_leads) - MAX_REVIEW_LEADS)
    review_leads = review_leads[:MAX_REVIEW_LEADS]
    return {
        "archive": analysis["outer_sha256"],
        "crosswalk": {
            key: analysis[key] for key in (
                "source_like_members", "exact_blob_occurrences",
                "unmatched_or_unexamined", "nested_archives_encountered",
            )
        },
        "members": items,
        "review_leads": review_leads,
        "review_leads_filtered_or_truncated": omitted,
        "staged_sources": staged_count,
        "staged_bytes": staged_bytes,
        "rights_and_publication_review_required": True,
    }


def pull(entry: dict, output: Path, tree: bytes, *, stage=False,
         runner=subprocess.run) -> dict:
    file_id = entry["id"]
    name = safe_path(entry["path"]).name
    dest = output / "downloads" / file_id / name
    dest.parent.mkdir(parents=True, exist_ok=False)
    runner(["gdown", entry["url"], "-O", str(dest), "--quiet", "--no-cookies",
            "--timeout", "120"], check=True, capture_output=True, text=True, timeout=600)
    size = dest.stat().st_size
    if size > MAX_ARCHIVE_BYTES:
        dest.unlink()
        raise ValueError("download exceeds single-file byte budget")
    raw = dest.read_bytes()
    result = {
        "id": file_id, "path": entry["path"], "bytes": size,
        "sha256": hashlib.sha256(raw).hexdigest(), "zip": None,
        "published": False, "integrated": False,
    }
    if name.lower().endswith(".zip"):
        result["zip"] = scan_zip(
            raw, tree, stage_root=(output / "staged" / file_id if stage else None)
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder-url", default=DEFAULT_FOLDER)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--file-id", action="append", default=[])
    parser.add_argument("--download-all", action="store_true")
    parser.add_argument("--stage-sources", action="store_true")
    args = parser.parse_args()
    if args.download_all and args.file_id:
        parser.error("choose --download-all or particular --file-id values")
    if args.stage_sources and (args.download_all or len(args.file_id) != 1):
        parser.error("--stage-sources requires exactly one explicit --file-id")
    if any(not ID_PATTERN.fullmatch(item) for item in args.file_id):
        parser.error("invalid Drive file ID")
    if args.out.exists():
        parser.error("output directory must not exist")
    args.out.mkdir(parents=True)
    entries = list_public_folder(args.folder_url)
    selected = set(args.file_id)
    missing = selected - {e["id"] for e in entries}
    if missing:
        parser.error("requested IDs not found in public folder: " + ", ".join(sorted(missing)))
    wanted = entries if args.download_all else [e for e in entries if e["id"] in selected]
    tree = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "HEAD"], check=True, stdout=subprocess.PIPE
    ).stdout
    report = {
        "schema": "ur-direct-drive-intake/1", "folder": args.folder_url,
        "listed_files": len(entries), "listing_complete_independently_verified": False,
        "files": entries, "downloads": [], "errors": [],
        "automatic_publication_authorized": False,
        "archive_deletion_authorized": False, "release_gate_credit": 0,
    }
    total = 0
    for entry in wanted:
        try:
            result = pull(entry, args.out, tree, stage=args.stage_sources)
            total += result["bytes"]
            if total > MAX_SESSION_BYTES:
                raise ValueError("session byte budget exceeded")
            report["downloads"].append(result)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            report["errors"].append({"id": entry["id"], "error": str(exc)[:320]})
    (args.out / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(f"Listed {len(entries)}; downloaded {len(report['downloads'])}; "
          f"errors {len(report['errors'])}; staged={args.stage_sources}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
