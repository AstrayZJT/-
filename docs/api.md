# API 速查

启动后访问 `/docs` 可查看交互式 Swagger 文档。所有 `/api/admin/*` 接口需要管理员令牌。

## 认证

```http
POST /api/auth/register
{"username": "demo", "password": "demo123", "display_name": "演示"}

POST /api/auth/login
{"username": "admin", "password": "admin123"}
→ {"access_token": "...", "token_type": "bearer", "user": {...}}
```

后续请求带 `Authorization: Bearer <token>`。

## 社交

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/posts?sort=latest|hot&page=1&size=10&q=` | 信息流 |
| POST | `/api/posts` | `{content, media_url, media_type}` |
| GET | `/api/posts/{id}` | 详情 |
| POST | `/api/posts/{id}/like` | 点赞切换 |
| GET/POST | `/api/posts/{id}/comments` | 评论 |
| POST | `/api/upload` | multipart `file` |
| GET | `/api/users/{id}` | 主页 |
| POST/DELETE | `/api/users/{id}/follow` | 关注 |

## 管理

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/admin/stats` | 统计 |
| GET | `/api/admin/moderation?status=pending` | 队列 |
| POST | `/api/admin/moderation/{id}/review` | `{"action":"approve"|"reject"}` |
| POST | `/api/admin/bots` | `{"count": 20}` |
| POST | `/api/admin/campaigns` | `{name,target_post_id,bot_count,actions,comment_text,interval_ms,duration_s}` |
| GET | `/api/admin/campaigns/{id}` | 详情 + 曲线 |
| GET/PUT | `/api/admin/settings` | 防御等级 0/1/2 |
| POST | `/api/admin/lab/text` | `{text}` |
| POST | `/api/admin/lab/image` | multipart `file` + `eps` |
| POST | `/api/admin/lab/video` | `{video_url, rate}` |
| GET | `/api/admin/lab/metrics` | 训练指标 |
