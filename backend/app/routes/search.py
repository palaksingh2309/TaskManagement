from flask import Blueprint, request, jsonify, g
from sqlalchemy import or_
from app.models import Employee, Task, Project, Department
from app.utils.auth import login_required

search_bp = Blueprint('search', __name__)


@search_bp.route('', methods=['GET'])
@login_required
def global_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []})

    results = []
    if g.current_user.role != 'employee':
        employees = Employee.query.filter(or_(
            Employee.first_name.ilike(f'%{q}%'),
            Employee.last_name.ilike(f'%{q}%'),
            Employee.employee_code.ilike(f'%{q}%'),
        )).limit(5).all()
        for e in employees:
            results.append({'type': 'employee', 'id': e.id, 'title': e.full_name,
                            'subtitle': e.designation, 'link': f'/dashboard/employees/{e.id}'})

    task_query = Task.query.filter(or_(
        Task.title.ilike(f'%{q}%'),
        Task.description.ilike(f'%{q}%'),
    ), Task.is_archived == False)
    if g.current_user.role == 'employee' and g.current_user.employee:
        task_query = task_query.filter(Task.assigned_to == g.current_user.employee.id)
    tasks = task_query.limit(5).all()
    for t in tasks:
        results.append({'type': 'task', 'id': t.id, 'title': t.title,
                        'subtitle': t.status, 'link': f'/dashboard/tasks/{t.id}'})

    projects = Project.query.filter(
        Project.name.ilike(f'%{q}%'), Project.status != 'archived'
    ).limit(5).all()
    for p in projects:
        results.append({'type': 'project', 'id': p.id, 'title': p.name,
                        'subtitle': p.status, 'link': f'/dashboard/projects/{p.id}'})

    departments = Department.query.filter(Department.name.ilike(f'%{q}%')).limit(3).all()
    for d in departments:
        results.append({'type': 'department', 'id': d.id, 'title': d.name,
                        'subtitle': 'Department', 'link': f'/dashboard/employees?department_id={d.id}'})

    return jsonify({'results': results, 'query': q})
