# 一键安装依赖 + 生成数据 + 训练模型
param(
    [string]$Mirror = "https://pypi.tuna.tsinghua.edu.cn/simple"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[1/5] 创建虚拟环境"
    python -m venv .venv
}

Write-Host "[2/5] 安装 Python 依赖"
& .venv\Scripts\python.exe -m pip install --upgrade pip -i $Mirror
& .venv\Scripts\python.exe -m pip install -r requirements.txt -i $Mirror

if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "[3/5] 构建前端"
    Push-Location frontend
    $env:npm_config_cache = "$root\frontend\.npm-cache"
    npm install --registry=https://registry.npmmirror.com --no-audit --no-fund
    $env:TEMP = "$root\.tmp"; $env:TMP = "$root\.tmp"
    New-Item -ItemType Directory -Force "$root\.tmp" | Out-Null
    npm run build
    Pop-Location
} else {
    Write-Host "[3/5] 未找到 npm，跳过前端构建（可先用 5173 开发模式）"
}

Write-Host "[4/5] 生成合成数据"
& .venv\Scripts\python.exe ml/generate_data.py

Write-Host "[5/5] 训练文本与图像模型（CPU 约 2-5 分钟）"
& .venv\Scripts\python.exe ml/train_text.py
& .venv\Scripts\python.exe ml/train_image.py
& .venv\Scripts\python.exe ml/eval_video.py
& .venv\Scripts\python.exe ml/export_demo.py

Write-Host "完成。运行 .\scripts\run.ps1 启动。"
