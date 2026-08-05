#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 认证接口
"""
from flask import request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from . import api_bp
from ..shared import validate_registration


def _api_error(message, code=400):
    return jsonify({'success': False, 'message': message}), code


def _api_success(data=None, message='ok'):
    resp = {'success': True, 'message': message}
    if data is not None:
        resp['data'] = data
    return jsonify(resp)


@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    errors = validate_registration(username, email, password)
    if errors:
        return _api_error('; '.join(errors))
    
    if User.query.filter_by(username=username).first():
        return _api_error('用户名已存在')
    if User.query.filter_by(email=email).first():
        return _api_error('该邮箱已被注册')
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()
    return _api_success(message='注册成功，请登录')


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return _api_error('请输入用户名和密码')
    
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return _api_error('用户名或密码错误', 401)
    
    if not user.status:
        return _api_error('账号已被禁用', 403)
    
    login_user(user, remember=data.get('remember', False))
    return _api_success(data={
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    })


@api_bp.route('/auth/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return _api_success(message='已退出登录')


@api_bp.route('/auth/me', methods=['GET'])
def api_me():
    if current_user.is_authenticated:
        return _api_success(data={
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'role': current_user.role
            }
        })
    return _api_success(data={'user': None})