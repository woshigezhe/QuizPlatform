#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置

数据库支持多版本互通：
  - 默认使用 SQLite（本地文件 quiz.db）
  - 设置环境变量 DATABASE_URL 可切换为 MySQL / PostgreSQL
    示例:
      MySQL:      set DATABASE_URL=mysql+pymysql://user:pass@localhost/dbname
      PostgreSQL: set DATABASE_URL=postgresql://user:pass@localhost/dbname
"""
import os
import secrets
import warnings

# ==================== 基础配置 ====================
DATABASE_FILE = 'quiz.db'

# SECRET_KEY：优先使用环境变量，否则生成随机密钥并在生产环境发出警告
_secret_key = os.environ.get('SECRET_KEY', '').strip()
if _secret_key:
    SECRET_KEY = _secret_key
else:
    SECRET_KEY = 'dev-secret-key-change-in-prod'
    if not os.environ.get('FLASK_DEBUG'):
        warnings.warn(
            "⚠️  安全警告：未设置 SECRET_KEY 环境变量，使用默认密钥。"
            "生产环境请务必设置 SECRET_KEY 环境变量！",
            RuntimeWarning
        )

# 管理员账号：优先使用环境变量
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
_admin_password = os.environ.get('ADMIN_PASSWORD', '').strip()
if _admin_password:
    ADMIN_PASSWORD = _admin_password
else:
    ADMIN_PASSWORD = 'admin123'
    if not os.environ.get('FLASK_DEBUG'):
        warnings.warn(
            "⚠️  安全警告：未设置 ADMIN_PASSWORD 环境变量，使用默认管理员密码。"
            "生产环境请务必设置 ADMIN_PASSWORD 环境变量！",
            RuntimeWarning
        )
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')

# ==================== 数据库 URI 构建 ====================
# 优先使用环境变量 DATABASE_URL，否则默认 SQLite
_database_url = os.environ.get('DATABASE_URL', '').strip()
if _database_url:
    # 支持 MySQL/PostgreSQL 等外部数据库
    SQLALCHEMY_DATABASE_URI = _database_url
else:
    # 默认使用 SQLite，数据库文件存储在 instance 目录
    # 使用绝对路径避免 Windows 反斜杠导致的 URI 解析问题
    _basedir = os.path.abspath(os.path.dirname(__file__))
    _db_path = os.path.join(_basedir, 'instance', DATABASE_FILE)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{_db_path.replace(os.sep, "/")}'

# ==================== Flask 配置类 ====================
class Config:
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = 'uploads'
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        # 确保 instance 目录存在（SQLite 数据库文件存放处）
        os.makedirs('instance', exist_ok=True)
