from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import Comment, Follow, Like, Post, User


def user_brief(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name or user.username,
        "avatar": user.avatar or "",
        "is_bot": bool(user.is_bot),
    }


def user_out(db: Session, user: User) -> dict:
    followers = db.query(func.count(Follow.id)).filter(Follow.following_id == user.id).scalar() or 0
    following = db.query(func.count(Follow.id)).filter(Follow.follower_id == user.id).scalar() or 0
    posts = db.query(func.count(Post.id)).filter(Post.author_id == user.id, Post.status == "approved").scalar() or 0
    return {
        **user_brief(user),
        "bio": user.bio or "",
        "is_admin": bool(user.is_admin),
        "created_at": user.created_at.isoformat() + "Z",
        "followers": followers,
        "following": following,
        "post_count": posts,
    }


def post_out(db: Session, post: Post, current: User | None = None) -> dict:
    liked = False
    if current is not None:
        liked = db.query(Like.id).filter(Like.user_id == current.id, Like.post_id == post.id).first() is not None
    return {
        "id": post.id,
        "author": user_brief(post.author),
        "content": post.content or "",
        "media_url": post.media_url or "",
        "media_type": post.media_type or "",
        "status": post.status,
        "label": post.label,
        "score": round(float(post.score or 0), 4),
        "like_count": post.like_count or 0,
        "comment_count": post.comment_count or 0,
        "created_at": post.created_at.isoformat() + "Z",
        "liked": liked,
    }


def comment_out(comment: Comment) -> dict:
    return {
        "id": comment.id,
        "user": user_brief(comment.user),
        "content": comment.content,
        "status": comment.status,
        "created_at": comment.created_at.isoformat() + "Z",
    }
