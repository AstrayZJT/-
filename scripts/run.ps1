# 启动演示（单端口 8000）
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "未找到虚拟环境，请先运行 .\scripts\setup.ps1"
}
if (-not (Test-Path "frontend\dist\index.html")) {
    Write-Host "未找到前端构建产物，先执行构建……"
    & "$PSScriptRoot\build.ps1"
}

Write-Host "SocialSim 启动中： http://127.0.0.1:8000"
Start-Process "http://127.0.0.1:8000"
& .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
