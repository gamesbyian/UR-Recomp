#!/usr/bin/env python3
"""Focused archival recovery for historical Uniracers TAS/bot artifacts.

Uses public archive/index endpoints and exact historical URLs. Successful payloads
are saved under references/recovered/tas-bot/ with a JSON report and SHA-256.
This is intentionally narrow and may be run from GitHub Actions when local/web
fetch paths cannot reach old hosts.
"""
from __future__ import annotations
import hashlib, json, os, re, time
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

OUT = Path("references/recovered/tas-bot")
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = [
    "http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/usjo13.lua",
    "http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/Uniracers.html",
    "http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/WRs.txt",
    "http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/ZZZ%20-%20Realtime%20Play.smv",
    "http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/Uniracers%20%28U%29%20%5B%21%5D%20%28Clean%29.srm",
    "http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/Uniracers%20%28U%29%20%5B%21%5D%20%28Hacked%29.srm",
    "http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/01%20-%20Dragster%20in%2023.46.avi",
    "http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/02%20-%20Zoom%20Zoo%201st%20lap%20in%2023.97.avi",
    "http://dehacked.2y.net/microstorage.php/info/1674584940/Uniracers%20%28U%29%20%5B%21%5D.smv",
    "http://dscarroll.com/uniracerstas/FallThrough.ashx",
]

WILDCARDS = [
    "www.obellemare.com/speedruns/Uniracers*",
    "obellemare.com/speedruns/Uniracers*",
    "halamantariel.homeip.net/speedruns/*",
    "dscarroll.com/uniracerstas/*",
    "dehacked.2y.net/microstorage.php*1674584940*",
]

UA = "UR-Recomp archival research (+https://github.com/gamesbyian/UR-Recomp)"

def get(url: str, timeout=30) -> tuple[int, str, bytes]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urlopen(req, timeout=timeout) as r:
            return getattr(r, "status", 200), r.headers.get("Content-Type", ""), r.read()
    except HTTPError as e:
        body = e.read() if hasattr(e, "read") else b""
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", body
    except Exception as e:
        return 0, type(e).__name__, str(e).encode()

def cdx(urlpat: str) -> list[dict]:
    params = {
        "url": urlpat,
        "output": "json",
        "fl": "timestamp,original,statuscode,mimetype,digest,length",
        "filter": "statuscode:200",
        "collapse": "digest",
    }
    url = "https://web.archive.org/cdx/search/cdx?" + urlencode(params)
    status, ctype, body = get(url, 60)
    if status != 200:
        return [{"_error": f"CDX HTTP {status}", "_body": body[:500].decode("utf-8","replace")}]
    try:
        rows = json.loads(body)
    except Exception as e:
        return [{"_error": f"CDX parse {e}", "_body": body[:500].decode("utf-8","replace")}]
    if not rows:
        return []
    hdr, *vals = rows
    return [dict(zip(hdr, row)) for row in vals]

def safe_name(original: str, fallback: str) -> str:
    path = urlsplit(original).path.rstrip("/")
    name = path.rsplit("/",1)[-1] or fallback
    from urllib.parse import unquote
    name = unquote(name)
    name = re.sub(r"[^A-Za-z0-9._()!+ -]+", "_", name)
    return name[:180] or fallback

def looks_like_archive_wrapper(body: bytes, ctype: str) -> bool:
    head = body[:1000].lower()
    return ("text/html" in ctype.lower() and (b"wayback machine" in head or b"web.archive.org" in head))

report = {"targets": [], "wildcards": {}, "recovered": [], "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
seen_payload_sha = set()

for target in TARGETS:
    rec = {"url": target, "cdx": []}
    rows = cdx(target)
    rec["cdx"] = rows
    report["targets"].append(rec)
    for row in rows:
        if "_error" in row:
            continue
        ts = row["timestamp"]
        original = row["original"]
        replay = f"https://web.archive.org/web/{ts}id_/{original}"
        status, ctype, body = get(replay, 60)
        sha = hashlib.sha256(body).hexdigest() if body else None
        attempt = {"timestamp":ts,"original":original,"replay":replay,"status":status,"content_type":ctype,"bytes":len(body),"sha256":sha}
        rec.setdefault("replay_attempts", []).append(attempt)
        if status != 200 or not body or looks_like_archive_wrapper(body, ctype):
            continue
        if sha in seen_payload_sha:
            continue
        seen_payload_sha.add(sha)
        name = safe_name(original, "recovered.bin")
        # Avoid overwriting same filename with distinct captures.
        dest = OUT / name
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() != sha:
            dest = OUT / f"{dest.stem}-{ts}{dest.suffix}"
        dest.write_bytes(body)
        report["recovered"].append({**attempt, "path": str(dest)})
        print(f"RECOVERED {dest} {len(body)} bytes {sha}")

for pat in WILDCARDS:
    rows = cdx(pat)
    report["wildcards"][pat] = rows[:1000]
    print(f"CDX {pat}: {len(rows)} unique successful captures")

# Probe original/current URLs too. A dead hostname sometimes has a surviving redirect/mirror.
report["live_probes"] = []
for target in TARGETS:
    status, ctype, body = get(target, 30)
    report["live_probes"].append({
        "url": target, "status": status, "content_type": ctype,
        "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest() if body else None,
        "head": body[:160].decode("utf-8","replace")
    })

(OUT / "recovery-report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

md = ["# Historical Uniracers bot/TAS recovery report", "", f"Generated: {report['generated_utc']}", ""]
md += [f"- Targets probed: {len(TARGETS)}", f"- Payloads recovered: {len(report['recovered'])}", ""]
if report["recovered"]:
    md += ["## Recovered payloads", ""]
    for x in report["recovered"]:
        md += [f"- `{x['path']}` — {x['bytes']} bytes — SHA-256 `{x['sha256']}` — {x['original']} ({x['timestamp']})"]
else:
    md += ["No payload bytes were recovered in this run.", ""]
md += ["## Archive-index summary", ""]
for target in report["targets"]:
    good=[r for r in target["cdx"] if "_error" not in r]
    md += [f"- `{target['url']}`: {len(good)} unique successful CDX captures"]
md += ["", "## Wildcard archive surfaces", ""]
for pat, rows in report["wildcards"].items():
    good=[r for r in rows if "_error" not in r]
    md += [f"- `{pat}`: {len(good)} unique successful captures"]
(OUT / "recovery-report.md").write_text("\n".join(md)+"\n", encoding="utf-8")
print("\n".join(md))
