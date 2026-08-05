#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 管理后台接口
"""
from flask import request, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from io import BytesIO
import os
import shutil
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None
import zipfile
from models import db, User, Category, Group, Question, QuizRecord, QuizDetail, UserProgress
from utils import admin_required
from . import api_bp
from .auth import _api_error, _api_success
from ..shared import allowed_file as _allowed_file, handle_background_image_upload, handle_question_image_upload

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}


def _handle_bg_image():
    return handle_background_image_upload(request.files)


def _handle_q_image():
    return handle_question_image_upload(request.files)


# ==================== 分类管理 ====================
@api_bp.route('/admin/categories', methods=['GET'])
@login_required
@admin_required
def api_admin_categories():
    cats = Category.query.all()
    result = []
    for c in cats:
        result.append({
            'id': c.id,
            'name': c.name,
            'parent_id': c.parent_id,
            'sort_order': c.sort_order,
            'question_count': c.questions.count(),
            'group_count': c.groups.count()
        })
    return _api_success(data={'categories': result})


@api_bp.route('/admin/categories', methods=['POST'])
@login_required
@admin_required
def api_admin_category_add():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    if not name:
        return _api_error('分类名称不能为空')
    cat = Category(name=name, parent_id=data.get('parent_id'))
    db.session.add(cat)
    db.session.commit()
    return _api_success(data={'id': cat.id, 'name': cat.name}, message='分类添加成功')


@api_bp.route('/admin/categories/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def api_admin_category_delete(id):
    cat = db.session.get(Category, id)
    if not cat:
        return _api_error('分类不存在', 404)
    
    # 清理关联数据：答题详情 → 答题记录 → 题目 → 分组 → 用户进度 → 分类
    question_ids = [q.id for q in Question.query.filter_by(category_id=id).all()]
    if question_ids:
        QuizDetail.query.filter(QuizDetail.question_id.in_(question_ids)).delete(synchronize_session=False)
    
    record_ids = [r.id for r in QuizRecord.query.filter_by(category_id=id).all()]
    if record_ids:
        QuizDetail.query.filter(QuizDetail.record_id.in_(record_ids)).delete(synchronize_session=False)
    
    QuizRecord.query.filter_by(category_id=id).delete(synchronize_session=False)
    Question.query.filter_by(category_id=id).delete(synchronize_session=False)
    Group.query.filter_by(category_id=id).delete(synchronize_session=False)
    UserProgress.query.filter_by(category_id=id).delete(synchronize_session=False)
    
    db.session.delete(cat)
    db.session.commit()
    return _api_success(message='分类已删除')


# ==================== 分组管理 ====================
@api_bp.route('/admin/groups', methods=['GET'])
@login_required
@admin_required
def api_admin_groups():
    groups = Group.query.all()
    result = []
    for g in groups:
        result.append({
            'id': g.id,
            'name': g.name,
            'category_id': g.category_id,
            'category_name': g.category.name if g.category else '',
            'order': g.order,
            'description': g.description,
            'study_content': g.study_content,
            'unlock_order': g.unlock_order,
            'background_image': g.background_image,
            'question_count': g.questions.count()
        })
    return _api_success(data={'groups': result})


@api_bp.route('/admin/groups', methods=['POST'])
@login_required
@admin_required
def api_admin_group_add():
    if request.is_json:
        data = request.get_json()
        background_image = data.get('background_image')
    else:
        data = request.form
        background_image = _handle_bg_image()
    
    name = data.get('name', '').strip()
    if not name:
        return _api_error('分组名称不能为空')
    
    group = Group(
        name=name,
        category_id=data.get('category_id'),
        order=int(data.get('order', 0)),
        description=data.get('description', ''),
        study_content=data.get('study_content', ''),
        unlock_order=int(data.get('unlock_order', 0)),
        background_image=background_image
    )
    db.session.add(group)
    db.session.commit()
    return _api_success(data={'id': group.id, 'name': group.name}, message='分组添加成功')


@api_bp.route('/admin/groups/<int:id>', methods=['PUT'])
@login_required
@admin_required
def api_admin_group_edit(id):
    group = db.session.get(Group, id)
    if not group:
        return _api_error('分组不存在', 404)
    
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    group.name = data.get('name', group.name)
    group.category_id = data.get('category_id', group.category_id)
    group.order = int(data.get('order', group.order))
    group.description = data.get('description', group.description)
    group.study_content = data.get('study_content', group.study_content)
    group.unlock_order = int(data.get('unlock_order', group.unlock_order))
    
    bg_image = _handle_bg_image()
    if bg_image:
        group.background_image = bg_image
    
    db.session.commit()
    return _api_success(data={'id': group.id, 'name': group.name}, message='分组更新成功')


@api_bp.route('/admin/groups/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def api_admin_group_delete(id):
    group = db.session.get(Group, id)
    if not group:
        return _api_error('分组不存在', 404)
    Question.query.filter_by(group_id=id).update({Question.group_id: None})
    db.session.delete(group)
    db.session.commit()
    return _api_success(message='分组已删除')


# ==================== 题目管理 ====================
@api_bp.route('/admin/questions', methods=['GET'])
@login_required
@admin_required
def api_admin_questions():
    category_id = request.args.get('category_id', type=int)
    group_id = request.args.get('group_id', type=int)
    
    query = Question.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    if group_id:
        query = query.filter_by(group_id=group_id)
    
    questions = query.order_by(Question.id.desc()).all()
    result = []
    for q in questions:
        result.append({
            'id': q.id,
            'category_id': q.category_id,
            'category_name': q.category.name if q.category else '',
            'group_id': q.group_id,
            'group_name': q.group.name if q.group else '',
            'type': q.type,
            'content': q.content,
            'image': q.image,
            'options': q.options,
            'answer': q.answer,
            'analysis': q.analysis,
            'difficulty': q.difficulty
        })
    
    categories = [{'id': c.id, 'name': c.name} for c in Category.query.all()]
    
    return _api_success(data={'questions': result, 'categories': categories})


@api_bp.route('/admin/questions', methods=['POST'])
@login_required
@admin_required
def api_admin_question_add():
    if request.is_json:
        data = request.get_json()
        image = data.get('image')
    else:
        data = request.form
        image = _handle_q_image()
    
    qtype = data.get('type', '').strip().lower()
    content = data.get('content', '').strip()
    if not content:
        return _api_error('题目内容不能为空')
    if qtype not in ('single', 'multiple', 'judge', 'fill'):
        return _api_error('无效的题型')
    
    options = data.get('options', [])
    if isinstance(options, str):
        options = [line.strip() for line in options.splitlines() if line.strip()]
    
    q = Question(
        category_id=data.get('category_id'),
        group_id=data.get('group_id') or None,
        type=qtype,
        content=content,
        image=image,
        options=options if qtype not in ('judge', 'fill') else [],
        answer=data.get('answer', ''),
        analysis=data.get('analysis', ''),
        difficulty=int(data.get('difficulty', 1))
    )
    db.session.add(q)
    db.session.commit()
    return _api_success(data={'id': q.id}, message='题目添加成功')


@api_bp.route('/admin/questions/<int:id>', methods=['PUT'])
@login_required
@admin_required
def api_admin_question_edit(id):
    q = db.session.get(Question, id)
    if not q:
        return _api_error('题目不存在', 404)
    
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    q.category_id = data.get('category_id', q.category_id)
    q.group_id = data.get('group_id') or None
    q.type = data.get('type', q.type)
    q.content = data.get('content', q.content)
    
    options = data.get('options', q.options)
    if isinstance(options, str):
        options = [line.strip() for line in options.splitlines() if line.strip()]
    q.options = options if q.type not in ('judge', 'fill') else []
    
    q.answer = data.get('answer', q.answer)
    q.analysis = data.get('analysis', q.analysis)
    q.difficulty = int(data.get('difficulty', q.difficulty))
    
    image = _handle_q_image()
    if image:
        q.image = image
    
    db.session.commit()
    return _api_success(data={'id': q.id}, message='题目更新成功')


@api_bp.route('/admin/questions/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def api_admin_question_delete(id):
    q = db.session.get(Question, id)
    if not q:
        return _api_error('题目不存在', 404)
    db.session.delete(q)
    db.session.commit()
    return _api_success(message='题目已删除')


@api_bp.route('/admin/questions/bulk-delete', methods=['POST'])
@login_required
@admin_required
def api_admin_questions_bulk_delete():
    data = request.get_json(silent=True) or {}
    question_ids = data.get('ids', [])
    if not question_ids:
        return _api_error('请至少选择一道题目')
    
    QuizDetail.query.filter(QuizDetail.question_id.in_(question_ids)).delete(synchronize_session=False)
    Question.query.filter(Question.id.in_(question_ids)).delete(synchronize_session=False)
    db.session.commit()
    
    return _api_success(message=f'成功删除 {len(question_ids)} 道题目')


# ==================== 批量导入 ====================
@api_bp.route('/admin/import', methods=['POST'])
@login_required
@admin_required
def api_admin_import():
    file = request.files.get('file')
    if not file:
        return _api_error('请选择文件')
    
    is_zip = file.filename.endswith('.zip')
    is_single = file.filename.endswith(('.xlsx', '.xls', '.csv'))
    
    if not (is_zip or is_single):
        return _api_error('请上传 .zip 压缩包 或 .xlsx/.xls/.csv 文件')
    
    filename = secure_filename(file.filename)
    filepath = os.path.join('uploads', filename)
    file.save(filepath)
    
    temp_dir = None
    data_filepath = None
    
    try:
        if is_zip:
            temp_dir = os.path.join('uploads', f'_import_{int(datetime.utcnow().timestamp())}')
            os.makedirs(temp_dir, exist_ok=True)
            
            with zipfile.ZipFile(filepath, 'r') as zf:
                zf.extractall(temp_dir)
            
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if f.endswith(('.xlsx', '.xls', '.csv')):
                        data_filepath = os.path.join(root, f)
                    elif f.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS:
                        src = os.path.join(root, f)
                        img_dir = os.path.join('static', 'uploads', 'questions')
                        os.makedirs(img_dir, exist_ok=True)
                        img_dest = os.path.join(img_dir, secure_filename(f))
                        shutil.copy2(src, img_dest)
            
            if not data_filepath:
                return _api_error('压缩包中未找到 Excel 或 CSV 文件')
        else:
            data_filepath = filepath
        
        df = pd.read_excel(data_filepath) if data_filepath.endswith(('.xlsx','xls')) else pd.read_csv(data_filepath)
        add_count = 0
        update_count = 0
        
        for _, row in df.iterrows():
            cat_name = row['分类名称']
            category = Category.query.filter_by(name=cat_name).first()
            if not category:
                category = Category(name=cat_name)
                db.session.add(category)
                db.session.flush()
            
            group_name = row.get('分组名称', '')
            group_id = None
            if pd.notna(group_name) and str(group_name).strip():
                group_name = str(group_name).strip()
                group = Group.query.filter_by(name=group_name, category_id=category.id).first()
                if not group:
                    group = Group(name=group_name, category_id=category.id)
                    db.session.add(group)
                    db.session.flush()
                group_id = group.id
            
            qtype = str(row['题型']).strip().lower()
            if qtype not in ['single', 'multiple', 'judge', 'fill']:
                continue
            
            opts = str(row['选项']).split('|') if pd.notna(row.get('选项')) else []
            answer = str(row['正确答案']).strip()
            content = str(row['题干']).strip()
            analysis = str(row.get('解析', '')).strip() if pd.notna(row.get('解析')) else ''
            difficulty = int(row.get('难度', 1)) if pd.notna(row.get('难度')) else 1
            
            image_filename = str(row.get('题目图片', '')).strip() if pd.notna(row.get('题目图片')) else ''
            image = None
            if image_filename:
                img_path = os.path.join('static', 'uploads', 'questions', secure_filename(image_filename))
                if os.path.exists(img_path):
                    image = img_path.replace('\\', '/')
            
            existing = Question.query.filter_by(category_id=category.id, content=content).first()
            if existing:
                existing.type = qtype
                existing.options = opts
                existing.answer = answer
                existing.analysis = analysis
                existing.difficulty = difficulty
                existing.group_id = group_id
                if image:
                    existing.image = image
                update_count += 1
            else:
                q = Question(
                    category_id=category.id, group_id=group_id, type=qtype,
                    content=content, image=image, options=opts,
                    answer=answer, analysis=analysis, difficulty=difficulty
                )
                db.session.add(q)
                add_count += 1
        
        db.session.commit()
        return _api_success(data={'added': add_count, 'updated': update_count},
                          message=f'导入完成：新增 {add_count} 道，更新 {update_count} 道')
    except Exception as e:
        db.session.rollback()
        return _api_error(f'导入失败：{str(e)}')
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


# ==================== 导出数据 ====================
@api_bp.route('/admin/export', methods=['GET'])
@login_required
@admin_required
def api_admin_export():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category_id = request.args.get('category_id', type=int)
    username = request.args.get('username')
    
    query = QuizRecord.query.join(User).join(Category)
    if start_date:
        try:
            query = query.filter(QuizRecord.start_time >= datetime.strptime(start_date, '%Y-%m-%d'))
        except ValueError:
            return _api_error('开始日期格式无效，请使用 YYYY-MM-DD 格式')
    if end_date:
        try:
            query = query.filter(QuizRecord.start_time <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
        except ValueError:
            return _api_error('结束日期格式无效，请使用 YYYY-MM-DD 格式')
    if category_id:
        query = query.filter(QuizRecord.category_id == category_id)
    if username:
        query = query.filter(User.username.contains(username))
    
    records = query.all()
    
    data = []
    for rec in records:
        data.append({
            '用户名': rec.user.username,
            '开始时间': rec.start_time.strftime('%Y-%m-%d %H:%M:%S') if rec.start_time else '',
            '结束时间': rec.end_time.strftime('%Y-%m-%d %H:%M:%S') if rec.end_time else '',
            '分类': rec.category.name,
            '得分': rec.score,
            '正确题数': rec.correct_count,
            '总题数': rec.total_questions,
            '用时 (秒)': (rec.end_time - rec.start_time).total_seconds() if rec.end_time else None
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='汇总')
        details_data = []
        for rec in records:
            for det in rec.details:
                details_data.append({
                    '记录 ID': rec.id,
                    '用户名': rec.user.username,
                    '题目': det.question.content,
                    '用户答案': det.user_answer,
                    '正确答案': det.question.answer,
                    '是否正确': det.is_correct,
                    '得分': det.score_earned
                })
        if details_data:
            df_details = pd.DataFrame(details_data)
            df_details.to_excel(writer, index=False, sheet_name='详情')
    output.seek(0)
    
    return send_file(output,
                     download_name=f'答题记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                     as_attachment=True)


# ==================== 用户管理 ====================
@api_bp.route('/admin/users', methods=['GET'])
@login_required
@admin_required
def api_admin_users():
    users = User.query.all()
    result = []
    for u in users:
        result.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'status': u.status,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'record_count': u.quiz_records.count()
        })
    return _api_success(data={'users': result})


@api_bp.route('/admin/users/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def api_admin_toggle_user(id):
    user = db.session.get(User, id)
    if not user:
        return _api_error('用户不存在', 404)
    if user.id == current_user.id:
        return _api_error('不能禁用自己')
    user.status = not user.status
    db.session.commit()
    return _api_success(data={'status': user.status}, message=f'用户 {user.username} 状态已切换')


@api_bp.route('/admin/users/<int:id>/clear-history', methods=['POST'])
@login_required
@admin_required
def api_admin_clear_user_history(id):
    user = db.session.get(User, id)
    if not user:
        return _api_error('用户不存在', 404)
    if user.id == current_user.id:
        return _api_error('不能清除自己的历史数据')
    
    records = QuizRecord.query.filter_by(user_id=user.id).all()
    record_ids = [r.id for r in records]
    if record_ids:
        QuizDetail.query.filter(QuizDetail.record_id.in_(record_ids)).delete(synchronize_session=False)
        QuizRecord.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    
    UserProgress.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return _api_success(message=f'已清除用户 {user.username} 的所有答题历史数据')


@api_bp.route('/admin/users/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def api_admin_delete_user(id):
    user = db.session.get(User, id)
    if not user:
        return _api_error('用户不存在', 404)
    if user.id == current_user.id:
        return _api_error('不能删除自己')
    
    records = QuizRecord.query.filter_by(user_id=user.id).all()
    record_ids = [r.id for r in records]
    if record_ids:
        QuizDetail.query.filter(QuizDetail.record_id.in_(record_ids)).delete(synchronize_session=False)
        QuizRecord.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    
    UserProgress.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    return _api_success(message=f'用户 {user.username} 及其所有数据已删除')