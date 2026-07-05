from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.models import Task, Employee
from app.utils.auth import login_required, role_required, paginate_query
from app.models import ActivityLog

calendar_bp = Blueprint('calendar', __name__)
audit_bp = Blueprint('audit', __name__)


@calendar_bp.route('', methods=['GET'])
@login_required
def calendar_events():
    from flask import g
    view = request.args.get('view', 'month')
    date_str = request.args.get('date', datetime.utcnow().isoformat())
    ref_date = datetime.fromisoformat(date_str.replace('Z', ''))

    if view == 'month':
        start = ref_date.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
    elif view == 'week':
        start = ref_date - timedelta(days=ref_date.weekday())
        end = start + timedelta(days=7)
    else:
        start = ref_date.replace(hour=0, minute=0, second=0)
        end = start + timedelta(days=1)

    query = Task.query.filter(
        Task.due_date.between(start, end),
        Task.is_archived == False,
    )
    if g.current_user.role == 'employee' and g.current_user.employee:
        query = query.filter(Task.assigned_to == g.current_user.employee.id)

    tasks = query.all()
    events = [{
        'id': t.id,
        'title': t.title,
        'start': t.due_date.isoformat() if t.due_date else None,
        'status': t.status,
        'priority': t.priority,
        'assignee': t.assignee.full_name if t.assignee else None,
        'color': {'low': '#10B981', 'medium': '#3B82F6', 'high': '#F59E0B', 'critical': '#EF4444'}.get(t.priority, '#3B82F6'),
    } for t in tasks]

    workload = {}
    for t in tasks:
        if t.assignee:
            name = t.assignee.full_name
            workload[name] = workload.get(name, 0) + 1

    return jsonify({'events': events, 'workload': workload, 'view': view})


@audit_bp.route('', methods=['GET'])
@role_required('admin')
def audit_logs():
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 20)
    action = request.args.get('action')
    entity_type = request.args.get('entity_type')

    query = ActivityLog.query
    if action:
        query = query.filter(ActivityLog.action.ilike(f'%{action}%'))
    if entity_type:
        query = query.filter(ActivityLog.entity_type == entity_type)
    query = query.order_by(ActivityLog.created_at.desc())
    result = paginate_query(query, page, per_page)
    return jsonify({
        'logs': [l.to_dict() for l in result['items']],
        'pagination': {k: v for k, v in result.items() if k != 'items'},
    })
