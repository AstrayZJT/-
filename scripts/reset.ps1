# 清空数据库并重新灌入演示数据
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Remove-Item "data\app.db" -Force -ErrorAction SilentlyContinue
Remove-Item "data\uploads\images\*" -Force -ErrorAction SilentlyContinue
Remove-Item "data\uploads\videos\*" -Force -ErrorAction SilentlyContinue
Remove-Item "data\uploads\lab\*" -Force -ErrorAction SilentlyContinue

& .venv\Scripts\python.exe -c "from backend.app.seed import seed_if_empty; print('seeded:', seed_if_empty())"
Write-Host "已重置。启动： .\scripts\run.ps1"
