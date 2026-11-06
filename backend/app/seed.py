from __future__ import annotations

import random
import shutil
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func

from .config import BASE_DIR, DEMO_DIR, IMAGE_DIR, VIDEO_DIR
from .db import SessionLocal, init_db
from .models import Comment, Follow, Like, ModerationTask, Post, User
from .security import hash_password

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

random.seed(20261106)

NORMAL_TEXTS = [
    "今天天气真好，去操场走了两圈，顺便拍了几张照片。",
    "食堂的牛肉面又涨价了，但是味道确实不错。",
    "图书馆三楼空调太冷，来自习记得带件外套。",
    "周末去秦岭爬山，山顶风很大，风景是真的好。",
    "刚交完实验报告，终于可以睡个好觉了。",
    "有人晚上一起打羽毛球吗？老地方集合。",
    "新买的耳机音质一般，准备退了换一个。",
    "组会开到十点，人都麻了，求推荐提神方法。",
    "校门口新开了一家奶茶店，排队的人好多。",
    "求推荐一门好过的选修课，这学期想轻松点。",
    "今天代码终于跑通了，记录一下这个时刻。",
    "宿舍楼下的猫又胖了一圈，估计被喂习惯了。",
    "早八真的起不来，谁懂啊。",
    "最近在学强化学习，头有点大，但挺有意思。",
    "操场跑步五公里，配速终于进六了。",
    "食堂新出的麻辣香锅味道不错，推荐。",
    "实验室的服务器又崩了，心态有点爆炸。",
    "晚上去看了一场电影，剧情一般，爆米花好吃。",
    "西安的秋天很短，抓紧时间拍照。",
    "和室友一起做了顿火锅，幸福感拉满。",
]

AD_TEXTS = [
    "加微信 abc123 兼职日结，一天300，名额有限！",
    "低价出二手自行车，九成新，加V详聊。",
    "扫码进群领考研资料，全程免费，先到先得。",
    "专业代写课程设计，价格美丽，加微信私聊。",
    "日结兼职，动动手指就能赚钱，加薇信了解。",
]

ABUSE_TEXTS = ["你就是个傻X，别在这丢人现眼了。", "滚开，别烦我，垃圾东西。"]

USERS = [
    ("linxiaoyu", "林小雨", "爱拍照，爱跑步，偶尔写点代码。"),
    ("zhanghao", "张浩", "计算机学院大三，方向是 CV。"),
    ("wangmeng", "王梦", "新闻系，喜欢记录校园生活。"),
    ("chenxi", "陈曦", "光电学院，最近在做实验。"),
    ("liuyang", "刘洋", "研一，摸鱼选手。"),
    ("sunqi", "孙琪", "喜欢猫和火锅。"),
    ("zhaolei", "赵磊", "篮球、摄影、咖啡。"),
    ("huangyue", "黄悦", "外语学院，正在准备雅思。"),
    ("zhouwen", "周文", "机械专业，偶尔剪视频。"),
    ("wujia", "吴佳", "每天都在赶 due。"),
    ("xulei", "徐磊", "宿舍宅，游戏高手。"),
    ("hejing", "何静", "喜欢看书和散步。"),
]


def _make_image(kind: str) -> str:
    from ml.generate_data import ad_image, normal_image

    img = ad_image() if kind == "ad" else normal_image()
    name = f"{uuid.uuid4().hex}.jpg"
    img.save(IMAGE_DIR / name, quality=92)
    return f"/media/images/{name}"


def _copy_video(src: Path) -> str:
    name = f"{uuid.uuid4().hex}{src.suffix}"
    shutil.copyfile(src, VIDEO_DIR / name)
    return f"/media/videos/{name}"


def ensure_demo_assets() -> None:
    """把 data/demo 里的演示素材复制到可访问的 uploads/demo。"""
    target = VIDEO_DIR.parent / "demo"
    target.mkdir(parents=True, exist_ok=True)
    for f in DEMO_DIR.glob("*"):
        if f.is_file() and not (target / f.name).exists():
            shutil.copyfile(f, target / f.name)


