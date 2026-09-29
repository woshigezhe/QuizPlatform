#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 答题接口
"""
from flask import request, session
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime
from models import db, Category, Group, Question, QuizRecord, QuizDetail, UserProgress, User
from utils import check_answer
from . import api_bp
from .auth import _api_error, _api_success


def _question_to_dict(q, include_answer=False):
    result = {
        'id': q.id,
        'type': q.type,
        'content': q.content,
        'image': q.image,
        'options': q.options if q.type in ('single', 'multiple') else [],
        'difficulty': q.difficulty
    }
    if include_answer:
        result['answer'] = q.answer
        result['analysis'] = q.analysis
    return result


def _session_api_error(message, code=400):
    """带 session 清理的错误响应"""
    session.pop('quiz_record_id', None)
    session.pop('question_ids', None)
    session.pop('group_question_ids', None)
    session.pop('current_index', None)
    session.pop('answers', None)
    session.pop('group_mode', None)
    session.pop('groups', None)
    session.pop('current_group', None)
    session.modified = True
    return _api_error(message, code)


# ==================== 首页/分类 ====================
@api_bp.route('/categories', methods=['GET'])
def api_categories():
    categories = Category.query.all()
    result = []
    for cat in categories:
        cat_data = {
            'id': cat.id,
            'name': cat.name,
            'parent_id': cat.parent_id,
            'sort_order': cat.sort_order,
            'question_count': cat.questions.count(),
            'group_count': cat.groups.count()
        }
        if current_user.is_authenticated:
            progress = UserProgress.query.filter_by(
                user_id=current_user.id, category_id=cat.id
            ).first()
            if progress and progress.last_completed_group:
                cat_data['progress'] = {
                    'unlocked_order': progress.last_completed_group.unlock_order,
                    'completed_group_id': progress.last_completed_group.id
                }
            else:
                cat_data['progress'] = {'unlocked_order': 0, 'completed_group_id': None}
        result.append(cat_data)
    return _api_success(data={'categories': result})


# ==================== 随机答题 ====================
@api_bp.route('/quiz/start', methods=['POST'])
@login_required
def api_start_quiz():
    data = request.get_json(silent=True) or {}
    category_id = data.get('category_id')
    if not category_id:
        return _api_error('请指定分类')
    
    category = db.session.get(Category, category_id)
    if not category:
        return _api_error('分类不存在', 404)
    
    questions = Question.query.filter_by(category_id=category_id).order_by(
        db.func.random()
    ).limit(10).all()
    
    if not questions:
        return _api_error('该分类下暂无题目')

    # 标记旧的进行中记录为已放弃（防止孤立数据）
    QuizRecord.query.filter_by(user_id=current_user.id, end_time=None).update(
        {QuizRecord.end_time: datetime.utcnow()}, synchronize_session=False
    )

    record = QuizRecord(
        user_id=current_user.id,
        category_id=category_id,
        total_questions=len(questions)
    )
    db.session.add(record)
    db.session.commit()
    
    session['quiz_record_id'] = record.id
    session['question_ids'] = [q.id for q in questions]
    session['current_index'] = 0
    session['answers'] = {}
    session['group_mode'] = False
    session.modified = True
    
    return _api_success(data={
        'record_id': record.id,
        'total': len(questions),
        'question': _question_to_dict(questions[0]),
        'index': 0
    })


# ==================== 题组答题 ====================
@api_bp.route('/quiz/group/start', methods=['POST'])
@login_required
def api_start_group_quiz():
    data = request.get_json(silent=True) or {}
    category_id = data.get('category_id')
    group_id = data.get('group_id')
    
    if not category_id:
        return _api_error('请指定分类')
    
    category = db.session.get(Category, category_id)
    if not category:
        return _api_error('分类不存在', 404)
    
    all_groups = Group.query.filter_by(category_id=category_id).order_by(
        Group.unlock_order, Group.order
    ).all()
    if not all_groups:
        return _api_error('该分类下没有题组')
    
    group_questions = []
    for g in all_groups:
        qs = Question.query.filter_by(group_id=g.id).all()
        if qs:
            group_questions.append({
                'group_id': g.id,
                'group_name': g.name,
                'category_id': g.category_id,
                'question_ids': [q.id for q in qs]
            })
    
    if not group_questions:
        return _api_error('所有题组下均无题目')
    
    progress = UserProgress.query.filter_by(
        user_id=current_user.id, category_id=category_id
    ).first()
    
    start_index = 0
    # 仅在“继续下一组”（未指定 group_id）时推进；指定 group_id 时应重玩该组而不重置进度
    if progress and progress.last_completed_group_id and not group_id:
        for idx, gq in enumerate(group_questions):
            if gq['group_id'] == progress.last_completed_group_id:
                if idx == len(group_questions) - 1:
                    db.session.delete(progress)
                    db.session.commit()
                    start_index = 0
                else:
                    start_index = idx + 1
                break
    
    if group_id:
        for idx, gq in enumerate(group_questions):
            if gq['group_id'] == group_id:
                if progress and progress.last_completed_group:
                    unlocked_order = progress.last_completed_group.unlock_order
                else:
                    unlocked_order = 0
                target_group = db.session.get(Group, group_id)
                if target_group and (target_group.unlock_order == 0 or target_group.unlock_order <= unlocked_order + 1):
                    start_index = idx
                break
    
    # 标记旧的进行中记录为已放弃，避免悬挂记录
    QuizRecord.query.filter_by(user_id=current_user.id, end_time=None).update(
        {QuizRecord.end_time: datetime.utcnow()}, synchronize_session=False
    )

    current_group = group_questions[start_index]
    record = QuizRecord(
        user_id=current_user.id,
        category_id=category_id,
        total_questions=len(current_group['question_ids'])
    )
    db.session.add(record)
    db.session.commit()
    
    session['quiz_record_id'] = record.id
    session['group_mode'] = True
    session['groups'] = group_questions
    session['current_group'] = start_index
    session['group_question_ids'] = current_group['question_ids']
    session['current_index'] = 0
    session['answers'] = {}
    session.modified = True
    
    first_q = db.session.get(Question, current_group['question_ids'][0])
    
    return _api_success(data={
        'record_id': record.id,
        'group_mode': True,
        'group_name': current_group['group_name'],
        'group_id': current_group['group_id'],
        'total': len(current_group['question_ids']),
        'question': _question_to_dict(first_q),
        'index': 0
    })


# ==================== 获取当前题目 ====================
@api_bp.route('/quiz/question', methods=['GET'])
@login_required
def api_get_question():
    question_ids = session.get('group_question_ids') if session.get('group_mode') else session.get('question_ids')
    if not question_ids:
        return _session_api_error('没有进行中的答题')
    
    current_index = session['current_index']
    if current_index >= len(question_ids):
        return _session_api_error('所有题目已完成')
    
    qid = question_ids[current_index]
    question = db.session.get(Question, qid)
    if not question:
        return _session_api_error('题目不存在')
    
    saved_answer = session.get('answers', {}).get(str(qid))
    
    return _api_success(data={
        'question': _question_to_dict(question),
        'index': current_index,
        'total': len(question_ids),
        'saved_answer': saved_answer,
        'group_mode': session.get('group_mode', False)
    })


# ==================== 保存答案 / 翻题 / 提交 ====================
@api_bp.route('/quiz/answer', methods=['POST'])
@login_required
def api_answer():
    data = request.get_json(silent=True) or {}
    action = data.get('action', 'next')
    qid = data.get('question_id')
    qtype = data.get('type', 'single')
    answer = data.get('answer')
    
    group_mode = session.get('group_mode', False)
    if group_mode:
        question_ids = session.get('group_question_ids', [])
    else:
        question_ids = session.get('question_ids', [])
    
    if not question_ids:
        return _session_api_error('没有进行中的答题')
    
    current_index = session.get('current_index', 0)
    
    if qid is not None and answer is not None:
        try:
            qid_int = int(qid)
        except (TypeError, ValueError):
            return _session_api_error('题目 ID 无效')
        if qid_int not in question_ids:
            return _session_api_error('题目不属于当前答题')
        answers = session.get('answers', {})
        answers[str(qid_int)] = answer
        session['answers'] = answers
        session.modified = True
    
    if action == 'next' and current_index < len(question_ids) - 1:
        session['current_index'] = current_index + 1
        next_qid = question_ids[current_index + 1]
        next_q = db.session.get(Question, next_qid)
        if not next_q:
            return _session_api_error('题目不存在')
        saved = session.get('answers', {}).get(str(next_qid))
        return _api_success(data={
            'question': _question_to_dict(next_q),
            'index': current_index + 1,
            'total': len(question_ids),
            'saved_answer': saved
        })
    elif action == 'prev' and current_index > 0:
        session['current_index'] = current_index - 1
        prev_qid = question_ids[current_index - 1]
        prev_q = db.session.get(Question, prev_qid)
        if not prev_q:
            return _session_api_error('题目不存在')
        saved = session.get('answers', {}).get(str(prev_qid))
        return _api_success(data={
            'question': _question_to_dict(prev_q),
            'index': current_index - 1,
            'total': len(question_ids),
            'saved_answer': saved
        })
    elif action == 'submit':
        if group_mode:
            return _submit_group_internal()
        else:
            return _submit_normal_internal()
    
    return _api_error('无效操作')


def _submit_normal_internal():
    record_id = session.get('quiz_record_id')
    record = db.session.get(QuizRecord, record_id)
    if not record:
        return _session_api_error('答题记录丢失')
    
    total_score = 0
    correct_count = 0
    for qid, user_answer in session.get('answers', {}).items():
        question = db.session.get(Question, int(qid))
        correct = check_answer(question, user_answer) if question else False
        score_earned = 1 if correct else 0
        total_score += score_earned
        if correct:
            correct_count += 1
        detail = QuizDetail(
            record_id=record_id,
            question_id=int(qid),
            user_answer=user_answer,
            is_correct=correct,
            score_earned=score_earned
        )
        db.session.add(detail)
    
    record.end_time = datetime.utcnow()
    record.score = total_score
    record.correct_count = correct_count
    db.session.commit()
    
    keys = ['question_ids', 'group_question_ids', 'current_index', 'answers', 'quiz_record_id', 'group_mode', 'groups', 'current_group']
    for k in keys:
        session.pop(k, None)
    session.modified = True
    
    return _api_success(data={'record_id': record_id})


def _submit_group_internal():
    groups = session.get('groups', [])
    current_group = session.get('current_group', 0)
    
    if current_group >= len(groups):
        return _session_api_error('题组数据异常')
    
    question_ids = groups[current_group]['question_ids']
    group_info = groups[current_group]
    
    all_correct = True
    answers = session.get('answers', {})
    for qid in question_ids:
        qid_str = str(qid)
        if qid_str not in answers:
            all_correct = False
            break
        question = db.session.get(Question, qid)
        if not question:
            all_correct = False
            break
        if not check_answer(question, answers[qid_str]):
            all_correct = False
            break
    
    record_id = session.get('quiz_record_id')
    record = db.session.get(QuizRecord, record_id) if record_id else None
    if not record or record.end_time:
        record = QuizRecord(
            user_id=current_user.id,
            category_id=group_info['category_id'],
            total_questions=len(question_ids)
        )
        db.session.add(record)
        db.session.commit()
    else:
        record.category_id = group_info['category_id']
        record.total_questions = len(question_ids)
    
    correct_count = 0
    for qid in question_ids:
        qid_str = str(qid)
        question = db.session.get(Question, qid)
        user_answer = answers.get(qid_str)
        is_correct = check_answer(question, user_answer) if question and user_answer else False
        if is_correct:
            correct_count += 1
        detail = QuizDetail(
            record_id=record.id,
            question_id=qid,
            user_answer=user_answer,
            is_correct=is_correct,
            score_earned=1 if is_correct else 0
        )
        db.session.add(detail)
    
    record.end_time = datetime.utcnow()
    record.score = correct_count
    record.correct_count = correct_count
    db.session.commit()
    
    if all_correct:
        progress = UserProgress.query.filter_by(
            user_id=current_user.id,
            category_id=group_info['category_id']
        ).first()
        if not progress:
            progress = UserProgress(
                user_id=current_user.id,
                category_id=group_info['category_id']
            )
            db.session.add(progress)
            db.session.flush()

        # 仅向前推进进度：重刷旧题组不应导致解锁状态回退
        completed_group = db.session.get(Group, group_info['group_id'])
        current_order = (progress.last_completed_group.unlock_order
                         if progress.last_completed_group else None)
        if completed_group and (current_order is None
                                or completed_group.unlock_order >= current_order):
            progress.last_completed_group_id = group_info['group_id']
        db.session.commit()
    
    keys = ['question_ids', 'group_question_ids', 'current_index', 'answers', 'quiz_record_id', 'group_mode', 'groups', 'current_group']
    for k in keys:
        session.pop(k, None)
    session.modified = True
    
    return _api_success(data={
        'record_id': record.id,
        'all_correct': all_correct,
        'group_name': group_info['group_name']
    })


# ==================== 答题结果 ====================
@api_bp.route('/quiz/result/<int:record_id>', methods=['GET'])
@login_required
def api_result(record_id):
    record = db.session.get(QuizRecord, record_id,
        options=[joinedload(QuizRecord.details).joinedload(QuizDetail.question),
                 joinedload(QuizRecord.category)])
    
    if not record:
        return _api_error('记录不存在', 404)
    if record.user_id != current_user.id and current_user.role != 'admin':
        return _api_error('无权查看', 403)
    
    details = []
    for d in record.details:
        details.append({
            'id': d.id,
            'question': _question_to_dict(d.question, include_answer=True),
            'user_answer': d.user_answer,
            'is_correct': d.is_correct,
            'score_earned': d.score_earned
        })
    
    seconds = (record.end_time - record.start_time).total_seconds() if record.end_time else 0
    
    all_correct = bool(record.details) and all(d.is_correct for d in record.details)

    return _api_success(data={
        'record': {
            'id': record.id,
            'category_name': record.category.name if record.category else '',
            'category_id': record.category_id,
            'score': record.score,
            'total_questions': record.total_questions,
            'correct_count': record.correct_count,
            'start_time': record.start_time.isoformat() if record.start_time else None,
            'end_time': record.end_time.isoformat() if record.end_time else None,
            'seconds': seconds,
            'minutes': int(seconds // 60),
            'seconds_remainder': round(seconds % 60)
        },
        'details': details,
        'all_correct': all_correct
    })


# ==================== 路线图 ====================
@api_bp.route('/roadmap/<int:category_id>', methods=['GET'])
@login_required
def api_roadmap(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        return _api_error('分类不存在', 404)
    
    groups = Group.query.filter_by(category_id=category_id).order_by(
        Group.unlock_order, Group.order
    ).all()
    
    if not groups:
        return _api_error('该分类下没有题组')
    
    progress = UserProgress.query.filter_by(
        user_id=current_user.id, category_id=category_id
    ).first()
    unlocked_order = progress.last_completed_group.unlock_order if (progress and progress.last_completed_group) else 0
    
    groups_data = []
    for g in groups:
        node_class = 'locked'
        if g.unlock_order == 0:
            node_class = 'unlocked'
        elif g.unlock_order <= unlocked_order:
            node_class = 'completed'
        elif g.unlock_order == unlocked_order + 1:
            node_class = 'current'
        
        groups_data.append({
            'id': g.id,
            'name': g.name,
            'description': g.description,
            'unlock_order': g.unlock_order,
            'background_image': g.background_image,
            'has_study_content': bool(g.study_content),
            'question_count': g.questions.count(),
            'node_class': node_class
        })
    
    return _api_success(data={
        'category': {'id': category.id, 'name': category.name},
        'groups': groups_data,
        'unlocked_order': unlocked_order
    })


# ==================== 学习资料 ====================
@api_bp.route('/study/<int:group_id>', methods=['GET'])
@login_required
def api_study(group_id):
    group = db.session.get(Group, group_id)
    if not group:
        return _api_error('题组不存在', 404)
    
    category = db.session.get(Category, group.category_id)
    progress = UserProgress.query.filter_by(
        user_id=current_user.id, category_id=group.category_id
    ).first()
    unlocked_order = progress.last_completed_group.unlock_order if (progress and progress.last_completed_group) else 0
    
    if group.unlock_order > 0 and group.unlock_order > unlocked_order + 1:
        return _api_error('请先完成前面的题组', 403)
    
    return _api_success(data={
        'group': {
            'id': group.id,
            'name': group.name,
            'description': group.description,
            'study_content': group.study_content,
            'background_image': group.background_image,
            'category_id': group.category_id
        },
        'category': {'id': category.id, 'name': category.name} if category else None
    })


# ==================== 排行版 ====================
@api_bp.route('/leaderboard', methods=['GET'])
def api_leaderboard():
    from sqlalchemy import func
    
    stats = db.session.query(
        User.id,
        User.username,
        func.count(QuizRecord.id).label('total_records'),
        func.coalesce(func.sum(QuizRecord.score), 0).label('total_score'),
        func.coalesce(func.sum(QuizRecord.total_questions), 0).label('total_questions'),
        func.coalesce(func.sum(QuizRecord.correct_count), 0).label('total_correct')
    ).join(QuizRecord, User.id == QuizRecord.user_id, isouter=True
    ).filter(User.status.is_(True)
    ).filter((QuizRecord.id.is_(None)) | (QuizRecord.end_time != None)
    ).group_by(User.id).order_by(func.sum(QuizRecord.score).desc()).all()
    
    ranked_users = []
    for idx, row in enumerate(stats):
        accuracy = round(row.total_correct / row.total_questions * 100, 1) if row.total_questions > 0 else 0.0
        ranked_users.append({
            'rank': idx + 1,
            'user_id': row.id,
            'username': row.username,
            'total_records': row.total_records,
            'total_score': int(row.total_score),
            'total_questions': int(row.total_questions),
            'total_correct': int(row.total_correct),
            'accuracy': accuracy
        })
    
    return _api_success(data={'ranked_users': ranked_users})


# ==================== 历史记录 ====================
@api_bp.route('/history', methods=['GET'])
@login_required
def api_history():
    records = QuizRecord.query.filter_by(user_id=current_user.id).order_by(
        QuizRecord.start_time.desc()
    ).all()
    
    records_data = []
    for r in records:
        records_data.append({
            'id': r.id,
            'category_id': r.category_id,
            'category_name': r.category.name if r.category else '',
            'score': r.score,
            'total_questions': r.total_questions,
            'correct_count': r.correct_count,
            'start_time': r.start_time.isoformat() if r.start_time else None,
            'end_time': r.end_time.isoformat() if r.end_time else None
        })
    
    return _api_success(data={'records': records_data})