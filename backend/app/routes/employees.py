from flask import Blueprint, request, jsonify, g
from datetime import datetime, date
from sqlalchemy import or_, func, case
from app.extensions import db
from app.models import Employee, User, Department, Task, UserSettings
from app.utils.auth import login_required, role_required, hash_password, log_activity, paginate_query

employees_bp = Blueprint('employees', __name__)


@employees_bp.route('', methods=['GET'])
@login_required
def list_employees():
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 10)
    search = request.args.get('search', '')
    department_id = request.args.get('department_id')
    status = request.args.get('status')
    include_archived = request.args.get('include_archived', 'false') == 'true'

    query = Employee.query
    if g.current_user.role == 'employee':
        emp = g.current_user.employee
        if emp:
            query = query.filter(Employee.id == emp.id)
    if search:
        query = query.filter(or_(
            Employee.first_name.ilike(f'%{search}%'),
            Employee.last_name.ilike(f'%{search}%'),
            Employee.employee_code.ilike(f'%{search}%'),
            Employee.designation.ilike(f'%{search}%'),
        ))
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if status:
        query = query.filter(Employee.employment_status == status)
    elif not include_archived:
        query = query.filter(Employee.employment_status != 'archived')

    query = query.order_by(Employee.created_at.desc())
    result = paginate_query(query, page, per_page)
    return jsonify({
        'employees': [e.to_dict(include_user=True) for e in result['items']],
        'pagination': {k: v for k, v in result.items() if k != 'items'},
    })


@employees_bp.route('/<int:emp_id>', methods=['GET'])
@login_required
def get_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    if g.current_user.role == 'employee':
        own = g.current_user.employee
        if not own or own.id != emp_id:
            return jsonify({'error': 'Permission denied'}), 403
    task_stats = db.session.query(
        func.count(Task.id).label('total'),
        func.sum(case((Task.status == 'completed', 1), else_=0)).label('completed'),
        func.sum(case((Task.status == 'overdue', 1), else_=0)).label('overdue'),
    ).filter(Task.assigned_to == emp_id, Task.is_archived == False).first()

    data = emp.to_dict(include_user=True)
    data['task_stats'] = {
        'total': task_stats.total or 0,
        'completed': int(task_stats.completed or 0),
        'overdue': int(task_stats.overdue or 0),
    }
    data['recent_tasks'] = [
        t.to_dict() for t in Task.query.filter_by(assigned_to=emp_id, is_archived=False)
        .order_by(Task.updated_at.desc()).limit(5).all()
    ]
    return jsonify({'employee': data})


@employees_bp.route('', methods=['POST'])
@role_required('admin', 'manager')
def create_employee():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', 'Employee@123')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()

    if not all([email, first_name, last_name]):
        return jsonify({'error': 'Required fields missing'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 409

    role = data.get('role', 'employee')
    if g.current_user.role == 'manager' and role == 'admin':
        return jsonify({'error': 'Cannot create admin users'}), 403

    user = User(email=email, password_hash=hash_password(password), role=role)
    db.session.add(user)
    db.session.flush()

    emp = Employee(
        user_id=user.id,
        employee_code=data.get('employee_code') or f'EMP{user.id:03d}',
        first_name=first_name,
        last_name=last_name,
        phone=data.get('phone'),
        department_id=data.get('department_id'),
        designation=data.get('designation', 'Team Member'),
        joining_date=datetime.strptime(data['joining_date'], '%Y-%m-%d').date() if data.get('joining_date') else date.today(),
        employment_status=data.get('employment_status', 'active'),
        skills=data.get('skills', []),
        notes=data.get('notes'),
        manager_id=data.get('manager_id'),
    )
    db.session.add(emp)
    db.session.add(UserSettings(user_id=user.id))
    db.session.commit()
    log_activity(g.current_user.id, 'employee_created', 'employee', emp.id, {'name': emp.full_name})
    return jsonify({'employee': emp.to_dict(include_user=True)}), 201


@employees_bp.route('/<int:emp_id>', methods=['PUT'])
@role_required('admin', 'manager')
def update_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    data = request.get_json() or {}
    for field in ['first_name', 'last_name', 'phone', 'department_id', 'designation',
                  'employment_status', 'skills', 'notes', 'manager_id', 'profile_picture']:
        if field in data:
            setattr(emp, field, data[field])
    if 'joining_date' in data and data['joining_date']:
        emp.joining_date = datetime.strptime(data['joining_date'], '%Y-%m-%d').date()
    if 'attendance_percentage' in data:
        emp.attendance_percentage = data['attendance_percentage']
    if 'role' in data and g.current_user.role == 'admin':
        emp.user.role = data['role']
    db.session.commit()
    log_activity(g.current_user.id, 'employee_updated', 'employee', emp.id)
    return jsonify({'employee': emp.to_dict(include_user=True)})


@employees_bp.route('/<int:emp_id>', methods=['DELETE'])
@role_required('admin')
def delete_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    emp.employment_status = 'archived'
    db.session.commit()
    log_activity(g.current_user.id, 'employee_archived', 'employee', emp.id)
    return jsonify({'message': 'Employee archived'})


@employees_bp.route('/<int:emp_id>/restore', methods=['POST'])
@role_required('admin')
def restore_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    emp.employment_status = 'active'
    db.session.commit()
    log_activity(g.current_user.id, 'employee_restored', 'employee', emp.id)
    return jsonify({'message': 'Employee restored'})


@employees_bp.route('/departments', methods=['GET'])
@login_required
def list_departments():
    depts = Department.query.all()
    return jsonify({'departments': [
        {'id': d.id, 'name': d.name, 'description': d.description,
         'employee_count': len(d.employees)} for d in depts
    ]})


@employees_bp.route('/departments', methods=['POST'])
@role_required('admin')
def create_department():
    data = request.get_json() or {}
    dept = Department(name=data['name'], description=data.get('description'))
    db.session.add(dept)
    db.session.commit()
    return jsonify({'department': {'id': dept.id, 'name': dept.name}}), 201
