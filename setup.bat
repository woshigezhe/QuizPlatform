@echo off
chcp 65001 >nul
title 在线答题系统 - 管理工具
setlocal enabledelayedexpansion

:: ==================== 配置变量 ====================
set "VENV_DIR=.venv"
set "APP_FILE=app.py"
set "HOST=127.0.0.1"
set "PORT=8000"
set "PROJECT_DIR=%~dp0"

:: ==================== 镜像自动检测 ====================
:detect_mirror
echo ※ 检测最优 pip 镜像源...

:: 测试官方源
curl -s --connect-timeout 2 https://pypi.org >nul 2>&1
if %errorlevel% equ 0 (
    set "PIP_INDEX="
    echo ✔ 使用官方源 pypi.org
    goto :eof
)

:: 逐一尝试国内镜像
curl -s --connect-timeout 2 https://pypi.tuna.tsinghua.edu.cn >nul 2>&1
if %errorlevel% equ 0 (
    set "PIP_INDEX=-i https://pypi.tuna.tsinghua.edu.cn/simple"
    echo ✔ 使用清华镜像
    goto :eof
)

curl -s --connect-timeout 2 https://mirrors.aliyun.com >nul 2>&1
if %errorlevel% equ 0 (
    set "PIP_INDEX=-i https://mirrors.aliyun.com/pypi/simple"
    echo ✔ 使用阿里云镜像
    goto :eof
)

curl -s --connect-timeout 2 https://mirrors.cloud.tencent.com >nul 2>&1
if %errorlevel% equ 0 (
    set "PIP_INDEX=-i https://mirrors.cloud.tencent.com/pypi/simple"
    echo ✔ 使用腾讯云镜像
    goto :eof
)

echo ⚠ 所有镜像均不可达，使用默认源
set "PIP_INDEX="
goto :eof

:detect_npm_mirror
echo ※ 检测最优 npm 镜像源...
curl -s --connect-timeout 2 https://registry.npmjs.org >nul 2>&1
if %errorlevel% equ 0 (
    set "NPM_REGISTRY=https://registry.npmjs.org"
    goto :eof
)
curl -s --connect-timeout 2 https://registry.npmmirror.com >nul 2>&1
if %errorlevel% equ 0 (
    set "NPM_REGISTRY=https://registry.npmmirror.com"
    echo ✔ 使用 npmmirror.com 镜像
    goto :eof
)
set "NPM_REGISTRY=https://registry.npmjs.org"
goto :eof

:: ==================== 检查 Python 环境 ====================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: ==================== 主菜单 ====================
:main_menu
cls
echo ╔══════════════════════════════════════════════╗
echo ║     📚 在线答题系统 - 管理工具              ║
echo ╠══════════════════════════════════════════════╣
echo ║                                              ║
echo ║  架构: Flask 服务端渲染 + Vue 3 前端 (SPA)    ║
echo ║  环境: 自动识别 (开发/生产)                  ║
echo ║  配置: config.py (密钥/数据库/管理员)         ║
echo ║                                              ║
echo ║  [1] 安装/更新依赖 (pip install)             ║
echo ║  [2] 初始化数据库 (建表+管理员)               ║
echo ║  [3] 启动开发服务器 (Flask debug)             ║
echo ║  [4] 启动生产服务器 (Gunicorn)                ║
echo ║  [5] 重置数据库 (删除重建)                    ║
echo ║  [6] 环境信息 / 配置检查                      ║
echo ║  [7] 进入 Python 交互环境                     ║
echo ║  [8] 一键启动 (安装+初始化+启动开发服)        ║
echo ║  [9] 前端开发服务器 (Vue 3 + Vite)            ║
echo ║  [G] GitHub 镜像克隆助手                       ║
echo ║  [0] 退出                                     ║
echo ║                                              ║
echo ╚══════════════════════════════════════════════╝
echo.
set /p choice="请输入选项编号 [0-9/G]: "

if "%choice%"=="1" goto install_deps
if "%choice%"=="2" goto init_db
if "%choice%"=="3" goto run_dev
if "%choice%"=="4" goto run_prod
if "%choice%"=="5" goto reset_db
if "%choice%"=="6" goto show_info
if "%choice%"=="7" goto python_shell
if "%choice%"=="8" goto one_click
if "%choice%"=="9" goto frontend_dev
if /i "%choice%"=="g" goto github_clone_helper
if "%choice%"=="0" goto exit_script
echo 无效选项，请重新选择
timeout /t 2 >nul
goto main_menu

