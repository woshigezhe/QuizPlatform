#!/bin/bash
# 在线答题系统 - 管理工具 (Linux/macOS)
# 用法: bash setup.sh
#       或 chmod +x setup.sh && ./setup.sh

set -e
shopt -s nocasematch

# ==================== 配置变量 ====================
VENV_DIR=".venv"
APP_FILE="app.py"
HOST="127.0.0.1"
PORT="5000"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ==================== 颜色输出 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}※${NC} $1"; }
success() { echo -e "${GREEN}✔${NC} $1"; }
warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
error()   { echo -e "${RED}[错误]${NC} $1"; }
header()  { echo -e "${BOLD}$1${NC}"; }

# ==================== 检查 Python 环境 ====================
check_python() {
    if ! command -v python3 &> /dev/null; then
        error "未检测到 Python3，请先安装 Python 3.8+"
        echo "下载地址: https://www.python.org/downloads/"
        exit 1
    fi

    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
        PYVER=$(python3 --version 2>&1)
        error "Python 版本过低，需要 3.8+，当前为 $PYVER"
        exit 1
    fi
}

# ==================== 激活虚拟环境 ====================
activate_venv() {
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        info "创建虚拟环境..."
        python3 -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            error "虚拟环境创建失败"
            return 1
        fi
    fi
    source "$VENV_DIR/bin/activate" 2>/dev/null
}

# ==================== 主菜单 ====================
main_menu() {
    clear 2>/dev/null || true
    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║     📚 在线答题系统 - 管理工具              ║${NC}"
    echo -e "${BOLD}╠══════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}║                                              ║${NC}"
    echo -e "${BOLD}║  架构: Flask 服务端渲染 + Vue 3 前端 (SPA)    ║${NC}"
    echo -e "${BOLD}║  环境: 自动识别 (开发/生产)                  ║${NC}"
    echo -e "${BOLD}║  配置: config.py (密钥/数据库/管理员)         ║${NC}"
    echo -e "${BOLD}║                                              ║${NC}"
    echo -e "${BOLD}║  [1] 安装/更新依赖 (pip install)             ║${NC}"
    echo -e "${BOLD}║  [2] 初始化数据库 (建表+管理员)               ║${NC}"
    echo -e "${BOLD}║  [3] 启动开发服务器 (Flask debug)             ║${NC}"
    echo -e "${BOLD}║  [4] 启动生产服务器 (Gunicorn)                ║${NC}"
    echo -e "${BOLD}║  [5] 重置数据库 (删除重建)                    ║${NC}"
    echo -e "${BOLD}║  [6] 环境信息 / 配置检查                      ║${NC}"
    echo -e "${BOLD}║  [7] 进入 Python 交互环境                     ║${NC}"
    echo -e "${BOLD}║  [8] 一键启动 (安装+初始化+启动开发服)        ║${NC}"
    echo -e "${BOLD}║  [9] 前端开发服务器 (Vue 3 + Vite)            ║${NC}"
    echo -e "${BOLD}║  [0] 退出                                     ║${NC}"
    echo -e "${BOLD}║                                              ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    read -p "请输入选项编号 [0-9]: " choice

    case "$choice" in
        1) install_deps ;;
        2) init_db ;;
        3) run_dev ;;
        4) run_prod ;;
        5) reset_db ;;
        6) show_info ;;
        7) python_shell ;;
        8) one_click ;;
        9) frontend_dev ;;
        0) exit_script ;; 
        *) echo -e "${RED}无效选项，请重新选择${NC}"; sleep 1; main_menu ;;
    esac
}

# ==================== [1] 安装依赖 ====================
install_deps() {
    activate_venv
    echo ""
    echo "============================================"
    header "[1] 安装 Python 依赖包"
    echo "============================================"

    info "升级 pip..."
    python3 -m pip install --upgrade pip -q

    info "安装项目依赖 (清华源)..."
    if pip install -r requirements.txt --only-binary :all: -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null; then
        success "依赖安装完成"
    else
        warn "清华源失败，尝试默认源..."
        if pip install -r requirements.txt --only-binary :all: 2>/dev/null; then
            success "依赖安装完成"
        else
            warn "仅二进制安装失败，尝试完整安装..."
            if pip install -r requirements.txt; then
                success "依赖安装完成"
            else
                error "依赖安装失败，请检查网络连接"
            fi
        fi
    fi

    echo ""
    read -p "按 Enter 返回主菜单..." _
    main_menu
}

