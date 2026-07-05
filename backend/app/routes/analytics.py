from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import func, case
from app.extensions import db
from app.models import Task, Employee, Project, Department
from app.utils.auth import login_required, role_required

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('', methods=['GET'])
@login_required
def analytics():
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    now = datetime.utcnow()

    task_query = Task.query.filter(Task.is_archived == False)
    if g.current_user.role == 'employee' and g.current_user.employee:
        task_query = task_query.filter(Task.assigned_to == g.current_user.employee.id)
    if date_from:
        task_query = task_query.filter(Task.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        task_query = task_query.filter(Task.created_at <= datetime.fromisoformat(date_to))

    total = task_query.count()
    completed = task_query.filter(Task.status == 'completed').count()
    overdue = task_query.filter(Task.status == 'overdue').count()
    avg_completion = db.session.query(func.avg(Task.actual_hours)).filter(
        Task.status == 'completed', Task.is_archived == False
    ).scalar() or 0

    dept_performance = db.session.query(
        Department.name,
        func.count(Task.id).label('total'),
        func.sum(case((Task.status == 'completed', 1), else_=0)).label('completed'),
    ).join(Employee, Employee.department_id == Department.id).join(
        Task, Task.assigned_to == Employee.id
    ).filter(Task.is_archived == False).group_by(Department.name).all()

    emp_prod_query = db.session.query(
        Employee.first_name, Employee.last_name,
        func.count(Task.id).label('total'),
        func.sum(case((Task.status == 'completed', 1), else_=0)).label('completed'),
    ).join(Task, Task.assigned_to == Employee.id).filter(
        Task.is_archived == False
    )
    if g.current_user.role == 'employee' and g.current_user.employee:
        emp_prod_query = emp_prod_query.filter(Employee.id == g.current_user.employee.id)
    employee_productivity = emp_prod_query.group_by(Employee.id).limit(10).all()

    project_progress = db.session.query(
        Project.name, Project.completion_percentage, Project.health_status
    ).filter(Project.status != 'archived').all()

    workload = db.session.query(
        Employee.first_name, Employee.last_name,
        func.count(Task.id).label('active_tasks'),
    ).join(Task, Task.assigned_to == Employee.id).filter(
        Task.status.in_(['not_started', 'in_progress', 'review']),
        Task.is_archived == False,
    ).group_by(Employee.id).all()

    return jsonify({
        'summary': {
            'total_tasks': total,
            'completed_tasks': completed,
            'overdue_tasks': overdue,
            'completion_rate': round(completed / total * 100, 1) if total else 0,
            'avg_completion_hours': round(float(avg_completion), 1),
        },
        'department_performance': [
            {'department': d, 'total': t, 'completed': int(c or 0),
             'rate': round(int(c or 0) / t * 100, 1) if t else 0}
            for d, t, c in dept_performance
        ],
        'employee_productivity': [
            {'name': f'{fn} {ln}', 'total': t, 'completed': int(c or 0),
             'rate': round(int(c or 0) / t * 100, 1) if t else 0}
            for fn, ln, t, c in employee_productivity
        ],
        'project_progress': [
            {'name': n, 'completion': float(cp or 0), 'health': h}
            for n, cp, h in project_progress
        ],
        'workload_distribution': [
            {'name': f'{fn} {ln}', 'active_tasks': at}
            for fn, ln, at in workload
        ],
    })
