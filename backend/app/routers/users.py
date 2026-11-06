from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_optional_user
from ..models import Follow, Post, User
from ..schemas import PostOut
from ..serializers import post_out, user_out

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), current: User | None = Depends(get_optional_user)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    data = user_out(db, user)
    data["is_following"] = bool(
        current and db.query(Follow.id).filter(Follow.follower_id == current.id,
                                               Follow.following_id == user.id).first()
    )
    return data


@router.get("/{user_id}/posts", response_model=list[PostOut])
def get_user_posts(user_id: int, db: Session = Depends(get_db),
                   current: User | None = Depends(get_optional_user)):
    posts = (
        db.query(Post)
        .filter(Post.author_id == user_id, Post.status == "approved")
        .order_by(Post.created_at.desc())
        .limit(50)
        .all()
    )
    return [post_out(db, p, current) for p in posts]


@router.post("/{user_id}/follow")
def follow(user_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="不能关注自己")
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    exists = db.query(Follow).filter(Follow.follower_id == current.id,
                                     Follow.following_id == user_id).first()
    if exists is None:
        db.add(Follow(follower_id=current.id, following_id=user_id))
        db.commit()
    return {"following": True}


@router.delete("/{user_id}/follow")
def unfollow(user_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    db.query(Follow).filter(Follow.follower_id == current.id, Follow.following_id == user_id).delete()
    db.commit()
    return {"following": False}
