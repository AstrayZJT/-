from __future__ import annotations

import asyncio
import random
from datetime import datetime

from sqlalchemy import func

from ..db import SessionLocal
from ..models import BotAction, BotCampaign, Comment, Follow, Like, Post, User
from .moderation import moderate_post

BOT_POSTS = [
    "加薇信 abc123 兼职日结，一天300",
    "低·价出二手自行车，加V详聊",
    "扫码进群领资料，名额有限",
    "曰结兼职，动动手指就能赚钱",
    "专业代写课程设计，价格美丽",
    "高薪兼职，日入500，私聊",
]
BOT_COMMENTS = ["说得好，支持一下", "这个必须顶", "同感，转发一下", "真的假的？", "已关注，期待更新"]

_running: set[int] = set()


def _pick_bots(db, n: int) -> list[User]:
    return db.query(User).filter(User.is_bot.is_(True)).order_by(User.id).limit(n).all()


def _do_like(db, bot: User, post: Post | None) -> bool:
    if post is None:
        return False
    exists = db.query(Like).filter(Like.user_id == bot.id, Like.post_id == post.id).first()
    if exists:
        return False
    db.add(Like(user_id=bot.id, post_id=post.id))
    post.like_count = (post.like_count or 0) + 1
    return True


def _do_comment(db, bot: User, post: Post | None, text: str) -> bool:
    if post is None:
        return False
    db.add(Comment(post_id=post.id, user_id=bot.id, content=text or random.choice(BOT_COMMENTS)))
    post.comment_count = (post.comment_count or 0) + 1
    return True


def _do_post(db, bot: User) -> Post:
    post = Post(author_id=bot.id, content=random.choice(BOT_POSTS), status="pending")
    db.add(post)
    db.flush()
    if post.id:
        moderate_post(db, post)
    return post


def _do_follow(db, bot: User, post: Post | None) -> bool:
    if post is None:
        return False
    exists = db.query(Follow).filter(
        Follow.follower_id == bot.id, Follow.following_id == post.author_id
    ).first()
    if exists:
        return False
    db.add(Follow(follower_id=bot.id, following_id=post.author_id))
    return True


async def run_campaign(campaign_id: int) -> None:
    if campaign_id in _running:
        return
    _running.add(campaign_id)
    started = datetime.utcnow()
    try:
        # 读取配置
        with SessionLocal() as db:
            campaign = db.get(BotCampaign, campaign_id)
            if campaign is None:
                return
            actions = [a.strip() for a in campaign.actions.split(",") if a.strip()]
            interval = campaign.interval_ms / 1000
            duration = campaign.duration_s
            bot_count = campaign.bot_count
            target_id = campaign.target_post_id
            comment_text = campaign.comment_text

        i = 0
        while (datetime.utcnow() - started).total_seconds() < duration:
            with SessionLocal() as db:
                campaign = db.get(BotCampaign, campaign_id)
                if campaign is None or campaign.status != "running":
                    break
                bots = _pick_bots(db, bot_count)
                if not bots:
                    campaign.status = "failed"
                    campaign.finished_at = datetime.utcnow()
                    db.commit()
                    break
                bot = bots[i % len(bots)]
                action = actions[i % len(actions)] if actions else "like"
                target = db.get(Post, target_id) if target_id else None
                done = False
                if action == "like":
                    done = _do_like(db, bot, target)
                elif action == "comment":
                    done = _do_comment(db, bot, target, comment_text)
                elif action == "post":
                    _do_post(db, bot)
                    done = True
                elif action == "follow":
                    done = _do_follow(db, bot, target)
                if done:
                    db.add(BotAction(campaign_id=campaign_id, bot_id=bot.id, action=action,
                                     post_id=target.id if target else None))
                    campaign.actions_done = (campaign.actions_done or 0) + 1
                db.commit()
            i += 1
            await asyncio.sleep(max(0.05, interval))

        with SessionLocal() as db:
            campaign = db.get(BotCampaign, campaign_id)
            if campaign and campaign.status == "running":
                campaign.status = "done"
                campaign.finished_at = datetime.utcnow()
                db.commit()
    finally:
        _running.discard(campaign_id)


def campaign_series(db, campaign_id: int, bucket_s: int = 1) -> list[dict]:
    rows = (
        db.query(BotAction.created_at)
        .filter(BotAction.campaign_id == campaign_id)
        .all()
    )
    if not rows:
        return []
    agg: dict[int, int] = {}
    for (ts,) in rows:
        bucket = int(ts.timestamp() // bucket_s) * bucket_s
        agg[bucket] = agg.get(bucket, 0) + 1
    base = min(agg)
    return [
        {"t": bucket - base, "count": count}
        for bucket, count in sorted(agg.items())
    ]
