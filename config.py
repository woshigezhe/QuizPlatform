#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置 — 自动识别开发/生产环境

环境识别规则：
  1. 环境变量 ENV=production → 生产环境
  2. 环境变量 FLASK_DEBUG=1 或 ENV=development → 开发环境
  3. 通过 gunicorn 运行（'gunicorn' in sys.argv[0]）→ 生产环境
  4. 默认 → 开发环境

开发环境：使用 SQLite（instance/quiz.db），SECRET_KEY/管理员密码使用默认值
生产环境：优先从环境变量读取数据库 URL 和安全密钥，缺失时报警并使用默认值
"""

import os
import sys
import warnings

# ==================== 环境检测 ====================
def _detect_environment():
    """自动检测当前运行环境"""
    # 1. 显式环境变量优先
    env = os.environ.get('ENV', '').strip().lower()
    if env in ('production', 'prod'):
        return 'production'
    if env in ('development', 'dev'):
        return 'development'

    # 2. FLASK_DEBUG 强制开发模式
    flask_debug = os.environ.get('FLASK_DEBUG', '').strip().lower()
    if flask_debug in ('1', 'true', 'yes'):
        return 'development'

    # 3. 通过 gunicorn 运行视为生产环境
    if 'gunicorn' in os.path.basename(sys.argv[0]).lower():
        return 'production'

    # 4. 默认开发环境
    return 'development'


ENVIRONMENT = _detect_environment()
IS_PRODUCTION = ENVIRONMENT == 'production'
IS_DEVELOPMENT = ENVIRONMENT == 'development'

# ==================== 基础路径 ====================
BASEDIR = os.path.abspath(os.path.dirname(__file__))

# ==================== 安全配置 ====================
_secret_key = os.environ.get('SECRET_KEY', '').strip()
if _secret_key:
    SECRET_KEY = _secret_key
else:
    if IS_PRODUCTION:
        warnings.warn(
            "⚠️  安全警告：生产环境未设置 SECRET_KEY 环境变量！",
            RuntimeWarning
        )
    SECRET_KEY = 'dev-secret-key-change-in-prod'

# ==================== 管理员账号 ====================
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')

_admin_password = os.environ.get('ADMIN_PASSWORD', '').strip()
if _admin_password:
    ADMIN_PASSWORD = _admin_password
else:
    if IS_PRODUCTION:
        warnings.warn(
            "⚠️  安全警告：生产环境未设置 ADMIN_PASSWORD 环境变量！",
            RuntimeWarning
        )
    ADMIN_PASSWORD = 'admin123'

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')

# ==================== 数据库 URI 构建 ====================
def _build_sqlite_uri(db_file):
    """构建 SQLite 数据库 URI"""
    db_path = os.path.join(BASEDIR, 'instance', db_file)
    return f'sqlite:///{db_path.replace(os.sep, "/")}'

# 环境自适应：开发环境默认 SQLite，生产环境可指定 MySQL/PostgreSQL
_database_url = os.environ.get('DATABASE_URL', '').strip()

if _database_url:
    SQLALCHEMY_DATABASE_URI = _database_url
elif IS_PRODUCTION:
    # 生产环境未设置 DATABASE_URL 时，尝试从单独的环境变量构建
    db_host = os.environ.get('DB_HOST', '').strip()
    db_port = os.environ.get('DB_PORT', '3306').strip()
    db_user = os.environ.get('DB_USER', '').strip()
    db_pass = os.environ.get('DB_PASS', '').strip()
    db_name = os.environ.get('DB_NAME', 'quiz_platform').strip()
    db_type = os.environ.get('DB_TYPE', 'mysql').strip().lower()

    if db_host and db_user and db_pass:
        if db_type == 'postgresql':
            SQLALCHEMY_DATABASE_URI = (
                f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
            )
        else:
            SQLALCHEMY_DATABASE_URI = (
                f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
            )
    else:
        # 生产环境回退到 SQLite
        warnings.warn("⚠️  生产环境未配置远程数据库，回退使用 SQLite", RuntimeWarning)
        SQLALCHEMY_DATABASE_URI = _build_sqlite_uri('quiz.db')
else:
    # 开发环境：默认 SQLite
    SQLALCHEMY_DATABASE_URI = _build_sqlite_uri('quiz.db')


# ==================== 数据库绑定（配置/用户/题库数据分离） ====================
# 三个逻辑数据库按类分离，默认均指向同一数据库（保证跨模型 JOIN 正常工作）
#   - bind 'config':  Category, Group, Question（题库配置）
#   - bind 'users':   User（用户账号）
#   - bind 'records': QuizRecord, QuizDetail, UserProgress（答题记录 / 用户进度）
#
# 生产环境可通过环境变量分别指定不同数据库实现物理分离：
#   CONFIG_DATABASE_URL  → 题库配置
#   USERS_DATABASE_URL   → 用户数据
#   RECORDS_DATABASE_URL → 答题记录
_config_url = os.environ.get('CONFIG_DATABASE_URL', '').strip()
_users_url = os.environ.get('USERS_DATABASE_URL', '').strip()
_records_url = os.environ.get('RECORDS_DATABASE_URL', '').strip()

SQLALCHEMY_BINDS = {
    'config':  _config_url if _config_url else SQLALCHEMY_DATABASE_URI,
    'users':   _users_url if _users_url else SQLALCHEMY_DATABASE_URI,
    'records': _records_url if _records_url else SQLALCHEMY_DATABASE_URI,
}


# ==================== Flask 配置类 ====================
class Config:
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_BINDS = SQLALCHEMY_BINDS
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = 'uploads'

    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs('instance', exist_ok=True)


# ==================== 打印当前环境信息（方便调试） ====================
def print_env_info():
    """打印当前环境配置摘要"""
    db_info = SQLALCHEMY_DATABASE_URI
    if '@' in db_info:
        # 隐藏密码
        db_info = db_info[:db_info.index(':')] + ':***@' + db_info.split('@', 1)[1]

    print(f"  环境: {'🔧 生产环境' if IS_PRODUCTION else '💻 开发环境'}")
    print(f"  数据库: {db_info}")
    if IS_PRODUCTION:
        print(f"  数据分离: {'是' if (_config_url or _users_url or _records_url) else '否（共用同一数据库）'}")