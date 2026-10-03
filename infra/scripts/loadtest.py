#!/usr/bin/env python3
"""Load test: N concurrent jobs through the API (register → upload → create → preview → render → done), reporting throughput.

    python3 infra/scripts/loadtest.py --api http://localhost:8000 --jobs 10 --fixture apps/api/tests/fixtures/voice.mp3
Run with the worker in draft mode for a cheap full pass:  RENDER_DRAFT=1 PLANNER_MODE=mock docker compose up -d --force-recreate worker
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import statistics
import time
import urllib.request
import uuid
from pathlib import Path


def req(method, url, data=None, headers=None, raw=False):
    body = data if raw else (json.dumps(data).encode() if data is not None else None)
    r = urllib.request.Request(url, data=body, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read() or b"null")


def multipart(url, fields, filename, content, content_type):
    boundary = "----vs" + uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n".encode() + content + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    r = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return resp.status


def one_job(api: str, admin_key: str, fixture: Path, i: int, public_rewrite: tuple[str, str] | None):
    t = {"start": time.time()}
    email = f"load-{uuid.uuid4().hex[:8]}@example.com"
    auth = req("POST", f"{api}/auth/register", {"email": email, "password": "load-test-pass-123"})
    h = {"Authorization": f"Bearer {auth['access_token']}"}
    req("POST", f"{api}/admin/grant-credits", {"email": email, "credits": 5}, {"X-Admin-Key": admin_key})
    data = fixture.read_bytes()
    post = req("POST", f"{api}/uploads/presign", {"filename": fixture.name, "content_type": "audio/mpeg", "size": len(data)}, h)
    url = post["url"].replace(*public_rewrite) if public_rewrite else post["url"]
    multipart(url, post["fields"], fixture.name, data, "audio/mpeg")
    p = req("POST", f"{api}/projects", {"title": f"load {i}", "template": "steps", "size": "9:16", "platform": "tiktok", "input_key": post["key"], "lang": "en"}, h)["project"]
    pid = p["id"]
    t["created"] = time.time()
    while True:
        cur = req("GET", f"{api}/projects/{pid}", headers=h)
        if cur["status"] == "preview_ready":
            break
        if cur["status"] == "failed":
            return {"i": i, "error": f"preview failed: {cur['error_code']}"}
        time.sleep(2)
    t["preview"] = time.time()
    req("POST", f"{api}/projects/{pid}/render", headers=h)
    while True:
        cur = req("GET", f"{api}/projects/{pid}", headers=h)
        if cur["status"] == "done":
            break
        if cur["status"] == "failed":
            return {"i": i, "error": f"render failed: {cur['error_code']}"}
        time.sleep(2)
    t["done"] = time.time()
    return {"i": i, "preview_s": round(t["preview"] - t["created"], 1), "render_s": round(t["done"] - t["preview"], 1), "total_s": round(t["done"] - t["start"], 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000"); ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--fixture", default="apps/api/tests/fixtures/voice.mp3"); ap.add_argument("--admin-key", default="change-me-admin-key")
    ap.add_argument("--rewrite", default="", help="public→reachable S3 host rewrite, e.g. http://localhost:9100=http://minio:9000")
    a = ap.parse_args()
    rewrite = tuple(a.rewrite.split("=", 1)) if a.rewrite else None
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        results = list(ex.map(lambda i: one_job(a.api, a.admin_key, Path(a.fixture), i, rewrite), range(a.jobs)))  # type: ignore[arg-type]
    wall = time.time() - t0
    ok = [r for r in results if "error" not in r]
    print(json.dumps(results, indent=1))
    if ok:
        print(f"\n{len(ok)}/{a.jobs} jobs done in {wall:.0f}s wall → {len(ok) / wall * 60:.1f} jobs/min")
        print(f"preview p50 {statistics.median(r['preview_s'] for r in ok):.0f}s, render p50 {statistics.median(r['render_s'] for r in ok):.0f}s, "
              f"total p50 {statistics.median(r['total_s'] for r in ok):.0f}s, max {max(r['total_s'] for r in ok):.0f}s")
    bad = [r for r in results if "error" in r]
    if bad:
        print("FAILED:", bad)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
