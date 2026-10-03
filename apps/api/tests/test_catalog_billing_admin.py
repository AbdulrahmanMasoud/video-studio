from __future__ import annotations

from .conftest import ADMIN, register


async def test_templates_catalog(client):
    r = await client.get("/templates")
    assert r.status_code == 200
    data = r.json()
    names = {t["name"] for t in data["templates"]}
    assert names == {"steps", "mirror", "quiz", "chat", "top-five", "hot-take"}
    t5 = next(t for t in data["templates"] if t["name"] == "top-five")
    assert "rank.media" in t5["media_fields"] and t5["preview"].endswith("top-five.jpg") and t5["available"]
    assert {s["id"] for s in data["sizes"]} >= {"9:16", "1:1", "4:5", "16:9"} and "ar" in {lang["code"] for lang in data["languages"]}
    r = await client.get("/templates", params={"include_disabled": "true"})
    assert len(r.json()["templates"]) == 24
    r = await client.get("/previews/steps.jpg")
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/")


async def test_billing_plans_and_mock_subscribe(client):
    r = await client.get("/billing/plans")
    assert r.status_code == 200 and {p["name"] for p in r.json()} == {"free", "starter", "pro", "agency"}
    u = await register(client)
    r = await client.post("/billing/checkout", json={"plan": "pro"}, headers=u["headers"])
    assert r.status_code == 200 and "mock_checkout=pro" in r.json()["url"]
    r = await client.post("/billing/mock/subscribe", json={"plan": "pro"}, headers=u["headers"])
    assert r.status_code == 200 and r.json()["plan"] == "pro" and r.json()["credits"] == 50
    me = (await client.get("/me", headers=u["headers"])).json()
    assert me["plan"]["brand_kit"] is True and me["plan"]["watermark"] is False and me["limits"]["concurrent_jobs"] == 3
    # brand kit now allowed
    r = await client.put("/me/brand-kit", json={"palette": {"accent": "#FF0000"}, "fonts": {"display": "Cairo"}}, headers=u["headers"])
    assert r.status_code == 200 and r.json()["palette"]["accent"] == "#FF0000"
    r = await client.put("/me/brand-kit", json={"palette": {"accent": "red"}}, headers=u["headers"])
    assert r.status_code == 422
    r = await client.get("/billing/portal", headers=u["headers"])
    assert r.status_code == 200
    r = await client.post("/billing/webhooks/lemonsqueezy", content=b"{}")
    assert r.status_code == 200  # mock provider accepts unsigned bodies; an empty payload is an unknown event


async def test_brand_kit_requires_plan(client):
    u = await register(client)
    r = await client.put("/me/brand-kit", json={"palette": {"accent": "#FF0000"}}, headers=u["headers"])
    assert r.status_code == 402 and r.json()["error_code"] == "plan_required"


async def test_admin_endpoints(client):
    u = await register(client)
    assert (await client.get("/admin/llm")).status_code == 401
    r = await client.get("/admin/llm", headers=ADMIN)
    assert r.status_code == 200 and set(r.json()["providers"]) >= {"anthropic", "openai", "ollama"}
    r = await client.put("/admin/llm", json={"planner_model": "openai/gpt-4o", "fallback_chain": ["groq/llama-3.3-70b-versatile"]}, headers=ADMIN)
    assert r.status_code == 200 and r.json()["settings"]["llm.planner_model"] == "openai/gpt-4o" and r.json()["settings"]["llm.fallback_chain"] == ["groq/llama-3.3-70b-versatile"]
    r = await client.put("/admin/llm", json={"planner_model": "not a model"}, headers=ADMIN)
    assert r.status_code == 422
    r = await client.post("/admin/grant-credits", json={"email": u["email"], "credits": 5, "note": "test"}, headers=ADMIN)
    assert r.status_code == 200 and r.json()["credits"] == 7
    r = await client.post("/admin/grant-credits", json={"email": "ghost@example.com", "credits": 1}, headers=ADMIN)
    assert r.status_code == 404
    r = await client.post("/admin/toggle-template", json={"name": "recipe", "enabled": True, "tier_required": "free"}, headers=ADMIN)
    assert r.status_code == 200
    assert "recipe" in {t["name"] for t in (await client.get("/templates")).json()["templates"]}
    await client.post("/admin/toggle-template", json={"name": "recipe", "enabled": False}, headers=ADMIN)
    assert (await client.get("/admin/failed", headers=ADMIN)).status_code == 200
    r = await client.post("/template-requests", json={"description": "A template for real-estate tours with a map and price tags", "example_url": "https://x.y/z"},
                          headers=u["headers"])
    assert r.status_code == 201
    r = await client.get("/admin/template-requests", headers=ADMIN)
    assert r.status_code == 200 and any(row["email"] == u["email"] for row in r.json())
    assert (await client.get("/admin/env", headers=ADMIN)).status_code == 200


async def test_health_and_metrics(client):
    r = await client.get("/health")
    assert r.status_code == 200 and r.json()["checks"] == {"db": "ok", "redis": "ok", "s3": "ok"}
    r = await client.get("/metrics")
    assert r.status_code == 200 and "vs_projects_total" in r.text and "vs_llm_cost_usd_total" in r.text
