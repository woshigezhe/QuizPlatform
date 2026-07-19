#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 蓝图 - 前后端分离 RESTful API
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from . import auth, quiz, admin  # noqa: E402,F401


def register_api(app):
    """注册 API 蓝图"""
    app.register_blueprint(api_bp)