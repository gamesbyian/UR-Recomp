#!/usr/bin/env python3
"""Compare Mesen CDL execution for two deterministic UR-Recomp fixtures.

This is intentionally a bounded discovery aid, not a new coverage metric.
It answers one question: which ROM bytes were executed/data-read in one
controlled fixture but not the other?
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools" / "run_fixture_mesen.py"
DEFAULT_MESEN_REPO = ROOT / ".tools" / "src" / "mesen-for-ai"


class MesenRpc:
    """Small stdio MCP client for the pinned mesen-for-ai daemon."""

    def __init__(self, repo: Path):
        self.repo = repo
        self.process: subprocess.Popen[str] | None = None
        self.next_id = 0
        self.session: str | None = None

    def __enter__(self):
        daemon = self.repo / "src" / "mesen_mcp" / "daemon.py"
        if not daemon.is_file():
            raise FileNotFoundError(
                f"mesen-for-ai daemon not found at {daemon}; "
                "run bootstrap_toolchain.py --tool mesen-for-ai"
            )
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.repo / "src")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "mesen_mcp.daemon"],
            cwd=self.repo,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "ur-recomp-cdl-trial", "version": "1"},
            },
        )
        return self

    def __exit__(self, *_):
        if self.process is None:
            return
        try:
            if self.session is not None:
                try:
                    self.tool("session.shutdown")
                except Exception:
                    pass
            if self.process.stdin:
                self.process.stdin.close()
            self.process.wait(timeout=30)
        except Exception:
            self.process.kill()
        finally:
            self.process = None
            self.session = None

    def _request(self, method: str, params: dict | None = None) -> dict:
        if self.process is None or self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("Mesen RPC client is not running")
        self.next_id += 1
        request_id = self.next_id
        self.process.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": method,
                    "params": params or {},
                }
            )
            + "\n"
        )
        self.process.stdin.flush()
        while True:
            line = self.process.stdout.readline()
            if not line:
                stderr = self.process.stderr.read() if self.process.stderr else ""
                raise RuntimeError(f"mesen-mcpd closed unexpectedly: {stderr}")
            message = json.loads(line)
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message

    def tool(self, name: str, **arguments):
        if self.session is not None and "session" not in arguments and name != "session.load_rom":
            arguments["session"] = self.session
        message = self._request("tools/call", {"name": name, "arguments": arguments})
        result = message["result"]
        content = result.get("content") or []
        payload = content[0].get("text", "") if content else ""
        parsed = json.loads(payload) if payload.strip().startswith(("{", "[")) else payload
        if result.get("isError"):
            raise RuntimeError(f"{name}: {parsed}")
        if name == "session.shutdown":
            self.session = None
        return parsed

    def load_rom(self, rom: str, **kwargs):
        result = self.tool("session.load_rom", rom=rom, **kwargs)
        self.session = result["session"]
        return result


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def ranges(indices: list[int]) -> list[tuple[int, int]]:
    if not indices:
        return []
    out: list[tuple[int, int]] = []
    start = prev = indices[0]
    for value in indices[1:]:
        if value == prev + 1:
            prev = value
            continue
        out.append((start, prev))
        start = prev = value
    out.append((start, prev))
    return out


def lorom_cpu_address(offset: int) -> str:
    """Map a canonical 2 MiB LoROM file offset to its low-bank CPU mirror."""
    if offset < 0:
        raise ValueError("negative ROM offset")
    bank = offset // 0x8000
    if bank > 0x7F:
        raise ValueError(f"ROM offset outside LoROM bank range: 0x{offset:X}")
    address = 0x8000 + (offset % 0x8000)
    return f"{bank:02X}:{address:04X}"


def classify_bytes(entries: list[dict]) -> tuple[set[int], set[int]]:
    code = {i for i, entry in enumerate(entries) if entry.get("code")}
    data = {i for i, entry in enumerate(entries) if entry.get("data")}
    return code, data


def compare_entries(baseline: list[dict], variant: list[dict]) -> dict:
    if len(baseline) != len(variant):
        raise ValueError(
            f"CDL map size mismatch: baseline={len(baseline)} variant={len(variant)}"
        )
    baseline_code, baseline_data = classify_bytes(baseline)
    variant_code, variant_data = classify_bytes(variant)
    variant_only_code = sorted(variant_code - baseline_code)
    baseline_only_code = sorted(baseline_code - variant_code)
    variant_only_data = sorted(variant_data - baseline_data)
    baseline_only_data = sorted(baseline_data - variant_data)
    return {
        "code": {
            "baseline": len(baseline_code),
            "variant": len(variant_code),
            "variant_only": len(variant_only_code),
            "baseline_only": len(baseline_only_code),
            "variant_only_ranges": [
                {
                    "start": lo,
                    "end": hi,
                    "length": hi - lo + 1,
                    "cpu_start": lorom_cpu_address(lo),
                    "cpu_end": lorom_cpu_address(hi),
                }
                for lo, hi in ranges(variant_only_code)
            ],
            "baseline_only_ranges": [
                {
                    "start": lo,
                    "end": hi,
                    "length": hi - lo + 1,
                    "cpu_start": lorom_cpu_address(lo),
                    "cpu_end": lorom_cpu_address(hi),
                }
                for lo, hi in ranges(baseline_only_code)
            ],
        },
        "data": {
            "baseline": len(baseline_data),
            "variant": len(variant_data),
            "variant_only": len(variant_only_data),
            "baseline_only": len(baseline_only_data),
            "variant_only_ranges": [
                {"start": lo, "end": hi, "length": hi - lo + 1}
                for lo, hi in ranges(variant_only_data)
            ],
            "baseline_only_ranges": [
                {"start": lo, "end": hi, "length": hi - lo + 1}
                for lo, hi in ranges(baseline_only_data)
            ],
        },
    }


def run_fixture(rom: Path, fixture: Path, mesen_repo: Path, export: Path):
    runner = load_module(RUNNER_PATH, "ur_fixture_runner")
    commands = runner.parse_fixture(fixture)
    with MesenRpc(mesen_repo) as mesen:
        mesen.load_rom(str(rom.resolve()), timeout=300)
        mesen.tool("cdl.start")
        runner.FixtureRunner(
            mesen, Path(tempfile.mkdtemp(prefix="ur-cdl-dumps-"))
        ).execute(commands)
        mesen.tool("cdl.stop")
        return mesen.tool(
            "cdl.export", memoryType="snesPrgRom", path=str(export.resolve())
        )


def render_markdown(baseline: Path, variant: Path, result: dict) -> str:
    code = result["code"]
    data = result["data"]
    lines = [
        "# Fixture execution-coverage A/B",
        "",
        f"Baseline: `{baseline}`  ",
        f"Variant: `{variant}`",
        "",
        "This artifact is a discovery aid. It does not measure semantic completeness.",
        "",
        "## Summary",
        "",
        "| Metric | Baseline | Variant | Variant only | Baseline only |",
        "|---|---:|---:|---:|---:|",
        f"| Executed/code bytes | {code['baseline']} | {code['variant']} | {code['variant_only']} | {code['baseline_only']} |",
        f"| Data bytes | {data['baseline']} | {data['variant']} | {data['variant_only']} | {data['baseline_only']} |",
        "",
        "## Variant-only executed ranges",
        "",
        "| ROM offset start | End | CPU range | Bytes |",
        "|---:|---:|---|---:|",
    ]
    for item in code["variant_only_ranges"]:
        lines.append(
            f"| `0x{item['start']:06X}` | `0x{item['end']:06X}` | "
            f"`{item['cpu_start']}..{item['cpu_end']}` | {item['length']} |"
        )
    if not code["variant_only_ranges"]:
        lines.append("| _none_ | _none_ | _none_ | 0 |")
    lines += [
        "",
        "## Baseline-only executed ranges",
        "",
        "| ROM offset start | End | CPU range | Bytes |",
        "|---:|---:|---|---:|",
    ]
    for item in code["baseline_only_ranges"]:
        lines.append(
            f"| `0x{item['start']:06X}` | `0x{item['end']:06X}` | "
            f"`{item['cpu_start']}..{item['cpu_end']}` | {item['length']} |"
        )
    if not code["baseline_only_ranges"]:
        lines.append("| _none_ | _none_ | _none_ | 0 |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("variant", type=Path)
    ap.add_argument(
        "--mesen-for-ai-repo",
        type=Path,
        default=Path(os.environ.get("MESEN_FOR_AI_REPO", DEFAULT_MESEN_REPO)),
    )
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--md-out", type=Path, required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="ur-cdl-") as temp:
        temp_path = Path(temp)
        baseline_export = temp_path / "baseline.json"
        variant_export = temp_path / "variant.json"
        baseline_summary = run_fixture(
            args.rom, args.baseline, args.mesen_for_ai_repo, baseline_export
        )
        variant_summary = run_fixture(
            args.rom, args.variant, args.mesen_for_ai_repo, variant_export
        )
        baseline_entries = json.loads(baseline_export.read_text())["bytes"]
        variant_entries = json.loads(variant_export.read_text())["bytes"]

    result = compare_entries(baseline_entries, variant_entries)
    payload = {
        "schema_version": 1,
        "baseline": str(args.baseline),
        "variant": str(args.variant),
        "baseline_summary": baseline_summary,
        "variant_summary": variant_summary,
        **result,
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n")
    args.md_out.write_text(render_markdown(args.baseline, args.variant, result))
    print(args.md_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
