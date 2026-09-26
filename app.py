#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在线答题系统 - 主入口
"""
from flask import Flask, request, jsonify, redirect, url_for
from flask_login import LoginManager
from config import Config
from models import db
from routes import register_routes
from routes.api import register_api
import os

# ==================== 初始化应用 ====================
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# 初始化扩展
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.auth_login'


@login_manager.unauthorized_handler
def unauthorized_handler():
    """API 请求返回 401 JSON，页面请求重定向到登录页。"""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': '请先登录'}), 401
    return redirect(url_for('auth.auth_login', next=request.url))

# 注册路由
register_routes(app)
register_api(app)

# ==================== 数据库初始化 ====================
# gunicorn 下不会进入 __main__，需在导入时确保建表与迁移（配合 --preload 只执行一次）
if __name__ != '__main__':
    try:
        from utils import init_db
        with app.app_context():
            init_db()
    except Exception as _e:  # 数据库暂时不可用时不阻塞启动
        print(f"[warn] 启动时初始化数据库失败: {_e}")

# ==================== 模板初始化 ====================
TEMPLATES_DIR = 'templates'
ADMIN_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, 'admin')

def ensure_templates():
    """确保模板目录存在"""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    os.makedirs(ADMIN_TEMPLATES_DIR, exist_ok=True)

# ==================== 用户加载器 ====================
@login_manager.user_loader
def load_user(user_id):
    from models import db, User
    return db.session.get(User, int(user_id))

# ==================== 启动 ====================
if __name__ == '__main__':
    ensure_templates()
    with app.app_context():
        from utils import init_db
        init_db()
    
    # debug 模式通过 FLASK_DEBUG 环境变量控制，默认关闭（生产安全）
    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    
    from config import print_env_info, ADMIN_USERNAME, ADMIN_PASSWORD
    print_env_info()
    print()
    print(f"服务器运行在 http://127.0.0.1:8000")
    print(f"默认管理员：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    
    if debug_mode:
        print("⚠️  DEBUG 模式已开启，仅限开发环境使用！")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=8000)
