#!/bin/bash
# QuizPlatform 生产部署脚本 (Flask SSR + RESTful API)
# 用法: bash deploy.sh [选项]
#
# 选项:
#   --workers NUM     工作进程数 (默认 4)
#   --port PORT       监听端口 (默认 5000)
#   --host HOST       监听地址 (默认 0.0.0.0)
#   --restart         仅重启服务 (不拉取代码, 不装依赖)
#   --pull-only       仅拉取最新代码
#   --no-pull         跳过代码拉取
#   --no-install      跳过依赖安装
#   --db-url URL      设置 DATABASE_URL 环境变量
#   --env-file FILE   加载环境变量文件
#   --health-check    部署后执行健康检查
#   --log-dir DIR     日志目录 (默认: 项目目录)
#   --help            显示帮助
#
# 示例:
#   bash deploy.sh                              # 完整部署
#   bash deploy.sh --restart                    # 仅重启服务
#   bash deploy.sh --workers 8 --port 8080      # 自定义参数
#   bash deploy.sh --env-file .env.prod         # 加载环境变量
#   bash deploy.sh --health-check               # 部署后验证服务可用性

set -e

# ==================== 默认配置 ====================
PROJECT_DIR="/opt/QuizPlatform"
SCREEN_NAME="quizplatform"
VENV_DIR=".venv"
WORKERS=4
HOST="0.0.0.0"
PORT=5000
DO_PULL=true
DO_INSTALL=true
DO_RESTART=true
ENV_FILE=""
LOG_DIR=""
HEALTH_CHECK=false

# ==================== 颜色输出 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${BLUE}[*]${NC} $1"; }
success() { echo -e "${GREEN}[✔]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✘]${NC} $1"; exit 1; }

# ==================== 镜像自动检测 ====================
detect_pip_mirror() {
    info "检测最优 pip 镜像源..."
    if curl -s --connect-timeout 2 https://pypi.org > /dev/null 2>&1; then
        PIP_INDEX=""
        success "使用官方源 pypi.org"
        return
    fi
    local mirrors=(
        "https://pypi.tuna.tsinghua.edu.cn/simple|清华"
        "https://mirrors.aliyun.com/pypi/simple|阿里云"
        "https://mirrors.cloud.tencent.com/pypi/simple|腾讯云"
    )
    for entry in "${mirrors[@]}"; do
        local url="${entry%%|*}"
        local name="${entry##*|}"
        local host=$(echo "$url" | awk -F/ '{print $3}')
        if curl -s --connect-timeout 2 "https://${host}" > /dev/null 2>&1; then
            PIP_INDEX="-i ${url}"
            success "使用${name}镜像"
            return
        fi
    done
    warn "所有镜像均不可达，使用默认源"
    PIP_INDEX=""
}

detect_github_mirror() {
    info "检测 GitHub 可达性..."
    if curl -s --connect-timeout 3 https://github.com > /dev/null 2>&1; then
        GIT_MIRROR_FLAG=""
        return
    fi
    if curl -s --connect-timeout 3 https://gitclone.com > /dev/null 2>&1; then
        GIT_MIRROR_FLAG="-c url.https://gitclone.com/github.com/.insteadOf=https://github.com/"
        success "使用 GitHub 镜像: gitclone.com"
        return
    fi
    warn "GitHub 不可达且无可用镜像代理"
    GIT_MIRROR_FLAG=""
}

# ==================== 显示帮助 ====================
show_help() {
    echo "QuizPlatform 生产部署脚本"
    echo ""
    echo "用法: bash deploy.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --workers NUM     工作进程数 (默认 4)"
    echo "  --port PORT       监听端口 (默认 5000)"
    echo "  --host HOST       监听地址 (默认 0.0.0.0)"
    echo "  --restart         仅重启服务 (不拉取代码, 不装依赖)"
    echo "  --pull-only       仅拉取最新代码"
    echo "  --restart-only    仅重启服务 (同 --restart)"
    echo "  --no-pull         跳过代码拉取"
    echo "  --no-install      跳过依赖安装"
    echo "  --db-url URL      设置 DATABASE_URL 环境变量"
    echo "  --env-file FILE   加载环境变量文件"
    echo "  --help            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  bash deploy.sh                              # 完整部署 (拉取 → 安装 → 重启)"
    echo "  bash deploy.sh --restart                    # 仅重启服务"
    echo "  bash deploy.sh --workers 8 --port 8080      # 自定义进程数和端口"
    echo "  bash deploy.sh --env-file .env.prod         # 从文件加载环境变量"
    echo "  bash deploy.sh --no-pull --no-install       # 仅重启"
    exit 0
}

# ==================== 解析参数 ====================
while [[ $# -gt 0 ]]; do
    case "$1" in
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --restart|--restart-only)
            DO_PULL=false
            DO_INSTALL=false
            DO_RESTART=true
            shift
            ;;
        --pull-only)
            DO_INSTALL=false
            DO_RESTART=false
            shift
            ;;
        --no-pull)
            DO_PULL=false
            shift
            ;;
        --no-install)
            DO_INSTALL=false
            shift
            ;;
        --db-url)
            export DATABASE_URL="$2"
            shift 2
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --health-check)
            HEALTH_CHECK=true
            shift
            ;;
        --log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        *)
            warn "未知选项: $1"
            echo "使用 --help 查看帮助"
            shift
            ;;
    esac
done

