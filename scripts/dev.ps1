# 前端开发模式：后端 8000 + Vite 5173
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"
Write-Host "后端 http://127.0.0.1:8000 ，前端 http://127.0.0.1:5173"
