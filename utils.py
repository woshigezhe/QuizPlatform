#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助函数
"""
from functools import wraps
from flask import jsonify
from flask_login import current_user
from models import db, User
from config import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL
from werkzeug.security import generate_password_hash

# ==================== 装饰器 ====================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ==================== 业务逻辑 ====================
_TRUE_WORDS = {'对', '正确', '是', '真', 'true', 't', 'yes', 'y', '1', '√'}
_FALSE_WORDS = {'错', '错误', '否', '假', 'false', 'f', 'no', 'n', '0', '×', 'x'}


def _normalize_judge(value):
    """把判断题答案归一化为 True/False；无法识别返回 None。"""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE_WORDS:
        return True
    if text in _FALSE_WORDS:
        return False
    return None


def check_answer(question, user_answer):
    """根据题型判断答案是否正确（兼容“对/错”与“正确/错误”等写法）"""
    if question is None or question.answer is None:
        return False

    answer = question.answer

    if question.type == 'single':
        return user_answer == answer

    elif question.type == 'multiple':
        if user_answer is None:
            return False
        correct = {x for x in str(answer).replace(' ', '').split(',') if x}
        if isinstance(user_answer, str):
            user = {x for x in user_answer.replace(' ', '').split(',') if x}
        else:
            user = set(user_answer)
        return user == correct

    elif question.type == 'judge':
        correct_bool = _normalize_judge(answer)
        user_bool = _normalize_judge(user_answer)
        if correct_bool is None or user_bool is None:
            return str(user_answer).strip() == str(answer).strip()
        return correct_bool == user_bool

    elif question.type == 'fill':
        if user_answer is None:
            return False
        correct_answers = [a.strip().lower() for a in str(answer).split('|') if a.strip()]
        user = str(user_answer).strip().lower()
        return user in correct_answers

    return False

def init_db():
    """创建数据库和默认管理员（单库模式）"""
    db.create_all()

    # 迁移：为 Group / Question 表添加新字段（如果不存在）
    from sqlalchemy import text, inspect
    _migrate_engine = db.engine
    _inspector = inspect(_migrate_engine)
    _quote = _migrate_engine.dialect.identifier_preparer.quote
    _group_tbl = _quote('group')

    def _add_column(table_sql, column_sql, desc):
        with _migrate_engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table_sql} ADD COLUMN {column_sql}"))
            conn.commit()
        print(f"已添加 {desc}")

    if 'group' in _inspector.get_table_names():
        columns = [col['name'] for col in _inspector.get_columns('group')]
        if 'study_content' not in columns:
            _add_column(_group_tbl, 'study_content TEXT', 'group.study_content 列')
        if 'unlock_order' not in columns:
            _add_column(_group_tbl, 'unlock_order INTEGER DEFAULT 0', 'group.unlock_order 列')
        if 'background_image' not in columns:
            _add_column(_group_tbl, 'background_image VARCHAR(255)', 'group.background_image 列')

    if 'question' in _inspector.get_table_names():
        columns = [col['name'] for col in _inspector.get_columns('question')]
        if 'image' not in columns:
            _add_column('question', 'image VARCHAR(255)', 'question.image 列')
    
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print(f"默认管理员已创建：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