# ==================== [2] 初始化数据库 ====================
init_db() {
    activate_venv
    echo ""
    echo "============================================"
    header "[2] 初始化数据库"
    echo "============================================"
    info "创建表结构 + 创建默认管理员账号..."

    if python3 -c "from app import app; from utils import init_db; app.app_context().push(); init_db()" 2>&1; then
        success "数据库初始化完成"
    else
        error "数据库初始化失败"
    fi

    echo ""
    read -p "按 Enter 返回主菜单..." _
    main_menu
}

# ==================== [3] 启动开发服务器 ====================
run_dev() {
    activate_venv
    echo ""
    echo "============================================"
    header "[3] 启动 Flask 开发服务器"
    echo "============================================"
    export FLASK_DEBUG=1
    info "设置 FLASK_DEBUG=1 启用热重载"
    info "地址: http://${HOST}:${PORT}"
    info "按 Ctrl+C 停止服务器"
    echo "============================================"
    echo ""

    python3 "$APP_FILE"
    read -p "按 Enter 返回主菜单..." _
    main_menu
}

# ==================== [4] 启动生产服务器 ====================
run_prod() {
    activate_venv
    echo ""
    echo "============================================"
    header "[4] 启动 Gunicorn 生产服务器"
    echo "============================================"

    if ! command -v gunicorn &> /dev/null; then
        warn "未检测到 gunicorn，正在安装..."
        pip install gunicorn -q
    fi

    echo ""
    echo "请选择工作进程数:"
    echo "  [1] 2 个进程 (轻量)"
    echo "  [2] 4 个进程 (推荐)"
    echo "  [3] 8 个进程 (高负载)"
    echo "  [c] 自定义"
    echo ""
    read -p "请输入选项: " worker_choice

    case "$worker_choice" in
        1) WORKERS=2 ;;
        2) WORKERS=4 ;;
        3) WORKERS=8 ;;
        c|C)
            read -p "请输入进程数: " WORKERS
            ;;
        *)
            warn "无效选项，默认 4 个进程"
            WORKERS=4
            ;;
    esac

    echo ""
    info "启动 Gunicorn (进程数: ${WORKERS})..."
    info "地址: http://${HOST}:${PORT}"
    info "按 Ctrl+C 停止服务器"
    echo "============================================"
    echo ""

    gunicorn -w "$WORKERS" -b "${HOST}:${PORT}" app:app --access-logfile - --error-logfile -
    read -p "按 Enter 返回主菜单..." _
    main_menu
}

# ==================== [5] 重置数据库 ====================
reset_db() {
    activate_venv
    echo ""
    echo "============================================"
    header "[5] 重置数据库"
    echo "============================================"
    warn "此操作将永久删除所有数据！"
    echo ""

    read -p "确认删除并重建数据库？(输入 yes 继续，no 取消): " confirm
    if [[ "$confirm" =~ ^(no|n)$ ]]; then
        echo "已取消"
        read -p "按 Enter 返回主菜单..." _
        main_menu
        return
    fi
    if [[ ! "$confirm" =~ ^(yes|y)$ ]]; then
        echo "请输入 yes 或 no"
        read -p "按 Enter 重新确认..." _
        reset_db
        return
    fi

    echo ""
    info "删除数据库文件..."

    DB_DIR="$PROJECT_DIR/instance"
    if [ -f "$DB_DIR/quiz.db" ]; then
        rm -f "$DB_DIR/quiz.db"
        success "已删除 instance/quiz.db"
    fi
    rm -f "$DB_DIR/quiz_config.db" "$DB_DIR/quiz_users.db" "$DB_DIR/quiz_records.db" 2>/dev/null

    echo ""
    info "重建数据库..."
    if python3 -c "from app import app; from utils import init_db; app.app_context().push(); init_db()" 2>&1; then
        success "数据库已重置"
        info "默认管理员：admin / admin123"
    else
        error "数据库重建失败"
    fi

    echo ""
    read -p "按 Enter 返回主菜单..." _
    main_menu
}

