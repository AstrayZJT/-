from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.config import DEMO_MODE, UPLOAD_DIR  # noqa: E402
from backend.app.db import init_db  # noqa: E402
from backend.app.routers import admin, auth, posts, users  # noqa: E402
from backend.app.seed import ensure_demo_assets, seed_if_empty  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_demo_assets()
    if DEMO_MODE:
        try:
            seed_if_empty()
        except Exception as exc:  # 种子失败不阻止启动
            print("seed skipped:", exc)
    yield
    for task in list(admin._tasks):
        task.cancel()


app = FastAPI(title="SocialSim 社交网络拟真平台", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000",
                   "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(admin.router)

app.mount("/media", StaticFiles(directory=str(UPLOAD_DIR)), name="media")


@app.get("/api/health")
def health():
    return {"status": "ok", "demo": DEMO_MODE}


DIST = BASE_DIR / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not Found")
        candidate = DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html")