# ==================== 加载环境变量文件 ====================
if [ -n "$ENV_FILE" ]; then
    if [ -f "$ENV_FILE" ]; then
        info "加载环境变量文件: $ENV_FILE"
        set -a
        source "$ENV_FILE"
        set +a
        success "环境变量加载完成"
    else
        warn "环境变量文件不存在: $ENV_FILE"
    fi
fi

# ==================== 设置生产环境标识 ====================
export ENV=production
export FLASK_DEBUG=0

echo ""
echo "========================================"
echo "  🚀 QuizPlatform 生产部署"
echo "========================================"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "  目录: $PROJECT_DIR"
    echo "  主机: ${HOST}:${PORT}"
    echo "  进程: ${WORKERS} 个"
    echo "  健康检查: $([ "$HEALTH_CHECK" = true ] && echo '是' || echo '否')"
    echo "========================================"
echo ""

cd "$PROJECT_DIR" || error "项目目录不存在: $PROJECT_DIR"

# ==================== [1] 拉取代码 ====================
if [ "$DO_PULL" = true ]; then
    echo "━━━ [1/3] 拉取最新代码 ━━━"
    detect_github_mirror
    git $GIT_MIRROR_FLAG fetch origin main 2>/dev/null || warn "git fetch 失败，跳过"

    LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "unknown")

    if [ "$LOCAL" = "$REMOTE" ] && [ "$LOCAL" != "unknown" ]; then
        success "代码已是最新 ($(echo $LOCAL | head -c 8))"
    else
        info "检测到更新，拉取代码..."
        git $GIT_MIRROR_FLAG pull origin main && success "代码已更新" || warn "git pull 失败"
    fi
    echo ""
fi

# ==================== [2] 安装依赖 ====================
if [ "$DO_INSTALL" = true ]; then
    echo "━━━ [2/3] 安装依赖 ━━━"

    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate" 2>/dev/null || true
        info "虚拟环境已激活"
    else
        info "创建虚拟环境..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
    fi

    info "升级 pip..."
    python3 -m pip install --upgrade pip -q 2>/dev/null || true

    detect_pip_mirror

    info "安装/更新项目依赖..."
    pip install -r requirements.txt --only-binary :all: -q $PIP_INDEX 2>/dev/null || \
        pip install -r requirements.txt -q $PIP_INDEX 2>/dev/null || \
        warn "部分依赖安装失败，继续部署..."

    # 确保 gunicorn 已安装
    if ! command -v gunicorn &> /dev/null; then
        info "安装 gunicorn..."
        pip install gunicorn -q $PIP_INDEX
    fi

    success "依赖安装完成"
    echo ""
else
    # 仍然需要激活虚拟环境
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate" 2>/dev/null || true
    fi
fi

# ==================== [3] 重启服务 ====================
if [ "$DO_RESTART" = true ]; then
    echo "━━━ [3/3] 重启服务 ━━━"

    # 停止旧进程
    if screen -list 2>/dev/null | grep -q "\.${SCREEN_NAME}"; then
        info "停止旧 screen 会话..."
        screen -S "$SCREEN_NAME" -X quit
        sleep 1
        success "旧会话已关闭"
    else
        info "没有运行中的服务"
    fi

    # 初始化数据库（如果需要）
    info "检查/初始化数据库..."
    python3 -c "
from app import app
from utils import init_db
with app.app_context():
    init_db()
" 2>/dev/null && success "数据库就绪" || warn "数据库检查跳过"

    # 启动新进程
    info "启动 Gunicorn (${WORKERS} 进程, ${HOST}:${PORT})..."

    _log_dir="${LOG_DIR:-$PROJECT_DIR}"
    _access_log="${_log_dir}/gunicorn_access.log"
    _error_log="${_log_dir}/gunicorn_error.log"

    screen -dmS "$SCREEN_NAME" bash -c "
source ${VENV_DIR}/bin/activate
export ENV=production
export FLASK_DEBUG=0
gunicorn -w ${WORKERS} -b ${HOST}:${PORT} app:app \
    --access-logfile ${_access_log} \
    --error-logfile ${_error_log} \
    --log-level info \
    --timeout 120 \
    --graceful-timeout 30 \
    --worker-class sync \
    2>&1
"

    sleep 2

    # 验证启动
    if screen -list 2>/dev/null | grep -q "\.${SCREEN_NAME}"; then
        success "🎉 部署成功！服务已在 ${HOST}:${PORT} 运行"
        echo ""
        echo "  访问日志: tail -f ${_access_log}"
        echo "  错误日志: tail -f ${_error_log}"
        echo "  查看状态: screen -list"
        echo "  重启服务: bash deploy.sh --restart"
        echo ""

        # 健康检查
        if [ "$HEALTH_CHECK" = true ]; then
            echo "━━━ 健康检查 ━━━"
            _check_url="http://localhost:${PORT}/"
            if command -v curl &> /dev/null; then
                _http_code=$(curl -s -o /dev/null -w '%{http_code}' "$_check_url" 2>/dev/null || echo "000")
                if [ "$_http_code" -ge 200 ] && [ "$_http_code" -lt 500 ]; then
                    success "HTTP 健康检查通过 (状态码: ${_http_code})"
                else
                    warn "HTTP 健康检查异常 (状态码: ${_http_code})"
                fi
            else
                info "未安装 curl，跳过 HTTP 健康检查"
            fi
            echo ""
        fi
    else
        error "服务启动失败！请检查日志: ${PROJECT_DIR}/gunicorn_error.log"
    fi
fi

echo "=========================================="
echo "  部署完成 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="