:: ==================== 激活虚拟环境 ====================
:activate_venv
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ※ 创建虚拟环境...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败
        pause
        goto main_menu
    )
)
call "%VENV_DIR%\Scripts\activate.bat" >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境激活失败
    pause
    goto main_menu
)
goto :eof

:: ==================== [1] 安装依赖 ====================
:install_deps
call :activate_venv
echo.
echo ============================================
echo  [1] 安装 Python 依赖包
echo ============================================

call :detect_mirror

echo ※ 升级 pip...
python -m pip install --upgrade pip -q %PIP_INDEX%

echo ※ 安装项目依赖...
pip install -r requirements.txt --only-binary :all: %PIP_INDEX%
if %errorlevel% neq 0 (
    echo [!] 仅二进制安装失败，尝试完整安装...
    pip install -r requirements.txt %PIP_INDEX%
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        goto main_menu
    )
)

echo.
echo ✔ 依赖安装完成
echo.
pause
goto main_menu

:: ==================== [2] 初始化数据库 ====================
:init_db
call :activate_venv
echo.
echo ============================================
echo  [2] 初始化数据库
echo ============================================
echo ※ 创建表结构 + 创建默认管理员账号...
python -c "from app import app; from utils import init_db; app.app_context().push(); init_db()"
if %errorlevel% neq 0 (
    echo [错误] 数据库初始化失败
    pause
    goto main_menu
)
echo.
echo ✔ 数据库初始化完成
echo.
pause
goto main_menu

:: ==================== [3] 启动开发服务器 ====================
:run_dev
call :activate_venv
echo.
echo ============================================
echo  [3] 启动 Flask 开发服务器
echo ============================================
echo ※ 设置 FLASK_DEBUG=1 启用热重载...
set FLASK_DEBUG=1
echo ※ 地址: http://%HOST%:%PORT%
echo ※ 按 Ctrl+C 停止服务器
echo ============================================
echo.
python %APP_FILE%
pause
goto main_menu

:: ==================== [4] 启动生产服务器 ====================
:run_prod
call :activate_venv
echo.
echo ============================================
echo  [4] 启动 Gunicorn 生产服务器
echo ============================================

where gunicorn >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未检测到 gunicorn，正在安装...
    pip install gunicorn -q
)

:gunicorn_workers
echo.
echo 请选择工作进程数:
echo   [1] 2 个进程 (轻量)
echo   [2] 4 个进程 (推荐)
echo   [3] 8 个进程 (高负载)
echo   [c] 自定义
echo.
set /p worker_choice="请输入选项: "

if "%worker_choice%"=="1" set WORKERS=2
if "%worker_choice%"=="2" set WORKERS=4
if "%worker_choice%"=="3" set WORKERS=8
if "%worker_choice%"=="c" goto custom_workers
if "%worker_choice%"=="C" goto custom_workers
if not defined WORKERS goto gunicorn_workers

goto :run_gunicorn

:custom_workers
set /p WORKERS="请输入进程数: "
goto :run_gunicorn

:run_gunicorn
echo.
echo ※ 启动 Gunicorn (进程数: %WORKERS%)...
echo ※ 地址: http://%HOST%:%PORT%
echo ※ 按 Ctrl+C 停止服务器
echo ============================================
echo.
gunicorn -w %WORKERS% -b %HOST%:%PORT% app:app --access-logfile - --error-logfile -
pause
goto main_menu

:: ==================== [5] 重置数据库 ====================
:reset_db
call :activate_venv
echo.
echo ============================================
echo  [5] 重置数据库
echo ============================================
echo ⚠ 警告：此操作将永久删除所有数据！

:confirm_reset
set /p confirm="确认删除并重建数据库？(输入 yes 继续，no 取消): "
if /i "%confirm%"=="no" (
    echo 已取消
    pause
    goto main_menu
)
if /i "%confirm%"=="y" goto do_reset
if /i "%confirm%"=="yes" goto do_reset
goto confirm_reset

:do_reset
echo.
echo ※ 删除数据库文件...

if exist "instance\quiz.db" (
    del /q "instance\quiz.db"
    echo   已删除 instance/quiz.db
) else (
    echo   未找到 quiz.db
)

:: 同时清理分离的数据库文件
if exist "instance\quiz_config.db" del /q "instance\quiz_config.db"
if exist "instance\quiz_users.db" del /q "instance\quiz_users.db"
if exist "instance\quiz_records.db" del /q "instance\quiz_records.db"

echo.
echo ※ 重建数据库...
python -c "from app import app; from utils import init_db; app.app_context().push(); init_db()"
if %errorlevel% neq 0 (
    echo [错误] 数据库重建失败
    pause
    goto main_menu
)
echo.
echo ✔ 数据库已重置，默认管理员：admin / admin123
echo.
pause
goto main_menu

