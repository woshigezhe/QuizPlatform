#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型

数据分离策略（通过 SQLAlchemy binds 实现）：
  - bind 'config':  Category, Group, Question（题库配置）
  - bind 'users':   User（用户账号）
  - bind 'records': QuizRecord, QuizDetail, UserProgress（答题记录 / 用户进度）

默认情况下所有 bind 指向同一 SQLite 文件 quiz.db（兼容原有行为），
跨模型 JOIN 和外键约束正常工作。
生产环境可通过环境变量分别指定独立数据库实现物理分离：
  CONFIG_DATABASE_URL  → 题库配置独立存储
  USERS_DATABASE_URL   → 用户数据独立存储
  RECORDS_DATABASE_URL → 答题记录独立存储

注意：当 bind 指向不同物理数据库（尤其是不同 SQLite 文件）时，
跨 bind 的外键约束将失效，需由应用层保证数据一致性。
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __bind_key__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Boolean, default=True)

    quiz_records = db.relationship('QuizRecord', backref='user', lazy='dynamic',
                                   foreign_keys='QuizRecord.user_id')
    progresses = db.relationship('UserProgress', backref='user', lazy='dynamic',
                                 foreign_keys='UserProgress.user_id')


class Category(db.Model):
    __bind_key__ = 'config'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    parent = db.relationship('Category', remote_side=[id], backref='children')
    questions = db.relationship('Question', backref='category', lazy='dynamic',
                                foreign_keys='Question.category_id')
    groups = db.relationship('Group', backref='category', lazy='dynamic',
                             foreign_keys='Group.category_id')
    quiz_records = db.relationship('QuizRecord', backref='category', lazy='dynamic',
                                   foreign_keys='QuizRecord.category_id')


class Group(db.Model):
    """题目分组"""
    __bind_key__ = 'config'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    order = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    study_content = db.Column(db.Text)  # 学习资料（Markdown/HTML）
    unlock_order = db.Column(db.Integer, default=0)  # 解锁序号，0=无需解锁
    background_image = db.Column(db.String(255))  # 背景图片路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question', backref='group', lazy='dynamic',
                                foreign_keys='Question.group_id')


class Question(db.Model):
    __bind_key__ = 'config'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False)   # single, multiple, judge, fill
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))  # 题目配图路径
    options = db.Column(db.JSON)
    answer = db.Column(db.String(500))
    analysis = db.Column(db.Text)
    difficulty = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    details = db.relationship('QuizDetail', backref='question', lazy='dynamic',
                              foreign_keys='QuizDetail.question_id')


class QuizRecord(db.Model):
    __bind_key__ = 'records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    score = db.Column(db.Float, default=0)
    total_questions = db.Column(db.Integer)
    correct_count = db.Column(db.Integer, default=0)

    details = db.relationship('QuizDetail', backref='record', lazy='select',
                              cascade='all, delete-orphan',
                              foreign_keys='QuizDetail.record_id')


class QuizDetail(db.Model):
    __bind_key__ = 'records'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('quiz_record.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_answer = db.Column(db.JSON)
    is_correct = db.Column(db.Boolean)
    score_earned = db.Column(db.Float, default=0)


class UserProgress(db.Model):
    """用户分组答题进度"""
    __bind_key__ = 'records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    last_completed_group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'category_id', name='unique_user_category'),)

    last_completed_group = db.relationship('Group',
                                           foreign_keys='UserProgress.last_completed_group_id')