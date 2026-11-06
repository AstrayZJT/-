from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_optional_user
from ..models import Comment, Like, Post, User
from ..schemas import CommentIn, PostIn
from ..serializers import comment_out, post_out
from ..services import media, moderation, text_mod

router = APIRouter(prefix="/api", tags=["posts"])


@router.post("/upload")
async def upload(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    return await media.save_upload(file)


@router.get("/posts")
def list_posts(
    sort: str = Query("latest", pattern="^(latest|hot)$"),
    q: str = "",
    author_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    query = db.query(Post).filter(Post.status == "approved")
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(Post.content.like(like)))
    if author_id:
        query = query.filter(Post.author_id == author_id)
    total = query.count()
    if sort == "hot":
        score = func.coalesce(Post.like_count, 0) * 2 + func.coalesce(Post.comment_count, 0) * 3
        query = query.order_by(score.desc(), Post.created_at.desc())
    else:
        query = query.order_by(Post.created_at.desc())
    posts = query.offset((page - 1) * size).limit(size).all()
    return {
        "items": [post_out(db, p, current) for p in posts],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/posts/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db), current: User | None = Depends(get_optional_user)):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    post.view_count = (post.view_count or 0) + 1
    db.commit()
    return post_out(db, post, current)


@router.post("/posts")
def create_post(payload: PostIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not payload.content.strip() and not payload.media_url:
        raise HTTPException(status_code=400, detail="内容不能为空")
    post = Post(
        author_id=user.id,
        content=payload.content.strip(),
        media_url=payload.media_url,
        media_type=payload.media_type,
    )
    db.add(post)
    db.flush()
    try:
        moderation.moderate_post(db, post)
    except Exception as exc:  # 审核失败不阻断发帖，但要留痕
        post.status = "approved"
        post.label = "normal"
        print("moderation error:", exc)
    db.commit()
    db.refresh(post)
    return post_out(db, post, user)


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    if post.author_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="无权删除")
    db.delete(post)
    db.commit()
    return {"ok": True}


@router.post("/posts/{post_id}/like")
def toggle_like(post_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    existing = db.query(Like).filter(Like.user_id == user.id, Like.post_id == post_id).first()
    if existing:
        db.delete(existing)
        post.like_count = max(0, (post.like_count or 0) - 1)
        liked = False
    else:
        db.add(Like(user_id=user.id, post_id=post_id))
        post.like_count = (post.like_count or 0) + 1
        liked = True
    db.commit()
    return {"liked": liked, "like_count": post.like_count}


@router.get("/posts/{post_id}/comments")
def list_comments(post_id: int, db: Session = Depends(get_db)):
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id, Comment.status == "approved")
        .order_by(Comment.created_at.asc())
        .limit(100)
        .all()
    )
    return [comment_out(c) for c in comments]


@router.post("/posts/{post_id}/comments")
def add_comment(post_id: int, payload: CommentIn, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    pred = text_mod.predict(payload.content)
    status = "approved" if pred["label"] == "normal" else "rejected"
    comment = Comment(post_id=post_id, user_id=user.id, content=payload.content, status=status)
    db.add(comment)
    if status == "approved":
        post.comment_count = (post.comment_count or 0) + 1
    db.commit()
    db.refresh(comment)
    data = comment_out(comment)
    data["moderation"] = pred
    return data
