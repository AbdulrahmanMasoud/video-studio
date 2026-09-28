"""'Request a template' form (drives the template roadmap)."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..core.models import TemplateRequest
from ..deps import DB, CurrentUser, err
from ..ratelimit import limiter
from ..schemas import Msg, TemplateRequestIn
from ..services import owns_key

router = APIRouter(prefix="/template-requests", tags=["templates"])


@router.post("", response_model=Msg, status_code=201)
@limiter.limit("10/hour")
async def create(request: Request, body: TemplateRequestIn, user: CurrentUser, db: DB):
    if body.file_key and not owns_key(user, body.file_key, "inputs"):
        raise err(422, "invalid_file_key", "file_key does not belong to you")
    db.add(TemplateRequest(user_id=user.id, description=body.description.strip(), example_url=body.example_url, file_key=body.file_key))
    await db.commit()
    return Msg(message="thanks, we received your template request")