def seed_if_empty() -> bool:
    init_db()
    ensure_demo_assets()
    with SessionLocal() as db:
        if (db.query(func.count(User.id)).scalar() or 0) > 0:
            return False

        admin = User(username="admin", display_name="平台管理员", password_hash=hash_password("admin123"),
                     is_admin=True, bio="内容安全运营")
        db.add(admin)

        users: list[User] = []
        for i, (name, display, bio) in enumerate(USERS):
            u = User(username=name, display_name=display, password_hash=hash_password("user123"),
                     bio=bio)
            db.add(u)
            users.append(u)

        bots = []
        for i in range(8):
            b = User(username=f"bot_seed{i}", display_name=f"网友{i:02d}", password_hash="!",
                     is_bot=True, bio="自动生成的演示账号")
            db.add(b)
            bots.append(b)
        db.commit()

        now = datetime.utcnow()
        posts: list[Post] = []
        for i, text in enumerate(NORMAL_TEXTS):
            author = users[i % len(users)]
            media_url, media_type = "", ""
            if i % 5 == 0:
                media_url, media_type = _make_image("normal"), "image"
            post = Post(author_id=author.id, content=text, media_url=media_url, media_type=media_type,
                        status="approved", label="normal",
                        created_at=now - timedelta(minutes=len(NORMAL_TEXTS) - i))
            db.add(post)
            posts.append(post)
        db.commit()

        # 待审核的广告/辱骂内容，让管理后台一打开就有队列
        for i, text in enumerate(AD_TEXTS):
            author = users[(i + 3) % len(users)]
            media_url, media_type = "", ""
            if i % 2 == 0:
                media_url, media_type = _make_image("ad"), "image"
            post = Post(author_id=author.id, content=text, media_url=media_url, media_type=media_type,
                        status="pending", label="ad", score=0.93,
                        created_at=now - timedelta(minutes=5 - i))
            db.add(post)
            db.flush()
            db.add(ModerationTask(post_id=post.id, modality="text", label="ad", score=0.93,
                                  reason="文本审核：广告导流（0.93）", status="pending"))
            if media_url:
                db.add(ModerationTask(post_id=post.id, modality="image", label="ad", score=0.88,
                                      reason="图片审核：广告导流（0.88）", status="pending"))
            posts.append(post)

        for i, text in enumerate(ABUSE_TEXTS):
            post = Post(author_id=users[(i + 5) % len(users)].id, content=text,
                        status="pending", label="abuse", score=0.9,
                        created_at=now - timedelta(minutes=2))
            db.add(post)
            db.flush()
            db.add(ModerationTask(post_id=post.id, modality="text", label="abuse", score=0.9,
                                  reason="文本审核：辱骂攻击（0.90）", status="pending"))
            posts.append(post)

        # 两段演示视频：一段违规落在采样间隙（基线漏过），一段落在整数秒（基线命中）
        gap = DEMO_DIR / "ad_gap.mp4"
        hit = DEMO_DIR / "ad_hit.mp4"
        if gap.exists():
            post = Post(author_id=users[6].id, content="随手拍的校园 vlog，看看晚霞。",
                        media_url=_copy_video(gap), media_type="video", status="approved",
                        label="normal", created_at=now - timedelta(minutes=1))
            db.add(post)
            posts.append(post)
        if hit.exists():
            post = Post(author_id=users[7].id, content="今天的校园日常。",
                        media_url=_copy_video(hit), media_type="video", status="pending",
                        label="ad", score=0.86, created_at=now - timedelta(minutes=1))
            db.add(post)
            db.flush()
            db.add(ModerationTask(post_id=post.id, modality="video", label="ad", score=0.86,
                                  reason="视频审核：第 3.0s 检出广告画面", status="pending"))
            posts.append(post)

        db.commit()

        # 互动数据
        for post in posts[:18]:
            lovers = random.sample(users, k=random.randint(2, 8))
            for u in lovers:
                db.add(Like(user_id=u.id, post_id=post.id))
            post.like_count = len(lovers)
            for _ in range(random.randint(0, 3)):
                u = random.choice(users)
                db.add(Comment(post_id=post.id, user_id=u.id, content="说得对，支持一下。"))
                post.comment_count = (post.comment_count or 0) + 1
        for u in users:
            for target in random.sample(users, k=random.randint(1, 3)):
                if target.id != u.id:
                    db.add(Follow(follower_id=u.id, following_id=target.id))
        db.commit()
        print("seed done:", len(users), "users,", len(posts), "posts")
        return True
