from __future__ import annotations

import asyncio
import re

from .conftest import mailpit_body, mailpit_messages, register, unique_email


async def test_register_login_me_and_cookies(client):
    email = unique_email()
    r = await client.post("/auth/register", json={"email": email, "password": "correct-horse-battery"})
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == email and body["user"]["plan"] == "free" and body["user"]["credits"] == 2
    assert "vs_access" in r.cookies and "vs_csrf" in r.cookies and body["csrf_token"] == r.cookies["vs_csrf"]
    # duplicate
    r2 = await client.post("/auth/register", json={"email": email, "password": "correct-horse-battery"})
    assert r2.status_code == 409 and r2.json()["error_code"] == "email_taken"
    # cookie session: GET works, POST without CSRF header is rejected, with header ok
    r = await client.get("/me")
    assert r.status_code == 200 and r.json()["user"]["email"] == email and r.json()["plan"]["name"] == "free"
    r = await client.patch("/me", json={"locale": "ar"})
    assert r.status_code == 403 and r.json()["error_code"] == "csrf"
    r = await client.patch("/me", json={"locale": "ar"}, headers={"X-CSRF-Token": body["csrf_token"]})
    assert r.status_code == 200 and r.json()["locale"] == "ar"
    # logout clears, login works
    r = await client.post("/auth/logout", headers={"X-CSRF-Token": body["csrf_token"]})
    assert r.status_code == 200
    client.cookies.clear()
    assert (await client.get("/me")).status_code == 401
    r = await client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert r.status_code == 401 and r.json()["error_code"] == "bad_credentials"
    r = await client.post("/auth/login", json={"email": email, "password": "correct-horse-battery"})
    assert r.status_code == 200
    r = await client.post("/auth/refresh")
    assert r.status_code == 200 and r.json()["access_token"]


async def test_bearer_auth_needs_no_csrf(client):
    u = await register(client)
    client.cookies.clear()
    r = await client.patch("/me", json={"locale": "ar"}, headers=u["headers"])
    assert r.status_code == 200


async def test_email_verification_via_mailpit(client):
    u = await register(client)
    token = None
    for _ in range(20):
        msgs = await mailpit_messages(u["email"])
        if msgs:
            body = await mailpit_body(msgs[0]["ID"])
            m = re.search(r"token=([\w.\-]+)", body)
            token = m.group(1) if m else None
            break
        await asyncio.sleep(0.5)
    assert token, "verification email not received by Mailpit"
    assert (await client.get("/me", headers=u["headers"])).json()["user"]["email_verified"] is False
    r = await client.post("/auth/verify", json={"token": token})
    assert r.status_code == 200
    assert (await client.get("/me", headers=u["headers"])).json()["user"]["email_verified"] is True
    r = await client.post("/auth/verify", json={"token": "nope"})
    assert r.status_code == 400 and r.json()["error_code"] == "token_invalid"


async def test_password_reset_flow(client):
    u = await register(client)
    r = await client.post("/auth/forgot", json={"email": u["email"]})
    assert r.status_code == 200
    assert (await client.post("/auth/forgot", json={"email": "nobody@example.com"})).status_code == 200  # no enumeration
    token = None
    for _ in range(20):
        msgs = [m for m in await mailpit_messages(u["email"]) if "Reset" in m.get("Subject", "")]
        if msgs:
            token = re.search(r"token=([\w.\-]+)", await mailpit_body(msgs[0]["ID"])).group(1)
            break
        await asyncio.sleep(0.5)
    assert token
    r = await client.post("/auth/reset", json={"token": token, "password": "another-strong-pass"})
    assert r.status_code == 200
    r = await client.post("/auth/reset", json={"token": token, "password": "third-pass-attempt"})  # single use
    assert r.status_code == 400
    assert (await client.post("/auth/login", json={"email": u["email"], "password": "another-strong-pass"})).status_code == 200


async def test_delete_account(client):
    u = await register(client)
    r = await client.request("DELETE", "/me", json={"password": "wrong"}, headers=u["headers"])
    assert r.status_code == 401
    r = await client.request("DELETE", "/me", json={"password": u["password"]}, headers=u["headers"])
    assert r.status_code == 200
    assert (await client.get("/me", headers=u["headers"])).status_code == 401


async def test_validation_errors_are_typed(client):
    r = await client.post("/auth/register", json={"email": "not-an-email", "password": "short"})
    assert r.status_code == 422 and r.json()["error_code"] == "validation_error"
