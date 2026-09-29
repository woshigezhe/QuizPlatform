#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路由模块公共工具：输入验证、文件上传辅助函数
"""
import os
import re
import uuid
import zipfile
import functools
from flask import jsonify

USERNAME_MIN_LEN = 3
USERNAME_MAX_LEN = 20
PASSWORD_MIN_LEN = 6
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_\u4e00-\u9fff]+$')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}


# ==================== 输入校验辅助 ====================
class ValidationError(ValueError):
    """参数校验失败，路由层捕获后统一返回 400。"""


def require_int(value, name='参数', default=None, min_value=None, max_value=None):
    """解析并校验整数字段；失败抛出 ValidationError。"""
    if value is None or value == '':
        if default is not None:
            return default
        raise ValidationError(f'{name}不能为空')
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f'{name}必须为整数')
    if min_value is not None and result < min_value:
        raise ValidationError(f'{name}不能小于 {min_value}')
    if max_value is not None and result > max_value:
        raise ValidationError(f'{name}不能大于 {max_value}')
    return result


def optional_int(value, default=None):
    """宽松解析可选整数；无法转换时返回 default（不抛异常）。"""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def require_int_list(value, name='参数'):
    """解析正整数 ID 列表，过滤非法项；结果为空时抛错。"""
    if not isinstance(value, (list, tuple)):
        raise ValidationError(f'{name}格式不正确')
    result = []
    for item in value:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue
    if not result:
        raise ValidationError(f'{name}不能为空')
    return result


def validate_api(f):
    """捕获 ValidationError，统一返回 400 JSON。"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
    return wrapper


def unique_filename(original_name):
    """基于 UUID 生成安全的唯一文件名，保留原扩展名（兼容中文名）。"""
    ext = ''
    if original_name and '.' in original_name:
        ext = original_name.rsplit('.', 1)[1].lower()
        if not re.fullmatch(r'[a-z0-9]{1,8}', ext):
            ext = ''
    return f"{uuid.uuid4().hex}{'.' + ext if ext else ''}"


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
        filename = unique_filename(file.filename)
        upload_dir = os.path.join('static', 'uploads', 'backgrounds')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        return os.path.join('static', 'uploads', 'backgrounds', filename).replace('\\', '/')
    return None


def handle_question_image_upload(request_files):
    file = request_files.get('question_image')
    if file and file.filename and allowed_file(file.filename):
        filename = unique_filename(file.filename)
        upload_dir = os.path.join('static', 'uploads', 'questions')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        return os.path.join('static', 'uploads', 'questions', filename).replace('\\', '/')
    return None


def safe_extract_zip(zf, dest_dir):
    """安全解压 zip，防止 Zip Slip 路径穿越。

    逐条校验成员路径必须落在 dest_dir 内，否则抛出 ValueError。
    返回成功写出的文件数。
    """
    dest_abs = os.path.realpath(dest_dir)
    count = 0
    for member in zf.infolist():
        name = member.filename
        if not name or name.endswith('/'):
            continue
        target = os.path.realpath(os.path.join(dest_abs, name))
        if target != dest_abs and not target.startswith(dest_abs + os.sep):
            raise ValueError(f'压缩包包含非法路径，已拒绝解压: {name}')
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with zf.open(member) as src, open(target, 'wb') as dst:
            dst.write(src.read())
        count += 1
    return count
