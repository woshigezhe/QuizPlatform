#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路由模块公共工具：输入验证、文件上传辅助函数
"""
import re
import os
from werkzeug.utils import secure_filename

USERNAME_MIN_LEN = 3
USERNAME_MAX_LEN = 20
PASSWORD_MIN_LEN = 6
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_\u4e00-\u9fff]+$')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}


def validate_registration(username, email, password):
    errors = []

    username = username.strip() if username else ''
    email = email.strip() if email else ''

    if not username:
        errors.append('用户名不能为空')
    elif len(username) < USERNAME_MIN_LEN or len(username) > USERNAME_MAX_LEN:
        errors.append(f'用户名长度需在 {USERNAME_MIN_LEN}-{USERNAME_MAX_LEN} 个字符之间')
    elif not USERNAME_REGEX.match(username):
        errors.append('用户名只能包含字母、数字、下划线和中文')

    if not email:
        errors.append('邮箱不能为空')
    elif not EMAIL_REGEX.match(email):
        errors.append('邮箱格式不正确')

    if not password:
        errors.append('密码不能为空')
    elif len(password) < PASSWORD_MIN_LEN:
        errors.append(f'密码长度不能少于 {PASSWORD_MIN_LEN} 个字符')

    return errors


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def handle_background_image_upload(request_files):
    file = request_files.get('background_image')
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_dir = os.path.join('static', 'uploads', 'backgrounds')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        return os.path.join('static', 'uploads', 'backgrounds', filename).replace('\\', '/')
    return None


def handle_question_image_upload(request_files):
    file = request_files.get('question_image')
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_dir = os.path.join('static', 'uploads', 'questions')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        return os.path.join('static', 'uploads', 'questions', filename).replace('\\', '/')
    return None
