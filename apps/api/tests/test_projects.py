"""Projects without a running worker: creation gating, uploads, assets limits, state checks, credits, SSE."""
from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import select

from vs_api.core import credits, state
from vs_api.core.db import sync_session_factory
from vs_api.core.models import Project

from .conftest import ADMIN, png_bytes, register, upload_presigned


async def presign_and_upload_input(client, headers, data: bytes = b"RIFF....WAVEfmt fake", content_type="audio/wav") -> str:
    r = await client.post("/uploads/presign", json={"filename": "voice.wav", "content_type": content_type, "size": len(data)}, headers=headers)
    assert r.status_code == 200, r.text
    post = r.json()
    assert post["method"] == "POST" and post["key"].startswith("inputs/")
    await upload_presigned(post, data, content_type)
    return post["key"]


def set_status(project_id, status, **fields):
    with sync_session_factory()() as s:
        p = s.get(Project, uuid.UUID(project_id))
        for k, v in fields.items():
            setattr(p, k, v)
        state.transition(s, p, status, {"test": True}, force=True)
        s.commit()


async def test_presign_rejects_bad_types_and_sizes(client):
    u = await register(client)
    r = await client.post("/uploads/presign", json={"filename": "x.txt", "content_type": "text/plain", "size": 10}, headers=u["headers"])
    assert r.status_code == 415
    r = await client.post("/uploads/presign", json={"filename": "x.mp4", "content_type": "video/mp4", "size": 300 * 1024 * 1024}, headers=u["headers"])
    assert r.status_code == 413


