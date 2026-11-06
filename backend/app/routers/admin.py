from __future__ import annotations

import asyncio
import json
import random
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import BASE_DIR, DEMO_DIR, LAB_DIR
from ..db import get_db
from ..deps import require_admin
from ..models import BotAction, BotCampaign, Comment, LabRun, Like, ModerationTask, Post, User
from ..schemas import CampaignIn, TextLabIn, VideoLabIn
from ..serializers import post_out, user_out
from ..services import bot_engine, image_mod, settings, text_mod, video_mod
from ..services.media import url_to_path

router = APIRouter(prefix="/api/admin", tags=["admin"])

_tasks: set[asyncio.Task] = set()


def _start(coro) -> None:
    task = asyncio.create_task(coro)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


def ensure_bots(db: Session, n: int) -> list[User]:
    bots = db.query(User).filter(User.is_bot.is_(True)).order_by(User.id).all()
    while len(bots) < n:
        suffix = uuid.uuid4().hex[:6]
        bot = User(
            username=f"bot_{suffix}",
            password_hash="!",
            display_name=f"网友{suffix[:4]}",
            is_bot=True,
            bio="自动生成的演示账号",
        )
        db.add(bot)
        bots.append(bot)
    db.commit()
    return bots[:n]


@router.get("/stats")
def stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return {
        "users": db.query(func.count(User.id)).filter(User.is_bot.is_(False)).scalar() or 0,
        "bots": db.query(func.count(User.id)).filter(User.is_bot.is_(True)).scalar() or 0,
        "posts": db.query(func.count(Post.id)).scalar() or 0,
        "pending": db.query(func.count(Post.id)).filter(Post.status == "pending").scalar() or 0,
        "rejected": db.query(func.count(Post.id)).filter(Post.status == "rejected").scalar() or 0,
        "likes": db.query(func.count(Like.id)).scalar() or 0,
        "comments": db.query(func.count(Comment.id)).scalar() or 0,
        "campaigns": db.query(func.count(BotCampaign.id)).scalar() or 0,
        "running_campaigns": db.query(func.count(BotCampaign.id)).filter(
            BotCampaign.status == "running").scalar() or 0,
    }


@router.get("/users")
def list_users(bot: bool | None = None, q: str = "", limit: int = 50,
               db: Session = Depends(get_db), _: User = Depends(require_admin)):
    query = db.query(User)
    if bot is not None:
        query = query.filter(User.is_bot.is_(bot))
    if q:
        like = f"%{q}%"
        query = query.filter(User.username.like(like) | User.display_name.like(like))
    users = query.order_by(User.created_at.desc()).limit(limit).all()
    return [user_out(db, u) for u in users]


