"""Phase 3 DoD integration test (needs the worker running with PLANNER_MODE=mock): register → upload the espeak fixture →
project with 3 image assets (+1 invalid) → preview_ready → edit a text → swap an asset → render → download a valid MP4."""
from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

import httpx
import pytest

from vs_api.config import get_settings

from .conftest import ADMIN, png_bytes, register, upload_presigned

pytestmark = pytest.mark.integration
FIXTURE = Path(__file__).parent / "fixtures" / "voice.mp3"
API_URL = os.environ.get("API_URL", "http://api:8000")


@pytest.fixture
async def client():
    """The live API container (same database and queue as the running worker), not the in-process app."""
    async with httpx.AsyncClient(base_url=API_URL, timeout=60) as c:
        yield c


async def fetch_presigned(url: str) -> httpx.Response:
    """SigV4 signs the Host header: rewrite the address to the internal endpoint but keep the public host in the header."""
    public, internal = get_settings().s3_public_endpoint_url, get_settings().s3_endpoint_url
    host = public.split("://", 1)[1]
    async with httpx.AsyncClient(timeout=120) as c:
        return await c.get(url.replace(public, internal), headers={"Host": host})


async def wait_status(client, headers, pid, targets, timeout=600):
    t0 = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - t0 < timeout:
        r = await client.get(f"/projects/{pid}", headers=headers)
        p = r.json()
        if p["status"] in targets:
            return p
        if p["status"] == "failed" and "failed" not in targets:
            raise AssertionError(f"project failed: {p['error_code']} {p['error_message']}")
        await asyncio.sleep(2)
    raise AssertionError(f"timeout waiting for {targets}")


async def add_asset(client, h, pid, name, data, ctype, description=None):
    post = (await client.post(f"/projects/{pid}/assets/presign", json={"filename": name, "content_type": ctype, "size": len(data)}, headers=h)).json()
    await upload_presigned(post, data, ctype)
    body = {"asset_id": post["asset_id"]}
    if description is not None:
        body["description"] = description
    r = await client.post(f"/projects/{pid}/assets", json=body, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


async def test_full_flow(client):
    assert FIXTURE.exists(), "tests/fixtures/voice.mp3 missing"
    u = await register(client)
    h = u["headers"]
    data = FIXTURE.read_bytes()
    post = (await client.post("/uploads/presign", json={"filename": "voice.mp3", "content_type": "audio/mpeg", "size": len(data)}, headers=h)).json()
    await upload_presigned(post, data, "audio/mpeg")
    r = await client.post("/projects", json={"title": "Integration", "template": "top-five", "size": "9:16", "platform": "tiktok", "input_key": post["key"],
                                             "brief": {"title": "Three sleep tips"}}, headers=h)
    assert r.status_code == 201, r.text
    pid = r.json()["project"]["id"]
    cols = [(230, 60, 60), (60, 160, 230), (60, 200, 120)]
    assets = [await add_asset(client, h, pid, f"img{i}.png", png_bytes(color=c), "image/png", "a coloured card" if i == 0 else None) for i, c in enumerate(cols)]
    bad = await add_asset(client, h, pid, "notimage.png", b"this is not a png at all", "image/png")
    # NOTE: the project was queued at creation; assets registered right after are picked up because the worker downloads them at job start.
    p = await wait_status(client, h, pid, {"preview_ready"})
    assert p["planner"] in ("llm", "fallback") and p["preview_url"] and p["plan"]["scenes"] and p["editable_fields"] and p["words"]
    by = {a["id"]: a for a in p["assets"]}
    assert all(by[a["id"]]["status"] == "ready" for a in assets), by
    assert by[bad["id"]]["status"] == "invalid" and by[bad["id"]]["error"]
    assert by[assets[1]["id"]]["description"] and by[assets[1]["id"]]["description_source"] == "ai"
    slots = {s["path"]: s["asset"] for s in p["asset_slots"]}
    names = [by[a["id"]]["name"] for a in assets]
    assert set(slots.values()) >= set(names), slots       # the mock planner placed all three images
    # contact sheet is a real JPEG (presigned for the browser's host; inside the network we keep the signed Host header)
    img = await fetch_presigned(p["preview_url"])
    assert img.status_code == 200 and img.content[:3] == b"\xff\xd8\xff"
    # edit a text
    field = p["editable_fields"][0]
    r = await client.post(f"/projects/{pid}/texts", json={"fields": [{"path": field["path"], "value": "Edited by test"}]}, headers=h)
    assert r.status_code == 200 and r.json()["project"]["status"] == "planning"
    p = await wait_status(client, h, pid, {"preview_ready"}, timeout=300)
    assert next(f for f in p["editable_fields"] if f["path"] == field["path"])["value"] == "Edited by test"
    # swap an asset: put the third image into the first slot
    first_slot = next(path for path, a in slots.items() if a == names[0])
    r = await client.post(f"/projects/{pid}/asset-slots", json={"changes": [{"path": first_slot, "asset": names[2]}]}, headers=h)
    assert r.status_code == 200
    p = await wait_status(client, h, pid, {"preview_ready"}, timeout=300)
    assert {s["path"]: s["asset"] for s in p["asset_slots"]}[first_slot] == names[2]
    assert names[0] in p["unused_assets"] or names[0] in {s["asset"] for s in p["asset_slots"]}
    # render (2 free credits, 13 s video → 1 credit) → done → download
    r = await client.post(f"/projects/{pid}/render", headers=h)
    assert r.status_code == 200, r.text
    p = await wait_status(client, h, pid, {"done"}, timeout=900)
    assert p["credits_committed"] == 1 and p["output_size"][0] <= 720 and p["qa"]["has_audio"]
    me = (await client.get("/me", headers=h)).json()
    assert me["user"]["credits"] == 1
    r = await client.get(f"/projects/{pid}/download", headers=h)
    assert r.status_code == 200
    out = Path("/tmp/integration_final.mp4")
    v = await fetch_presigned(r.json()["url"])
    assert v.status_code == 200 and len(v.content) > 50_000
    out.write_bytes(v.content)
    if __import__("shutil").which("ffprobe"):
        o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout
        assert "video" in o and "audio" in o
    else:
        assert v.content[4:8] == b"ftyp"
    # events endpoint ends immediately for a finished project
    async with client.stream("GET", f"/projects/{pid}/events", headers=h, timeout=10) as resp:
        text = ""
        async for line in resp.aiter_lines():
            text += line + "\n"
            if line.startswith("event: end"):
                break
        assert "event: end" in text
    _ = ADMIN
