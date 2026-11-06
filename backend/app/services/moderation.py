from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import ModerationTask, Post
from . import image_mod, settings, text_mod, video_mod
from .media import url_to_path

PRIORITY = {"normal": 0, "ad": 1, "abuse": 2}


def _add_task(db: Session, post: Post, modality: str, pred: dict, reason: str) -> None:
    label = pred.get("label", "normal")
    score = float(pred.get("score", 0.0))
    status = "approved" if label == "normal" else "pending"
    db.add(
        ModerationTask(
            post_id=post.id,
            modality=modality,
            label=label,
            score=score,
            reason=reason,
            status=status,
        )
    )


def moderate_post(db: Session, post: Post) -> None:
    level = int(settings.get_settings().get("defense_level", 0))
    best_label, best_score = "normal", 0.0

    text = (post.content or "").strip()
    if text:
        if level == 0:
            pred = text_mod.predict_raw(text)
        elif level == 1:
            pred = text_mod.predict(text)
        else:
            pred = text_mod.predict_robust(text)
        _add_task(db, post, "text", pred, f"文本审核：{pred.get('label_zh', '')}（{pred.get('score', 0):.2f}）")
        if PRIORITY.get(pred["label"], 0) > PRIORITY.get(best_label, 0):
            best_label, best_score = pred["label"], float(pred["score"])

    if post.media_type == "image" and post.media_url:
        path = url_to_path(post.media_url)
        if path:
            pred = image_mod.predict_image(path, adv=(level >= 2))
            _add_task(db, post, "image", pred, f"图片审核：{pred.get('label_zh', '')}（{pred.get('score', 0):.2f}）")
            if PRIORITY.get(pred["label"], 0) > PRIORITY.get(best_label, 0):
                best_label, best_score = pred["label"], float(pred["score"])

    if post.media_type == "video" and post.media_url:
        path = url_to_path(post.media_url)
        if path:
            rate = 0.4 if level >= 2 else 1.0
            result = video_mod.analyze(path, rate=rate)
            violations = result.get("violations", [])
            if violations:
                v = violations[0]
                pred = {"label": "ad", "score": float(v.get("score", 0.8)),
                        "label_zh": "广告导流"}
                reason = f"视频审核：第 {v.get('start')}s 检出广告画面（采样间隔 {rate}s）"
            else:
                pred = {"label": "normal", "score": 0.9, "label_zh": "正常"}
                reason = f"视频审核：未检出违规（采样间隔 {rate}s，共 {len(result.get('samples', []))} 帧）"
            _add_task(db, post, "video", pred, reason)
            if PRIORITY.get(pred["label"], 0) > PRIORITY.get(best_label, 0):
                best_label, best_score = pred["label"], float(pred["score"])

    post.label = best_label
    post.score = best_score
    post.status = "pending" if best_label != "normal" else "approved"
