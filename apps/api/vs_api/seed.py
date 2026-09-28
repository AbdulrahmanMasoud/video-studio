"""Dev seed: an admin user with credits (idempotent). `make seed`."""
from __future__ import annotations

import os

from sqlalchemy import select

from .core import credits
from .core.db import sync_session_factory
from .core.models import User
from .core.security import hash_password


def main():
    email = os.environ.get("SEED_EMAIL", "admin@example.com")
    password = os.environ.get("SEED_PASSWORD", "admin-password-123")
    with sync_session_factory()() as s:
        u = s.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if u is None:
            u = User(email=email, password_hash=hash_password(password), plan="pro", is_admin=True, credits=0)
            s.add(u); s.flush()
            credits.grant(s, u.id, 50, "grant", external_id=f"seed:{email}", note="seed")
            s.commit()
            print(f"created {email} / {password} (pro, 50 credits)")
        else:
            print(f"{email} exists (plan {u.plan}, {u.credits} credits)")


if __name__ == "__main__":
    main()
