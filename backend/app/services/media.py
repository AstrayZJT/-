from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image

from ..config import ALLOWED_IMAGE_EXT, ALLOWED_VIDEO_EXT, IMAGE_DIR, MAX_UPLOAD_MB, VIDEO_DIR


async def save_upload(file: UploadFile) -> dict:
    ext = Path(file.filename or "").suffix.lower()
    content = await file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"文件不能超过 {MAX_UPLOAD_MB}MB")

    if ext in ALLOWED_IMAGE_EXT:
        target = IMAGE_DIR / f"{uuid.uuid4().hex}{ext}"
        target.write_bytes(content)
        try:
            with Image.open(target) as img:
                width, height = img.size
        except Exception:
            target.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="图片格式无法识别")
        return {"url": f"/media/images/{target.name}", "media_type": "image",
                "width": width, "height": height, "size": len(content)}

    if ext in ALLOWED_VIDEO_EXT:
        target = VIDEO_DIR / f"{uuid.uuid4().hex}{ext}"
        target.write_bytes(content)
        return {"url": f"/media/videos/{target.name}", "media_type": "video",
                "width": 0, "height": 0, "size": len(content)}

    raise HTTPException(status_code=400, detail="仅支持 png/jpg/webp/gif 或 mp4/webm/mov/avi")


def url_to_path(url: str) -> Path | None:
    if not url.startswith("/media/"):
        return None
    rel = url.removeprefix("/media/")
    base = IMAGE_DIR.parent
    path = (base / rel).resolve()
    if base.resolve() not in path.parents:
        return None
    return path if path.exists() else None
