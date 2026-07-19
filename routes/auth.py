#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证路由：登录、注册、退出
"""
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)

# 输入验证常量
USERNAME_MIN_LEN = 3
USERNAME_MAX_LEN = 20
PASSWORD_MIN_LEN = 6
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_\u4e00-\u9fff]+$')


def _validate_registration(username, email, password):
    """验证注册表单输入，返回错误信息列表"""
    errors = []
    
    # 用户名验证
    username = username.strip()
    if not username:
        errors.append('用户名不能为空')
    elif len(username) < USERNAME_MIN_LEN or len(username) > USERNAME_MAX_LEN:
        errors.append(f'用户名长度需在 {USERNAME_MIN_LEN}-{USERNAME_MAX_LEN} 个字符之间')
    elif not USERNAME_REGEX.match(username):
        errors.append('用户名只能包含字母、数字、下划线和中文')
    
    # 邮箱验证
    email = email.strip()
    if not email:
        errors.append('邮箱不能为空')
    elif not EMAIL_REGEX.match(email):
        errors.append('邮箱格式不正确')
    
    # 密码验证
    if not password:
        errors.append('密码不能为空')
    elif len(password) < PASSWORD_MIN_LEN:
        errors.append(f'密码长度不能少于 {PASSWORD_MIN_LEN} 个字符')
    
    return errors


@auth_bp.route('/register', methods=['GET', 'POST'])
def auth_register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # 输入验证
        errors = _validate_registration(username, email, password)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('auth.auth_register'))
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('auth.auth_register'))
        if User.query.filter_by(email=email).first():
            flash('该邮箱已被注册')
            return redirect(url_for('auth.auth_register'))
        
        user = User(username=username, email=email,
                    password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录')
        return redirect(url_for('auth.auth_login'))
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('请输入用户名和密码')
            return redirect(url_for('auth.auth_login'))
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.status:
                flash('账号已被禁用')
                return redirect(url_for('auth.auth_login'))
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('quiz.index'))
        flash('用户名或密码错误')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def auth_logout():
    logout_user()
    return redirect(url_for('quiz.index'))
