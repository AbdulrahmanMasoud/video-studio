"""Project assets: presign, register, list, patch description, delete. Real-content checks happen in the worker (status ready/invalid)."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import func, select
from starlette.concurrency import run_in_threadpool

from .. import services as svc
from ..core import plans, storage
from ..core.models import ProjectAsset
from ..deps import DB, CurrentUser, err
from ..schemas import AssetOut, AssetPatchIn, AssetRegisterIn, Msg, PresignIn, PresignOut

router = APIRouter(prefix="/projects/{project_id}/assets", tags=["assets"])
EDITABLE_STATUSES = {"created", "uploading", "queued_transcribe", "preview_ready", "failed"}


def _kind(content_type: str) -> str | None:
    if content_type in storage.IMAGE_TYPES:
        return "image"
    if content_type in storage.CLIP_TYPES:
        return "clip"
    return None


@router.post("/presign", response_model=PresignOut)
async def presign_asset(project_id: uuid.UUID, body: PresignIn, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    if p.status not in EDITABLE_STATUSES:
        raise err(409, "project_busy", "assets can be added before the preview and while the preview is ready")
    kind = _kind(body.content_type)
    if not kind:
        raise err(415, "unsupported_type", "assets must be JPG, PNG, WebP, HEIC images or MP4/MOV clips")
    lim = plans.limits()
    max_mb = int(lim.get("asset_image_max_mb", 25) if kind == "image" else lim.get("asset_clip_max_mb", 100))
    if body.size > max_mb * 1024 * 1024:
        raise err(413, "file_too_large", f"{kind}s are limited to {max_mb} MB")
    n = int((await db.execute(select(func.count()).select_from(ProjectAsset).where(ProjectAsset.project_id == p.id))).scalar_one())
    if n >= int(lim.get("assets_per_project", 20)):
        raise err(422, "too_many_assets", f"a project can have {lim.get('assets_per_project', 20)} assets")
    asset = ProjectAsset(project_id=p.id, user_id=user.id, kind=kind, key="", original_name=body.filename[:255], mime=body.content_type, bytes=body.size, status="pending")
    db.add(asset); await db.flush()
    asset.key = storage.asset_key(user.id, p.id, asset.id, body.content_type)
    await db.commit()
    post = await run_in_threadpool(storage.presign_upload, asset.key, body.content_type, max_mb * 1024 * 1024)
    return PresignOut(**post, asset_id=asset.id)


@router.post("", response_model=AssetOut, status_code=201)
async def register_asset(project_id: uuid.UUID, body: AssetRegisterIn, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    a = (await db.execute(select(ProjectAsset).where(ProjectAsset.id == body.asset_id, ProjectAsset.project_id == p.id))).scalar_one_or_none()
    if not a:
        raise err(404, "not_found", "asset not found; presign first")
    info = await run_in_threadpool(storage.head, a.key)
    if not info:
        raise err(422, "upload_missing", "the file was not uploaded")
    lim = plans.limits()
    max_mb = int(lim.get("asset_image_max_mb", 25) if a.kind == "image" else lim.get("asset_clip_max_mb", 100))
    if info["size"] > max_mb * 1024 * 1024:
        await run_in_threadpool(storage.delete, a.key)
        raise err(413, "file_too_large", f"{a.kind}s are limited to {max_mb} MB")
    a.bytes = info["size"]
    if body.description is not None:
        a.description = body.description.strip()[:300]
        a.description_source = "user" if a.description else None
    a.status = "uploaded"
    await db.commit(); await db.refresh(a)
    return svc.asset_out(a, await svc.presigned(a.key) if a.kind == "image" else None)


@router.get("", response_model=list[AssetOut])
async def list_assets(project_id: uuid.UUID, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    rows = (await db.execute(select(ProjectAsset).where(ProjectAsset.project_id == p.id).order_by(ProjectAsset.created_at))).scalars().all()
    return [svc.asset_out(a, await svc.presigned(a.key) if a.kind == "image" and a.status != "pending" else None) for a in rows]


@router.patch("/{asset_id}", response_model=AssetOut)
async def patch_asset(project_id: uuid.UUID, asset_id: uuid.UUID, body: AssetPatchIn, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    a = (await db.execute(select(ProjectAsset).where(ProjectAsset.id == asset_id, ProjectAsset.project_id == p.id))).scalar_one_or_none()
    if not a:
        raise err(404, "not_found", "asset not found")
    a.description = body.description.strip()[:300]
    a.description_source = "user" if a.description else None
    await db.commit(); await db.refresh(a)
    return svc.asset_out(a)


@router.delete("/{asset_id}", response_model=Msg)
async def delete_asset(project_id: uuid.UUID, asset_id: uuid.UUID, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    a = (await db.execute(select(ProjectAsset).where(ProjectAsset.id == asset_id, ProjectAsset.project_id == p.id))).scalar_one_or_none()
    if not a:
        raise err(404, "not_found", "asset not found")
    if p.status not in EDITABLE_STATUSES:
        raise err(409, "project_busy", "wait for the current step to finish")
    used = any(s.get("asset") == a.name for s in (p.asset_slots or []))
    if used:
        raise err(409, "asset_in_use", "remove the asset from its slot first")
    await db.delete(a); await db.commit()
    await run_in_threadpool(storage.delete, a.key)
    _ = datetime
    return Msg(message="asset deleted")