async def test_create_project_validations(client):
    u = await register(client)
    h = u["headers"]
    base = {"title": "T", "template": "steps", "size": "9:16", "platform": "tiktok"}
    r = await client.post("/projects", json=base, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "input_required"
    r = await client.post("/projects", json={**base, "script": "hello"}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "tts_disabled"
    r = await client.post("/projects", json={**base, "template": "recipe", "input_key": "x"}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "template_disabled"
    r = await client.post("/projects", json={**base, "template": "nope", "input_key": "x"}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "unknown_template"
    r = await client.post("/projects", json={**base, "input_key": "inputs/someone-else/x.wav"}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "invalid_input_key"
    r = await client.post("/projects", json={**base, "input_key": f"inputs/{u['user']['id']}/missing/x.wav"}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "input_missing"
    r = await client.post("/projects", json={**base, "size": "abc", "input_key": "x"}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "invalid_size"
    r = await client.post("/projects", json={**base, "platform": "myspace", "input_key": "x"}, headers=h)
    assert r.status_code == 422


async def test_create_list_get_delete_and_concurrency(client):
    u = await register(client)
    h = u["headers"]
    key = await presign_and_upload_input(client, h)
    r = await client.post("/projects", json={"title": "My first", "template": "steps", "size": "9:16", "platform": "tiktok", "input_key": key, "brief": {"title": "Hi"}},
                          headers=h)
    assert r.status_code == 201, r.text
    p = r.json()["project"]
    assert p["status"] == "queued_transcribe" and p["input_kind"] == "audio" and p["size_w"] == 1080 and r.json()["job_id"]
    # free plan: 1 concurrent job
    key2 = await presign_and_upload_input(client, h)
    r = await client.post("/projects", json={"title": "Second", "template": "quiz", "size": "16:9", "input_key": key2}, headers=h)
    assert r.status_code == 429 and r.json()["error_code"] == "too_many_jobs"
    r = await client.get("/projects", headers=h)
    assert r.status_code == 200 and r.json()["total"] == 1 and r.json()["items"][0]["id"] == p["id"]
    r = await client.get(f"/projects/{p['id']}", headers=h)
    assert r.status_code == 200 and r.json()["assets"] == [] and r.json()["brief"] == {"title": "Hi"}
    # other users cannot see it
    other = await register(client)
    assert (await client.get(f"/projects/{p['id']}", headers=other["headers"])).status_code == 404
    # edits are refused before preview_ready
    r = await client.post(f"/projects/{p['id']}/texts", json={"fields": [{"path": "scenes[0].title", "value": "x"}]}, headers=h)
    assert r.status_code == 409 and r.json()["error_code"] == "not_preview_ready"
    assert (await client.post(f"/projects/{p['id']}/render", headers=h)).status_code == 409
    assert (await client.get(f"/projects/{p['id']}/download", headers=h)).status_code == 409
    assert (await client.post(f"/projects/{p['id']}/retry", headers=h)).status_code == 409
    # delete releases the slot
    r = await client.request("DELETE", f"/projects/{p['id']}", headers=h)
    assert r.status_code == 200
    assert (await client.get(f"/projects/{p['id']}", headers=h)).status_code == 404
    r = await client.post("/projects", json={"title": "Second", "template": "quiz", "size": "16:9", "input_key": key2}, headers=h)
    assert r.status_code == 201


async def test_texts_slots_render_credits_and_events(client):
    """Drive the state machine directly (no worker) to test the API rules around preview_ready."""
    u = await register(client)
    h = u["headers"]
    key = await presign_and_upload_input(client, h)
    p = (await client.post("/projects", json={"title": "Credits", "template": "top-five", "size": "9:16", "input_key": key}, headers=h)).json()["project"]
    plan = {"lang": "en", "scenes": [{"type": "intro", "start": 0, "title": "Top 3"}, {"type": "rank", "start": "w:2", "n": 1, "title": "One"}]}
    set_status(p["id"], "preview_ready", plan=plan, editable_fields=[{"path": "scenes[0].title", "label": "intro · title", "value": "Top 3", "maxLen": 60}],
               asset_slots=[{"path": "scenes[1].media", "asset": None}], words=[{"w": "a", "s": 0, "e": 0.2}] * 10, duration_s=200.0)
    r = await client.get(f"/projects/{p['id']}", headers=h)
    assert r.json()["credits_needed"] == 3 and r.json()["editable_fields"][0]["path"] == "scenes[0].title"
    # texts: unknown path / too long
    r = await client.post(f"/projects/{p['id']}/texts", json={"fields": [{"path": "scenes[9].nope", "value": "x"}]}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "field_not_editable"
    r = await client.post(f"/projects/{p['id']}/texts", json={"fields": [{"path": "scenes[0].title", "value": "x" * 61}]}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "value_too_long"
    # asset slots: unknown slot / unknown asset / bad word
    r = await client.post(f"/projects/{p['id']}/asset-slots", json={"changes": [{"path": "scenes[0].title", "asset": None}]}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "invalid_slot"
    r = await client.post(f"/projects/{p['id']}/asset-slots", json={"changes": [{"path": "scenes[1].media", "asset": "asset_nope"}]}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "unknown_asset"
    r = await client.post(f"/projects/{p['id']}/asset-slots", json={}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "nothing_to_do"
    # render needs 3 credits; free user has 2
    r = await client.post(f"/projects/{p['id']}/render", headers=h)
    assert r.status_code == 402 and r.json()["error_code"] == "insufficient_credits"
    await client.post("/admin/grant-credits", json={"email": u["email"], "credits": 5}, headers=ADMIN)
    r = await client.post(f"/projects/{p['id']}/render", headers=h)
    assert r.status_code == 200 and r.json()["project"]["status"] == "queued_render" and r.json()["project"]["credits_reserved"] == 3
    me = (await client.get("/me", headers=h)).json()
    assert me["user"]["credits"] == 4  # 7 - 3 reserved
    # ledger consistency
    with sync_session_factory()() as s:
        assert credits.balance(s, uuid.UUID(u["user"]["id"])) == 4
    # a render failure releases credits (simulate what the worker does)
    with sync_session_factory()() as s:
        proj = s.get(Project, uuid.UUID(p["id"]))
        credits.release(s, proj); state.fail(s, proj, "timeout", "boom", "render"); s.commit()
    assert (await client.get("/me", headers=h)).json()["user"]["credits"] == 7
    r = await client.get(f"/projects/{p['id']}", headers=h)
    assert r.json()["status"] == "failed" and r.json()["error_code"] == "timeout" and r.json()["failed_stage"] == "render"
    # retry from render re-reserves and re-queues
    r = await client.post(f"/projects/{p['id']}/retry", headers=h)
    assert r.status_code == 200 and r.json()["project"]["status"] == "queued_render"
    assert (await client.get("/me", headers=h)).json()["user"]["credits"] == 4
    # SSE: current state first, then the end event once done
    set_status(p["id"], "done", output_key="outputs/x/y/final.mp4")
    async with client.stream("GET", f"/projects/{p['id']}/events", headers=h, timeout=10) as resp:
        assert resp.status_code == 200
        chunks = []
        async for line in resp.aiter_lines():
            chunks.append(line)
            if line.startswith("event: end"):
                break
        text = "\n".join(chunks)
        assert "event: status" in text and '"done"' in text
    r = await client.get(f"/projects/{p['id']}/download", headers=h)
    assert r.status_code == 200 and r.json()["url"].startswith("http") and r.json()["filename"] == "Credits.mp4"


async def test_assets_presign_register_limits(client):
    u = await register(client)
    h = u["headers"]
    key = await presign_and_upload_input(client, h)
    p = (await client.post("/projects", json={"title": "Assets", "template": "top-five", "size": "9:16", "input_key": key}, headers=h)).json()["project"]
    pid = p["id"]
    r = await client.post(f"/projects/{pid}/assets/presign", json={"filename": "a.gif", "content_type": "image/gif", "size": 10}, headers=h)
    assert r.status_code == 415
    r = await client.post(f"/projects/{pid}/assets/presign", json={"filename": "a.png", "content_type": "image/png", "size": 30 * 1024 * 1024}, headers=h)
    assert r.status_code == 413
    r = await client.post(f"/projects/{pid}/assets/presign", json={"filename": "clip.mov", "content_type": "video/quicktime", "size": 101 * 1024 * 1024}, headers=h)
    assert r.status_code == 413
    png = png_bytes()
    r = await client.post(f"/projects/{pid}/assets/presign", json={"filename": "a.png", "content_type": "image/png", "size": len(png)}, headers=h)
    assert r.status_code == 200, r.text
    post = r.json()
    assert post["asset_id"] and post["key"].startswith(f"assets/{u['user']['id']}/{pid}/")
    # register before upload → 422
    r = await client.post(f"/projects/{pid}/assets", json={"asset_id": post["asset_id"], "description": "a photo"}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "upload_missing"
    await upload_presigned(post, png, "image/png")
    r = await client.post(f"/projects/{pid}/assets", json={"asset_id": post["asset_id"], "description": "a photo"}, headers=h)
    assert r.status_code == 201, r.text
    a = r.json()
    assert a["status"] == "uploaded" and a["description_source"] == "user" and a["name"].startswith("asset_") and a["thumbnail_url"]
    r = await client.patch(f"/projects/{pid}/assets/{a['id']}", json={"description": "the product"}, headers=h)
    assert r.status_code == 200 and r.json()["description"] == "the product"
    r = await client.get(f"/projects/{pid}/assets", headers=h)
    assert r.status_code == 200 and len(r.json()) == 1
    # count limit: presign 19 more then the 21st fails
    for i in range(19):
        r = await client.post(f"/projects/{pid}/assets/presign", json={"filename": f"{i}.png", "content_type": "image/png", "size": 100}, headers=h)
        assert r.status_code == 200
    r = await client.post(f"/projects/{pid}/assets/presign", json={"filename": "x.png", "content_type": "image/png", "size": 100}, headers=h)
    assert r.status_code == 422 and r.json()["error_code"] == "too_many_assets"
    r = await client.request("DELETE", f"/projects/{pid}/assets/{a['id']}", headers=h)
    assert r.status_code == 200
    assert (await client.request("DELETE", f"/projects/{pid}/assets/{a['id']}", headers=h)).status_code == 404


async def test_project_rate_limit_per_user(client, monkeypatch):
    from vs_api import ratelimit
    from vs_api.config import get_settings
    s = get_settings()
    monkeypatch.setattr(s, "rate_limits_enabled", True)
    u = await register(client)
    uid = u["user"]["id"]
    for _ in range(10):
        ratelimit.check_user_limit(uid, "projects", 10)
    with pytest.raises(Exception) as ei:
        ratelimit.check_user_limit(uid, "projects", 10)
    assert getattr(ei.value, "status_code", None) == 429
    monkeypatch.setattr(s, "rate_limits_enabled", False)
    _ = asyncio, select


async def test_enqueue_paths_texts_slots_retry_delete_active(client):
    """Happy paths that only enqueue RQ jobs (no worker needed): texts, asset slots, retry from preview, delete an active project."""
    u = await register(client)
    h = u["headers"]
    key = await presign_and_upload_input(client, h)
    p = (await client.post("/projects", json={"title": "Enqueue", "template": "top-five", "size": "1:1", "input_key": key}, headers=h)).json()["project"]
    pid = p["id"]
    # register a ready asset directly
    png = png_bytes()
    post = (await client.post(f"/projects/{pid}/assets/presign", json={"filename": "a.png", "content_type": "image/png", "size": len(png)}, headers=h)).json()
    await upload_presigned(post, png, "image/png")
    a = (await client.post(f"/projects/{pid}/assets", json={"asset_id": post["asset_id"]}, headers=h)).json()
    with sync_session_factory()() as s:
        from vs_api.core.models import ProjectAsset
        row = s.get(ProjectAsset, uuid.UUID(a["id"])); row.status = "ready"; s.commit()
    plan = {"lang": "en", "scenes": [{"type": "intro", "start": 0, "title": "Top 3"}, {"type": "rank", "start": "w:2", "n": 1, "title": "One", "media": a["name"]}]}
    set_status(pid, "preview_ready", plan=plan, editable_fields=[{"path": "scenes[0].title", "label": "intro · title", "value": "Top 3", "maxLen": 60}],
               asset_slots=[{"path": "scenes[1].media", "asset": a["name"]}], words=[{"w": "a", "s": 0, "e": 0.2}] * 10, duration_s=20.0)
    # asset in use cannot be deleted
    r = await client.request("DELETE", f"/projects/{pid}/assets/{a['id']}", headers=h)
    assert r.status_code == 409 and r.json()["error_code"] == "asset_in_use"
    d = (await client.get(f"/projects/{pid}", headers=h)).json()
    assert d["unused_assets"] == [] and d["assets"][0]["status"] == "ready"
    r = await client.post(f"/projects/{pid}/texts", json={"fields": [{"path": "scenes[0].title", "value": "Top three"}]}, headers=h)
    assert r.status_code == 200 and r.json()["project"]["status"] == "planning" and r.json()["job_id"].startswith("edit-")
    set_status(pid, "preview_ready")
    r = await client.post(f"/projects/{pid}/asset-slots", json={"changes": [{"path": "scenes[1].media", "asset": None}], "insert": [{"asset": a["name"], "at_word": 3, "dur": 2}]},
                          headers=h)
    assert r.status_code == 200 and r.json()["project"]["status"] == "planning"
    r = await client.post(f"/projects/{pid}/asset-slots", json={"insert": [{"asset": a["name"], "at_word": 99}]}, headers=h)
    assert r.status_code == 409  # planning now
    # a failed preview retries from the transcribe queue
    with sync_session_factory()() as s:
        proj = s.get(Project, uuid.UUID(pid)); state.fail(s, proj, "input_too_long", "too long", "preview"); s.commit()
    r = await client.post(f"/projects/{pid}/retry", headers=h)
    assert r.status_code == 200 and r.json()["project"]["status"] == "queued_transcribe" and r.json()["project"]["attempts"] == 2
    # delete cancels the active job and releases the concurrency slot
    r = await client.request("DELETE", f"/projects/{pid}", headers=h)
    assert r.status_code == 200
    assert (await client.get("/projects", headers=h)).json()["total"] == 0
    assert (await client.get("/projects", params={"status": "failed"}, headers=h)).json()["items"] == []
    # asset presign is refused on a deleted/absent project
    assert (await client.post(f"/projects/{pid}/assets/presign", json={"filename": "a.png", "content_type": "image/png", "size": 5}, headers=h)).status_code == 404


async def test_custom_sizes(client):
    from vs_api.services import parse_size
    assert parse_size("4:3") == (1440, 1080) and parse_size("1080x1920") == (1080, 1920) and parse_size("21:9") == (2520, 1080)
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        parse_size("10x10")
