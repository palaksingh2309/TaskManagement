from flask import Blueprint, request, jsonify, g
from datetime import datetime
from sqlalchemy import or_
from app.extensions import db
from app.models import Task, Subtask, Comment, TaskHistory, Notification, Employee
from app.utils.auth import login_required, role_required, log_activity, paginate_query

tasks_bp = Blueprint('tasks', __name__)

STATUSES = ['not_started', 'in_progress', 'review', 'completed', 'cancelled', 'on_hold', 'overdue']
PRIORITIES = ['low', 'medium', 'high', 'critical']


def _check_overdue():
    now = datetime.utcnow()
    overdue_tasks = Task.query.filter(
        Task.due_date < now,
        Task.status.notin_(['completed', 'cancelled']),
        Task.is_archived == False,
    ).all()
    for task in overdue_tasks:
        if task.status != 'overdue':
            task.status = 'overdue'
    db.session.commit()


def _task_query_for_user():
    query = Task.query.filter(Task.is_archived == False)
    if g.current_user.role == 'employee':
        emp = g.current_user.employee
        if emp:
            query = query.filter(Task.assigned_to == emp.id)
    return query


def _can_access_task(task):
    if g.current_user.role in ('admin', 'manager'):
        return True
    emp = g.current_user.employee
    return emp and task.assigned_to == emp.id


@tasks_bp.route('', methods=['GET'])
@login_required
def list_tasks():
    _check_overdue()
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 20)
    search = request.args.get('search', '')
    status = request.args.get('status')
    priority = request.args.get('priority')
    project_id = request.args.get('project_id')
    assigned_to = request.args.get('assigned_to')
    view = request.args.get('view', 'list')
    sort_by = request.args.get('sort_by', 'updated_at')
    sort_order = request.args.get('sort_order', 'desc')

    query = _task_query_for_user()
    if search:
        query = query.filter(or_(Task.title.ilike(f'%{search}%'), Task.description.ilike(f'%{search}%')))
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)

    sort_col = getattr(Task, sort_by, Task.updated_at)
    query = query.order_by(sort_col.desc() if sort_order == 'desc' else sort_col.asc())

    if view == 'kanban':
        tasks = query.all()
        board = {s: [] for s in STATUSES}
        for t in tasks:
            board[t.status].append(t.to_dict())
        return jsonify({'board': board})

    result = paginate_query(query, page, per_page)
    return jsonify({
        'tasks': [t.to_dict() for t in result['items']],
        'pagination': {k: v for k, v in result.items() if k != 'items'},
    })


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not _can_access_task(task):
        return jsonify({'error': 'Permission denied'}), 403
    return jsonify({'task': task.to_dict(detailed=True)})


