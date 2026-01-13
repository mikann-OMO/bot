@echo off
chcp 65001 >nul
echo ====================================
echo  NoneBot2 QQ机器人启动脚本
echo ====================================
echo.

:: 检查Python是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误：未安装Python 3.9+
echo 请先安装Python 3.9或更高版本，然后重新运行此脚本
echo.
pause
exit /b 1
)

:: 检查Python版本
for /f "tokens=2 delims=." %%i in ('python --version ^| findstr /i "python"') do set PYTHON_MINOR=%%i
if %PYTHON_MINOR% lss 9 (
    echo 错误：Python版本过低，需要Python 3.9+
echo 当前版本：%PYTHON_VERSION%
echo.
pause
exit /b 1
)

echo 找到Python环境：
python --version
echo.

:: 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo 创建虚拟环境...
python -m venv venv
echo 虚拟环境创建成功！
echo.
)

:: 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat
echo.

:: 更新pip
echo 更新pip...
pip install --upgrade pip >nul
echo.

:: 安装依赖
echo 安装依赖...
pip install -r requirements.txt >nul 2>nul
if %errorlevel% neq 0 (
    echo 依赖安装失败，尝试使用poetry安装...
pip install poetry >nul
poetry install
echo.
) else (
    echo 依赖安装成功！
echo.
)

:: 运行机器人
echo 启动机器人...
echo 按 Ctrl+C 停止机器人
echo ====================================
echo.
python bot.py

:: 退出虚拟环境
deactivate