# ==================== [6] 环境信息 ====================
show_info() {
    activate_venv
    echo ""
    echo "============================================"
    header "[6] 环境信息"
    echo "============================================"
    echo ""

    python3 -c "from config import print_env_info; print_env_info()" 2>/dev/null

    echo ""
    echo -e "${BOLD}--- Python 环境 ---${NC}"
    python3 --version 2>&1
    pip3 --version 2>&1

    echo ""
    echo -e "${BOLD}--- 已安装的关键包 ---${NC}"
    pip3 list 2>/dev/null | grep -iE "flask|sqlalchemy|gunicorn|pandas|openpyxl" || echo "  (未找到)"

    echo ""
    echo -e "${BOLD}--- 项目路径 ---${NC}"
    echo "  $PROJECT_DIR"

    echo ""
    echo -e "${BOLD}--- 环境变量 ---${NC}"
    echo "  ENV              = ${ENV:-未设置}"
    echo "  FLASK_DEBUG      = ${FLASK_DEBUG:-未设置}"
    echo "  DATABASE_URL     = ${DATABASE_URL:-未设置}"
    echo "  CONFIG_DATABASE_URL = ${CONFIG_DATABASE_URL:-未设置}"
    echo "  USERS_DATABASE_URL  = ${USERS_DATABASE_URL:-未设置}"
    echo "  RECORDS_DATABASE_URL = ${RECORDS_DATABASE_URL:-未设置}"

    echo ""
    read -p "按 Enter 返回主菜单..." _
    main_menu
}

# ==================== [7] Python 交互环境 ====================
python_shell() {
    activate_venv
    echo ""
    echo "============================================"
    header "[7] Python 交互环境"
    echo "============================================"
    info "已自动导入 app/db/models/utils"
    info "输入 exit() 退出"
    echo "============================================"
    echo ""

    python3 -i -c "
from app import app
app.app_context().push()
from models import *
from utils import *
print('app context ready, tables:', [t for t in dir() if t[0].isupper()])
"

    main_menu
}

# ==================== [8] 一键启动 ====================
one_click() {
    activate_venv
    echo ""
    echo "============================================"
    header "[8] 一键启动（安装依赖 + 初始化 + 开发服务器）"
    echo "============================================"

    echo ""
    info "[1/3] 安装依赖..."
    pip install -r requirements.txt --only-binary :all: -q -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || \
        pip install -r requirements.txt --only-binary :all: -q
    success "依赖安装完成"

    echo ""
    info "[2/3] 初始化数据库..."
    python3 -c "from app import app; from utils import init_db; app.app_context().push(); init_db()" 2>&1
    success "数据库初始化完成"

    echo ""
    info "[3/3] 启动开发服务器..."
    export FLASK_DEBUG=1
    echo ""
    echo "============================================"
    header "  服务器运行在 http://${HOST}:${PORT}"
    header "  默认管理员: admin / admin123"
    header "  按 Ctrl+C 停止服务器"
    echo "============================================"
    echo ""

    python3 "$APP_FILE"
    read -p "按 Enter 返回主菜单..." _
    main_menu
}

# ==================== [9] 前端开发服务器 ====================
frontend_dev() {
    echo ""
    echo "============================================"
    header "[9] 启动 Vue 3 前端开发服务器"
    echo "============================================"

    if [ ! -d "frontend/node_modules" ]; then
        if ! command -v node &> /dev/null; then
            error "未检测到 Node.js，请先安装 Node.js 16+"
            echo "下载地址: https://nodejs.org/"
            read -p "按 Enter 返回主菜单..." _
            main_menu
            return
        fi
        info "首次运行，安装前端依赖 (npm install)..."
        (cd frontend && npm install) || {
            error "前端依赖安装失败"
            read -p "按 Enter 返回主菜单..." _
            main_menu
            return
        }
    fi

    info "前端地址: http://localhost:3000"
    info "API 代理目标: http://127.0.0.1:5000"
    info "请确保 Flask 后端已启动"
    info "按 Ctrl+C 停止服务器"
    echo "============================================"
    echo ""

    cd frontend && npm run dev
    cd "$PROJECT_DIR"
    read -p "按 Enter 返回主菜单..." _
    main_menu
}

# ==================== 退出 ====================
exit_script() {
    echo ""
    echo "再见！"
    exit 0
}

# ==================== 主入口 ====================
check_python
main_menu