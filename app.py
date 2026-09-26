#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在线答题系统 - 主入口（后端 API 服务）

前端为 Vue SPA（构建产物 frontend/dist，由 nginx 托管），
本服务仅提供 RESTful API（/api）与静态资源（/static）。
"""
from flask import Flask, jsonify
from flask_login import LoginManager, current_user, logout_user
from config import Config
from models import db
from routes.api import register_api
import os

# ==================== 初始化应用 ====================
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# 初始化扩展
db.init_app(app)
login_manager = LoginManager(app)


@login_manager.unauthorized_handler
def unauthorized_handler():
    """未登录统一返回 401 JSON（本服务只提供 API）。"""
    return jsonify({'success': False, 'message': '请先登录'}), 401


# ==================== 注册 API ====================
register_api(app)


# ==================== 账号禁用即时生效 ====================
@app.before_request
def check_user_active():
    if current_user.is_authenticated and not current_user.status:
        logout_user()
        return jsonify({'success': False, 'message': '账号已被禁用'}), 401


# ==================== 数据库初始化 ====================
# gunicorn 下不会进入 __main__，需在导入时确保建表与迁移（配合 --preload 只执行一次）
if __name__ != '__main__':
    try:
        from utils import init_db
        with app.app_context():
            init_db()
    except Exception as _e:  # 数据库暂时不可用时不阻塞启动
        print(f"[warn] 启动时初始化数据库失败: {_e}")


# ==================== 用户加载器 ====================
@login_manager.user_loader
def load_user(user_id):
    from models import db, User
    return db.session.get(User, int(user_id))


# ==================== 本地开发启动 ====================
if __name__ == '__main__':
    with app.app_context():
        from utils import init_db
        init_db()

    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')

    from config import print_env_info, ADMIN_USERNAME, ADMIN_PASSWORD
    print_env_info()
    print()
    print("服务器运行在 http://127.0.0.1:8000")
    print(f"默认管理员：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    if debug_mode:
        print("⚠️  DEBUG 模式已开启，仅限开发环境使用！")

    app.run(debug=debug_mode, host='0.0.0.0', port=8000)
