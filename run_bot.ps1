<#
    NoneBot2 QQ机器人启动脚本（PowerShell版本）
    功能：自动检查Python环境、创建虚拟环境、安装依赖并运行机器人
#>

$ErrorActionPreference = "Stop"

# 设置编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "====================================" -ForegroundColor Cyan
Write-Host " NoneBot2 QQ机器人启动脚本 " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "找到Python环境：" -NoNewline
    Write-Host $pythonVersion -ForegroundColor Green
    Write-Host
}
catch {
    Write-Host "错误：未安装Python 3.9+" -ForegroundColor Red
    Write-Host "请先安装Python 3.9或更高版本，然后重新运行此脚本"
    Write-Host
    Read-Host "按Enter键退出"
    exit 1
}

# 检查Python版本
$versionMatch = [regex]::Match($pythonVersion, 'Python (\d+)\.(\d+)\.(\d+)')
if ($versionMatch.Success) {
    $major = [int]$versionMatch.Groups[1].Value
    $minor = [int]$versionMatch.Groups[2].Value
    
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
        Write-Host "错误：Python版本过低，需要Python 3.9+" -ForegroundColor Red
        Write-Host "当前版本：$pythonVersion" -ForegroundColor Yellow
        Write-Host
        Read-Host "按Enter键退出"
        exit 1
    }
}

# 创建虚拟环境（如果不存在）
if (-not (Test-Path "venv")) {
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "虚拟环境创建成功！" -ForegroundColor Green
    Write-Host
}

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host

# 更新pip
Write-Host "更新pip..." -ForegroundColor Yellow
pip install --upgrade pip | Out-Null
Write-Host

# 安装依赖
Write-Host "安装依赖..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt | Out-Null
    Write-Host "依赖安装成功！" -ForegroundColor Green
    Write-Host
}
catch {
    Write-Host "依赖安装失败，尝试使用poetry安装..." -ForegroundColor Yellow
    pip install poetry | Out-Null
    poetry install
    Write-Host
}

# 运行机器人
Write-Host "启动机器人..." -ForegroundColor Green
Write-Host "按 Ctrl+C 停止机器人" -ForegroundColor Yellow
Write-Host "====================================" -ForegroundColor Cyan
Write-Host

python bot.py

# 退出虚拟环境
deactivate