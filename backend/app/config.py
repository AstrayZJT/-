from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
IMAGE_DIR = UPLOAD_DIR / "images"
VIDEO_DIR = UPLOAD_DIR / "videos"
LAB_DIR = UPLOAD_DIR / "lab"
DEMO_DIR = DATA_DIR / "demo"
MODEL_DIR = BASE_DIR / "ml" / "weights"
SEED_DIR = DATA_DIR / "seed"

for _p in (DATA_DIR, UPLOAD_DIR, IMAGE_DIR, VIDEO_DIR, LAB_DIR, DEMO_DIR, MODEL_DIR, SEED_DIR):
    _p.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

SECRET_KEY = os.environ.get("SOCIALSIM_SECRET", "social-sim-course-project-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

MAX_UPLOAD_MB = 60
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_VIDEO_EXT = {".mp4", ".webm", ".mov", ".avi"}

# 演示模式：关闭后不写入演示数据
DEMO_MODE = os.environ.get("SOCIALSIM_DEMO", "1") == "1"
