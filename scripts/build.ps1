# 构建前端
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\frontend"
$env:npm_config_cache = "$root\frontend\.npm-cache"
$env:TEMP = "$root\.tmp"; $env:TMP = "$root\.tmp"
New-Item -ItemType Directory -Force "$root\.tmp" | Out-Null
npm install --registry=https://registry.npmmirror.com --no-audit --no-fund
npm run build
