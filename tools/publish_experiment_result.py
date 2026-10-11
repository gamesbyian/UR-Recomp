#!/usr/bin/env python3
"""Publish one bounded experimental result with exact source/input identity.

This is a transport/provenance receipt, NOT an original-game QA verdict.
Promotion of a useful finding into the repo remains a reviewed commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def file_identity(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing, nonregular or symlinked experiment input: {path}")
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw)}


def publish(*, name: str, question: str, result: Path, inputs: list[Path],
            summary_md: Path | None, metadata: dict) -> tuple[dict, str]:
    if not name.strip() or not question.strip():
        raise ValueError("experiment name and question must be nonempty")
    all_paths = [result, *inputs, *([summary_md] if summary_md else [])]
    canonical = [p.resolve() for p in all_paths]
    if len(set(canonical)) != len(canonical):
        raise ValueError("duplicate experiment file role/path")
    result_id = file_identity(result)
    try:
        primary = json.loads(result.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"primary result is not valid JSON: {exc}") from exc
    if not isinstance(primary, dict):
        raise ValueError("primary result must be a JSON object")
    input_ids = [file_identity(p) for p in inputs]
    summary_id = file_identity(summary_md) if summary_md else None
    status = "produced_not_adjudicated"
    manifest = {
        "schema": "UR-EXPERIMENT-RESULT/1",
        "authority": "diagnostic/research; not a release gate",
        "name": name, "question": question,
        "status": status,
        "conclusion": "not_adjudicated",
        "source": metadata,
        "primary": result_id,
        "inputs": input_ids,
        "source_summary": summary_id,
        "integrity": {"input_count": len(inputs), "all_expected_files_present": True},
    }
    md = [f"### Experiment: {name}",
          f"**Question:** {question}",
          f"**Run:** {metadata.get('GITHUB_RUN_ID') or 'local'} | "
          f"**Commit:** {metadata.get('GITHUB_SHA') or 'unspecified'}",
          f"**Evidence:** {status}; scientific conclusion not automatically inferred.",
          f"**Primary result SHA-256:** {result_id['sha256']}",
          f"**Inputs:** {len(input_ids)} file(s) with recorded SHA-256/size.",
          ""]
    if summary_md:
        narrative = summary_md.read_text(encoding="utf-8")
        md.append(narrative[:10000])
        if len(narrative) > 10000:
            md.append("\nFull result summary is in the artifact; display truncated at 10,000 characters.")
    else:
        md.append("No domain summary supplied; inspect the primary JSON result.")
    md.append("\nRetain the result + manifest as one artifact. Commit decision-bearing findings into the existing research ledger and compact analysis/data evidence after review, never by an automatic CI push.\n")
    return manifest, "\n".join(md)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--result", required=True, type=Path)
    p.add_argument("--input", action="append", type=Path, default=[])
    p.add_argument("--source-summary", type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--github-summary", type=Path)
    args = p.parse_args()
    if args.out.resolve() in {x.resolve() for x in [args.result, *args.input, *([args.source_summary] if args.source_summary else [])]}:
        p.error("output must not overwrite any evidence file")
    env_keys = ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA",
                "GITHUB_WORKFLOW", "GITHUB_EVENT_NAME", "GITHUB_HEAD_REF")
    metadata = {key: os.environ.get(key, "") for key in env_keys}
    event = os.environ.get("GITHUB_EVENT_PATH")
    if event and Path(event).is_file():
        metadata["github_event_sha256"] = hashlib.sha256(Path(event).read_bytes()).hexdigest()
    try:
        manifest, summary = publish(name=args.name, question=args.question,
                                    result=args.result, inputs=args.input,
                                    summary_md=args.source_summary, metadata=metadata)
    except ValueError as exc:
        p.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if args.github_summary:
        with args.github_summary.open("a", encoding="utf-8") as stream:
            stream.write(summary)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
