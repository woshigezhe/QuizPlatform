#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路由模块
"""
from .auth import auth_bp
from .quiz import quiz_bp
from .admin import admin_bp

def register_routes(app):
    """注册所有路由蓝图"""
    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(quiz_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from flask_login import current_user, logout_user
    from flask import flash, redirect, url_for

    @app.before_request
    def check_user_active():
        if current_user.is_authenticated and not current_user.status:
            logout_user()
            flash('账号已被禁用', 'warning')
            return redirect(url_for('auth.auth_login'))
