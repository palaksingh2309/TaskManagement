from flask import Blueprint, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models import Employee, Task, Project, ActivityLog, Notification
from app.utils.auth import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/stats', methods=['GET'])
@login_required
def stats():
    today = datetime.utcnow().date()
    today_end = datetime.combine(today, datetime.max.time())

    emp_query = Employee.query.filter(Employee.employment_status == 'active')
    task_query = Task.query.filter(Task.is_archived == False)

    if g.current_user.role == 'employee' and g.current_user.employee:
        task_query = task_query.filter(Task.assigned_to == g.current_user.employee.id)

    total_tasks = task_query.count()
    pending = task_query.filter(Task.status.in_(['not_started', 'in_progress', 'review', 'on_hold'])).count()
    completed = task_query.filter(Task.status == 'completed').count()
    overdue = task_query.filter(Task.status == 'overdue').count()
    today_deadlines = task_query.filter(
        Task.due_date >= datetime.combine(today, datetime.min.time()),
        Task.due_date <= today_end,
        Task.status != 'completed',
    ).count()

    productivity = round((completed / total_tasks * 100) if total_tasks else 0, 1)

    return jsonify({
        'total_employees': emp_query.count() if g.current_user.role != 'employee' else 1,
        'total_tasks': total_tasks,
        'pending_tasks': pending,
        'completed_tasks': completed,
        'overdue_tasks': overdue,
        'today_deadlines': today_deadlines,
        'productivity_score': productivity,
        'active_projects': Project.query.filter(Project.status == 'active').count(),
    })


@dashboard_bp.route('/activity', methods=['GET'])
@login_required
def recent_activity():
    query = ActivityLog.query
    if g.current_user.role == 'employee':
        query = query.filter(ActivityLog.user_id == g.current_user.id)
    logs = query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    return jsonify({'activity': [l.to_dict() for l in logs]})


@dashboard_bp.route('/deadlines', methods=['GET'])
@login_required
def upcoming_deadlines():
    now = datetime.utcnow()
    week_later = now + timedelta(days=7)
    query = Task.query.filter(
        Task.due_date.between(now, week_later),
        Task.status.notin_(['completed', 'cancelled']),
        Task.is_archived == False,
    )
    if g.current_user.role == 'employee' and g.current_user.employee:
        query = query.filter(Task.assigned_to == g.current_user.employee.id)
    tasks = query.order_by(Task.due_date.asc()).limit(10).all()
    return jsonify({'deadlines': [t.to_dict() for t in tasks]})


@dashboard_bp.route('/chart-data', methods=['GET'])
@login_required
def chart_data():
    base_filter = [Task.is_archived == False]
    if g.current_user.role == 'employee' and g.current_user.employee:
        base_filter.append(Task.assigned_to == g.current_user.employee.id)

    status_counts = db.session.query(Task.status, func.count(Task.id)).filter(
        *base_filter
    ).group_by(Task.status).all()
    priority_counts = db.session.query(Task.priority, func.count(Task.id)).filter(
        *base_filter
    ).group_by(Task.priority).all()

    months = []
    completion_trend = []
    for i in range(5, -1, -1):
        month_start = (datetime.utcnow().replace(day=1) - timedelta(days=30 * i))
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        q = Task.query.filter(
            Task.completed_at.between(month_start, month_end),
            Task.status == 'completed',
            *base_filter,
        )
        count = q.count()
        months.append(month_start.strftime('%b'))
        completion_trend.append(count)

    return jsonify({
        'status_distribution': {s: c for s, c in status_counts},
        'priority_distribution': {p: c for p, c in priority_counts},
        'completion_trend': {'labels': months, 'data': completion_trend},
    })