@tasks_bp.route('', methods=['POST'])
@login_required
def create_task():
    data = request.get_json() or {}
    if not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400

    due_date = None
    if data.get('due_date'):
        due_date = datetime.fromisoformat(data['due_date'].replace('Z', ''))

    task = Task(
        title=data['title'],
        description=data.get('description'),
        status=data.get('status', 'not_started'),
        priority=data.get('priority', 'medium'),
        project_id=data.get('project_id'),
        assigned_to=data.get('assigned_to'),
        created_by=g.current_user.id,
        due_date=due_date,
        estimated_hours=data.get('estimated_hours', 0),
        is_recurring=data.get('is_recurring', False),
        recurrence_pattern=data.get('recurrence_pattern'),
    )
    db.session.add(task)
    db.session.flush()

    for i, st in enumerate(data.get('subtasks', [])):
        db.session.add(Subtask(task_id=task.id, title=st['title'], position=i))

    db.session.add(TaskHistory(task_id=task.id, user_id=g.current_user.id, action='created'))
    if task.assigned_to:
        emp = Employee.query.get(task.assigned_to)
        if emp:
            db.session.add(Notification(
                user_id=emp.user_id, type='task_assigned',
                title='New Task Assigned', message=f'You have been assigned: {task.title}',
                link=f'/dashboard/tasks/{task.id}',
            ))
    db.session.commit()
    log_activity(g.current_user.id, 'task_created', 'task', task.id, {'title': task.title})
    return jsonify({'task': task.to_dict(detailed=True)}), 201


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not _can_access_task(task):
        return jsonify({'error': 'Permission denied'}), 403
    data = request.get_json() or {}
    trackable = ['title', 'description', 'status', 'priority', 'project_id', 'assigned_to',
                 'estimated_hours', 'actual_hours', 'progress_percentage', 'is_favorite', 'position']
    for field in trackable:
        if field in data:
            old = getattr(task, field)
            new = data[field]
            if old != new:
                db.session.add(TaskHistory(
                    task_id=task.id, user_id=g.current_user.id,
                    action=f'{field}_changed', old_value=str(old), new_value=str(new),
                ))
            setattr(task, field, new)
    if 'due_date' in data:
        task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '')) if data['due_date'] else None
    if data.get('status') == 'completed':
        task.completed_at = datetime.utcnow()
        task.progress_percentage = 100
    db.session.commit()
    log_activity(g.current_user.id, 'task_updated', 'task', task.id)
    return jsonify({'task': task.to_dict(detailed=True)})


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if g.current_user.role == 'employee' and not _can_access_task(task):
        return jsonify({'error': 'Permission denied'}), 403
    task.is_archived = True
    db.session.commit()
    log_activity(g.current_user.id, 'task_archived', 'task', task.id)
    return jsonify({'message': 'Task archived'})


@tasks_bp.route('/<int:task_id>/restore', methods=['POST'])
@login_required
def restore_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_archived = False
    db.session.commit()
    return jsonify({'message': 'Task restored'})


@tasks_bp.route('/<int:task_id>/duplicate', methods=['POST'])
@login_required
def duplicate_task(task_id):
    original = Task.query.get_or_404(task_id)
    new_task = Task(
        title=f'{original.title} (Copy)',
        description=original.description,
        status='not_started',
        priority=original.priority,
        project_id=original.project_id,
        assigned_to=original.assigned_to,
        created_by=g.current_user.id,
        estimated_hours=original.estimated_hours,
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'task': new_task.to_dict()}), 201


@tasks_bp.route('/bulk-assign', methods=['POST'])
@role_required('admin', 'manager')
def bulk_assign():
    data = request.get_json() or {}
    task_ids = data.get('task_ids', [])
    assigned_to = data.get('assigned_to')
    Task.query.filter(Task.id.in_(task_ids)).update({'assigned_to': assigned_to}, synchronize_session=False)
    db.session.commit()
    return jsonify({'message': f'{len(task_ids)} tasks assigned'})


@tasks_bp.route('/<int:task_id>/comments', methods=['POST'])
@login_required
def add_comment(task_id):
    task = Task.query.get_or_404(task_id)
    if not _can_access_task(task):
        return jsonify({'error': 'Permission denied'}), 403
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'Comment content is required'}), 400
    comment = Comment(task_id=task.id, user_id=g.current_user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    return jsonify({'comment': comment.to_dict()}), 201


@tasks_bp.route('/<int:task_id>/subtasks', methods=['POST'])
@login_required
def add_subtask(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json() or {}
    subtask = Subtask(task_id=task.id, title=data['title'], position=len(task.subtasks))
    db.session.add(subtask)
    completed = sum(1 for s in task.subtasks if s.is_completed)
    total = len(task.subtasks) + 1
    task.progress_percentage = (completed / total * 100) if total else 0
    db.session.commit()
    return jsonify({'subtask': subtask.to_dict()}), 201


@tasks_bp.route('/subtasks/<int:subtask_id>/toggle', methods=['POST'])
@login_required
def toggle_subtask(subtask_id):
    subtask = Subtask.query.get_or_404(subtask_id)
    subtask.is_completed = not subtask.is_completed
    task = subtask.task
    total = len(task.subtasks)
    completed = sum(1 for s in task.subtasks if s.is_completed)
    task.progress_percentage = (completed / total * 100) if total else 0
    db.session.commit()
    return jsonify({'subtask': subtask.to_dict()})