:: ==================== [6] 环境信息 ====================
:show_info
call :activate_venv
echo.
echo ============================================
echo  [6] 环境信息
echo ============================================
echo.
python -c "from config import print_env_info; print_env_info()"
echo.
echo --- Python 环境 ---
python --version
echo.
pip --version
echo.
echo --- 已安装的关键包 ---
pip list 2>nul | findstr /I "flask sqlalchemy gunicorn pandas openpyxl"
echo.
echo --- 项目路径 ---
echo %PROJECT_DIR%
echo.
echo --- 环境变量 ---
if defined ENV (echo   ENV = %ENV%) else (echo   ENV = 未设置)
if defined FLASK_DEBUG (echo   FLASK_DEBUG = %FLASK_DEBUG%) else (echo   FLASK_DEBUG = 未设置)
if defined DATABASE_URL (echo   DATABASE_URL = %DATABASE_URL%) else (echo   DATABASE_URL = 未设置)
if defined DB_PATH (echo   DB_PATH = %DB_PATH%) else (echo   DB_PATH = 未设置)
echo.
pause
goto main_menu

:: ==================== [7] Python 交互环境 ====================
:python_shell
call :activate_venv
echo.
echo ============================================
echo  [7] Python 交互环境
echo ============================================
echo ※ 已自动导入 app/db/models/utils
echo ※ 输入 exit() 退出
echo ============================================
echo.
python -i -c "from app import app; app.app_context().push(); from models import *; from utils import *; print('app context ready')"
goto main_menu

:: ==================== [8] 一键启动 ====================
:one_click
call :activate_venv
echo.
echo ============================================
echo  [8] 一键启动（安装依赖 + 初始化 + 开发服务器）
echo ============================================

call :detect_mirror

echo ※ [1/3] 安装依赖...
pip install -r requirements.txt --only-binary :all: -q %PIP_INDEX% 2>nul
if %errorlevel% neq 0 (
    pip install -r requirements.txt -q %PIP_INDEX%
)
echo   依赖安装完成

echo ※ [2/3] 初始化数据库...
python -c "from app import app; from utils import init_db; app.app_context().push(); init_db()"
echo   数据库初始化完成

echo ※ [3/3] 启动开发服务器...
set FLASK_DEBUG=1
echo.
echo ============================================
echo   服务器运行在 http://%HOST%:%PORT%
echo   默认管理员: admin / admin123
echo   按 Ctrl+C 停止服务器
echo ============================================
echo.
python %APP_FILE%
pause
goto main_menu

:: ==================== [9] 前端开发服务器 ====================
:frontend_dev
echo.
echo ============================================
echo  [9] 启动 Vue 3 前端开发服务器
echo ============================================
if not exist "frontend\node_modules" (
    echo ※ 首次运行，检测 Node.js 环境...
    where node >nul 2>&1
    if %errorlevel% neq 0 (
        echo [错误] 未检测到 Node.js，请先安装 Node.js 16+
        echo 下载地址: https://nodejs.org/
        pause
        goto main_menu
    )
    call :detect_npm_mirror
    echo ※ 安装前端依赖 (npm install)...
    cd frontend
    call npm install --registry="%NPM_REGISTRY%"
    cd ..
    if %errorlevel% neq 0 (
        echo [错误] 前端依赖安装失败
        pause
        goto main_menu
    )
)
echo ※ 前端地址: http://localhost:3000
echo ※ API 代理目标: http://127.0.0.1:8000
echo ※ 请确保 Flask 后端已启动
echo ※ 按 Ctrl+C 停止服务器
echo ============================================
echo.
cd frontend
call npm run dev
cd ..
pause
goto main_menu

:: ==================== [G] GitHub 克隆助手 ====================
:github_clone_helper
echo.
echo ============================================
echo  [G] GitHub 镜像克隆助手
echo ============================================
echo.
echo   GitHub 访问缓慢/失败时，使用镜像代理克隆:
echo.
echo   gitclone.com:
echo     git clone https://gitclone.com/github.com/xybbb/QuizPlatform.git
echo.
echo   cnpmjs.org:
echo     git clone https://github.com.cnpmjs.org/xybbb/QuizPlatform.git
echo.
echo   克隆后进入项目:
echo     cd QuizPlatform ^&^& setup.bat
echo.
pause
goto main_menu

:: ==================== 退出 ====================
:exit_script
echo.
echo 再见！
timeout /t 1 >nul
exit /b 0