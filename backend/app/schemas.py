from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str = ""
    avatar: str = ""
    is_bot: bool = False


class UserOut(UserBrief):
    bio: str = ""
    is_admin: bool = False
    created_at: datetime
    followers: int = 0
    following: int = 0
    post_count: int = 0


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=20, pattern=r"^[A-Za-z0-9_\u4e00-\u9fa5]+$")
    password: str = Field(min_length=6, max_length=64)
    display_name: str = Field(default="", max_length=30)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileIn(BaseModel):
    display_name: str | None = Field(default=None, max_length=30)
    bio: str | None = Field(default=None, max_length=200)
    avatar: str | None = Field(default=None, max_length=300)


class PostIn(BaseModel):
    content: str = Field(default="", max_length=5000)
    media_url: str = Field(default="", max_length=300)
    media_type: str = Field(default="", max_length=20)


class CommentIn(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentOut(BaseModel):
    id: int
    user: UserBrief
    content: str
    status: str
    created_at: datetime


class PostOut(BaseModel):
    id: int
    author: UserBrief
    content: str
    media_url: str = ""
    media_type: str = ""
    status: str
    label: str
    score: float
    like_count: int
    comment_count: int
    created_at: datetime
    liked: bool = False


class PageOut(BaseModel):
    items: list[PostOut]
    total: int
    page: int
    size: int


class UploadOut(BaseModel):
    url: str
    media_type: str
    width: int = 0
    height: int = 0
    size: int = 0


class ModerationOut(BaseModel):
    id: int
    post: PostOut
    modality: str
    label: str
    score: float
    reason: str
    status: str
    created_at: datetime


class CampaignIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    target_post_id: int | None = None
    bot_count: int = Field(default=5, ge=1, le=50)
    actions: str = Field(default="like,comment", max_length=120)
    comment_text: str = Field(default="", max_length=300)
    interval_ms: int = Field(default=600, ge=100, le=5000)
    duration_s: int = Field(default=30, ge=5, le=600)


class CampaignOut(BaseModel):
    id: int
    name: str
    target_post_id: int | None
    bot_count: int
    actions: str
    comment_text: str
    interval_ms: int
    duration_s: int
    status: str
    actions_done: int
    created_at: datetime


class StatsOut(BaseModel):
    users: int
    bots: int
    posts: int
    pending: int
    rejected: int
    likes: int
    comments: int
    campaigns: int
    running_campaigns: int


class TextLabIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class VideoLabIn(BaseModel):
    video_url: str = ""
    rate: float = Field(default=1.0, ge=0.2, le=5.0)
