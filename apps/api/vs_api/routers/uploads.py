"""Presigned direct-to-S3 uploads for project inputs (audio/video)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from ..core import plans, storage
from ..deps import CurrentUser, err
from ..schemas import PresignIn, PresignOut

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/presign", response_model=PresignOut)
async def presign(body: PresignIn, user: CurrentUser):
    max_bytes = int(plans.limits().get("input_max_mb", 200)) * 1024 * 1024
    if body.content_type not in storage.INPUT_TYPES:
        raise err(415, "unsupported_type", f"unsupported input type {body.content_type}; upload audio or video")
    if body.size > max_bytes:
        raise err(413, "file_too_large", f"inputs are limited to {max_bytes // (1024 * 1024)} MB")
    key = storage.input_key(user.id, uuid.uuid4(), body.content_type)   # project id is not known yet: a fresh folder per upload
    post = await run_in_threadpool(storage.presign_upload, key, body.content_type, body.size)
    return PresignOut(**post)
