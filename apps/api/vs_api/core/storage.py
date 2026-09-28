"""S3-compatible object storage (MinIO in dev, R2/S3 in prod). boto3 is sync: the API calls these in a threadpool."""
from __future__ import annotations

import mimetypes
import uuid
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from ..config import get_settings

INPUT_TYPES = {"audio/mpeg": "mp3", "audio/mp4": "m4a", "audio/x-m4a": "m4a", "audio/aac": "aac", "audio/wav": "wav", "audio/x-wav": "wav",
               "audio/webm": "webm", "audio/ogg": "ogg", "audio/flac": "flac", "video/mp4": "mp4", "video/quicktime": "mov", "video/webm": "webm",
               "video/x-matroska": "mkv", "video/x-m4v": "m4v"}
IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/heic": "heic", "image/heif": "heif"}
CLIP_TYPES = {"video/mp4": "mp4", "video/quicktime": "mov"}


def _client(public: bool = False):
    s = get_settings()
    return boto3.client("s3", endpoint_url=s.s3_public_endpoint_url if public else s.s3_endpoint_url, region_name=s.s3_region,
                        aws_access_key_id=s.s3_access_key, aws_secret_access_key=s.s3_secret_key,
                        config=Config(signature_version="s3v4", s3={"addressing_style": "path" if s.s3_force_path_style else "auto"}))


@lru_cache(maxsize=2)
def client(public: bool = False):
    return _client(public)


def bucket() -> str:
    return get_settings().s3_bucket


def input_key(user_id, project_id, content_type: str) -> str:
    ext = INPUT_TYPES.get(content_type, "bin")
    return f"inputs/{user_id}/{project_id}/{uuid.uuid4().hex}.{ext}"


def asset_key(user_id, project_id, asset_id, content_type: str) -> str:
    ext = IMAGE_TYPES.get(content_type) or CLIP_TYPES.get(content_type) or "bin"
    return f"assets/{user_id}/{project_id}/{asset_id}.{ext}"


def output_key(user_id, project_id, name: str) -> str:
    return f"outputs/{user_id}/{project_id}/{name}"


def presign_upload(key: str, content_type: str, max_bytes: int, ttl: int | None = None) -> dict:
    """Presigned POST (browser multipart form) enforcing content-type and size via the policy."""
    s = get_settings()
    fields = {"Content-Type": content_type}
    conditions = [{"Content-Type": content_type}, ["content-length-range", 1, int(max_bytes)]]
    post = client(public=True).generate_presigned_post(Bucket=bucket(), Key=key, Fields=fields, Conditions=conditions, ExpiresIn=ttl or s.presign_ttl_s)
    return {"url": post["url"], "fields": post["fields"], "key": key, "method": "POST", "expires_in": ttl or s.presign_ttl_s}


def presign_download(key: str, filename: str | None = None, ttl: int | None = None) -> str:
    s = get_settings()
    params = {"Bucket": bucket(), "Key": key}
    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
    return client(public=True).generate_presigned_url("get_object", Params=params, ExpiresIn=ttl or s.presign_ttl_s)


def head(key: str) -> dict | None:
    try:
        r = client().head_object(Bucket=bucket(), Key=key)
        return {"size": int(r.get("ContentLength", 0)), "content_type": r.get("ContentType", "")}
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
            return None
        raise


def download(key: str, dst: Path) -> Path:
    dst = Path(dst); dst.parent.mkdir(parents=True, exist_ok=True)
    client().download_file(bucket(), key, str(dst))
    return dst


def upload(src: Path, key: str, content_type: str | None = None) -> str:
    ct = content_type or mimetypes.guess_type(str(src))[0] or "application/octet-stream"
    client().upload_file(str(src), bucket(), key, ExtraArgs={"ContentType": ct})
    return key


def put_bytes(data: bytes, key: str, content_type: str) -> str:
    client().put_object(Bucket=bucket(), Key=key, Body=data, ContentType=content_type)
    return key


def delete(*keys: str) -> None:
    keys = tuple(k for k in keys if k)
    if keys:
        client().delete_objects(Bucket=bucket(), Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True})


def delete_prefix(prefix: str) -> int:
    n = 0
    paginator = client().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket(), Prefix=prefix):
        keys = [o["Key"] for o in page.get("Contents", [])]
        if keys:
            client().delete_objects(Bucket=bucket(), Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True}); n += len(keys)
    return n


def ping() -> bool:
    client().head_bucket(Bucket=bucket())
    return True