@router.post("/bots")
def create_bots(payload: dict, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    n = int(payload.get("count", 5))
    n = max(1, min(n, 50))
    bots = ensure_bots(db, n)
    return {"created": n, "total_bots": len(bots)}


@router.get("/moderation")
def moderation_queue(status: str = "pending", limit: int = 50,
                     db: Session = Depends(get_db), _: User = Depends(require_admin)):
    query = db.query(ModerationTask)
    if status:
        query = query.filter(ModerationTask.status == status)
    tasks = query.order_by(ModerationTask.created_at.desc()).limit(limit).all()
    items = []
    for t in tasks:
        post = db.get(Post, t.post_id)
        if post is None:
            continue
        items.append({
            "id": t.id,
            "post": post_out(db, post),
            "modality": t.modality,
            "label": t.label,
            "score": round(float(t.score or 0), 4),
            "reason": t.reason,
            "status": t.status,
            "created_at": t.created_at.isoformat() + "Z",
        })
    return items


@router.post("/moderation/{task_id}/review")
def review(task_id: int, payload: dict, db: Session = Depends(get_db),
           admin: User = Depends(require_admin)):
    action = payload.get("action")
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action 只能是 approve/reject")
    task = db.get(ModerationTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    post = db.get(Post, task.post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    for t in db.query(ModerationTask).filter(ModerationTask.post_id == post.id).all():
        t.status = "approved" if action == "approve" else "rejected"
        t.reviewed_by = admin.id
    post.status = "approved" if action == "approve" else "rejected"
    db.commit()
    return {"ok": True, "post_status": post.status}


@router.get("/settings")
def get_settings(_: User = Depends(require_admin)):
    data = settings.get_settings()
    return {**data, "levels": settings.LEVELS}


@router.put("/settings")
def put_settings(payload: dict, _: User = Depends(require_admin)):
    level = int(payload.get("defense_level", 0))
    if level not in settings.LEVELS:
        raise HTTPException(status_code=400, detail="防御等级只能是 0/1/2")
    return {**settings.update_settings(defense_level=level), "levels": settings.LEVELS}


@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.query(BotCampaign).order_by(BotCampaign.created_at.desc()).limit(30).all()
    return [{
        "id": c.id, "name": c.name, "target_post_id": c.target_post_id,
        "bot_count": c.bot_count, "actions": c.actions, "comment_text": c.comment_text,
        "interval_ms": c.interval_ms, "duration_s": c.duration_s, "status": c.status,
        "actions_done": c.actions_done, "created_at": c.created_at.isoformat() + "Z",
    } for c in rows]


@router.post("/campaigns")
async def create_campaign(payload: CampaignIn, db: Session = Depends(get_db),
                          _: User = Depends(require_admin)):
    if payload.target_post_id is not None and db.get(Post, payload.target_post_id) is None:
        raise HTTPException(status_code=404, detail="目标帖子不存在")
    if payload.bot_count > db.query(func.count(User.id)).filter(User.is_bot.is_(True)).scalar():
        ensure_bots(db, payload.bot_count)
    campaign = BotCampaign(
        name=payload.name,
        target_post_id=payload.target_post_id,
        bot_count=payload.bot_count,
        actions=payload.actions,
        comment_text=payload.comment_text,
        interval_ms=payload.interval_ms,
        duration_s=payload.duration_s,
        status="running",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    _start(bot_engine.run_campaign(campaign.id))
    return {"id": campaign.id, "status": campaign.status}


@router.get("/campaigns/{campaign_id}")
def campaign_detail(campaign_id: int, db: Session = Depends(get_db),
                    _: User = Depends(require_admin)):
    campaign = db.get(BotCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    target = db.get(Post, campaign.target_post_id) if campaign.target_post_id else None
    actions = (
        db.query(BotAction)
        .filter(BotAction.campaign_id == campaign_id)
        .order_by(BotAction.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "id": campaign.id, "name": campaign.name, "status": campaign.status,
        "bot_count": campaign.bot_count, "actions": campaign.actions,
        "actions_done": campaign.actions_done, "duration_s": campaign.duration_s,
        "target": post_out(db, target) if target else None,
        "series": bot_engine.campaign_series(db, campaign_id),
        "recent_actions": [{
            "bot_id": a.bot_id, "action": a.action, "post_id": a.post_id,
            "time": a.created_at.isoformat() + "Z",
        } for a in actions],
    }


@router.post("/campaigns/{campaign_id}/stop")
def stop_campaign(campaign_id: int, db: Session = Depends(get_db),
                  _: User = Depends(require_admin)):
    campaign = db.get(BotCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    campaign.status = "stopped"
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ lab
@router.post("/lab/text")
def lab_text(payload: TextLabIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    raw = text_mod.predict_raw(payload.text)
    normalized = text_mod.predict(payload.text)
    robust = text_mod.predict_robust(payload.text)
    variants = []
    for v in text_mod.make_variants(payload.text, n=5):
        r = text_mod.predict_raw(v["text"])
        n = text_mod.predict(v["text"])
        b = text_mod.predict_robust(v["text"])
        variants.append({
            "type": v["type"], "text": v["text"],
            "raw": r, "normalized": n, "robust": b,
            "evaded": r["label"] == "normal",
        })
    result = {
        "text": payload.text,
        "raw": raw, "normalized": normalized, "robust": robust,
        "variants": variants,
        "defense_level": settings.get_settings().get("defense_level", 0),
    }
    db.add(LabRun(kind="text", mode="attack", params=json.dumps({"text": payload.text}, ensure_ascii=False),
                  result=json.dumps(result, ensure_ascii=False)))
    db.commit()
    return result


@router.post("/lab/image")
async def lab_image(
    file: UploadFile = File(...),
    eps: float = Form(24 / 255),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    content = await file.read()
    ext = Path(file.filename or "x.png").suffix.lower() or ".png"
    src = LAB_DIR / f"orig_{uuid.uuid4().hex}{ext}"
    src.write_bytes(content)
    try:
        result = image_mod.run_attack(src, eps=eps)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"图片处理失败：{exc}")
    if result.get("error"):
        raise HTTPException(status_code=503, detail=result["error"])
    adv: "object" = result.pop("adv_image")
    adv_path = LAB_DIR / f"adv_{src.stem}{ext}"
    adv.save(adv_path)
    # 对抗训练模型的判断
    robust_pred = image_mod.predict_image(adv_path, adv=True)
    payload = {
        **result,
        "orig_url": f"/media/lab/{src.name}",
        "adv_url": f"/media/lab/{adv_path.name}",
        "robust": robust_pred,
        "eps": eps,
    }
    db.add(LabRun(kind="image", mode="attack", params=json.dumps({"eps": eps}, ensure_ascii=False),
                  result=json.dumps({k: v for k, v in payload.items() if k != "adv_image"},
                                    ensure_ascii=False)))
    db.commit()
    return payload


@router.post("/lab/video")
def lab_video(payload: VideoLabIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if payload.video_url:
        path = url_to_path(payload.video_url)
        if path is None:
            raise HTTPException(status_code=404, detail="视频不存在")
    else:
        path = DEMO_DIR / "ad_gap.mp4"
    if not path.exists():
        raise HTTPException(status_code=503, detail="演示视频尚未生成，请先运行 ml/generate_data.py")
    fixed = video_mod.analyze(path, rate=payload.rate, start=0.0)
    dense = video_mod.analyze(path, rate=0.4, start=0.1)
    result = {
        "file": path.name,
        "fixed": fixed,
        "dense": dense,
        "fixed_detected": bool(fixed.get("violations")),
        "dense_detected": bool(dense.get("violations")),
    }
    db.add(LabRun(kind="video", mode="attack", params=json.dumps(payload.model_dump(), ensure_ascii=False),
                  result=json.dumps(result, ensure_ascii=False)))
    db.commit()
    return result


@router.get("/lab/metrics")
def lab_metrics(_: User = Depends(require_admin)):
    out = {}
    for key in ("text_metrics", "image_metrics", "video_metrics"):
        f = BASE_DIR / "ml" / "weights" / f"{key}.json"
        out[key] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    out["settings"] = settings.get_settings()
    return out
