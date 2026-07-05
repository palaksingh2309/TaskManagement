from flask import Blueprint, request, jsonify, g
from datetime import datetime
from app.extensions import db
from app.models import Project, ProjectMember, ProjectMilestone, Task
from app.utils.auth import login_required, role_required, log_activity, paginate_query

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('', methods=['GET'])
@login_required
def list_projects():
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 10)
    status = request.args.get('status')
    search = request.args.get('search', '')

    query = Project.query.filter(Project.status != 'archived')
    if status:
        query = query.filter(Project.status == status)
    if search:
        query = query.filter(Project.name.ilike(f'%{search}%'))
    query = query.order_by(Project.updated_at.desc())
    result = paginate_query(query, page, per_page)
    return jsonify({
        'projects': [p.to_dict() for p in result['items']],
        'pagination': {k: v for k, v in result.items() if k != 'items'},
    })


@projects_bp.route('/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id, is_archived=False).all()
    data = project.to_dict(include_members=True)
    data['tasks'] = [t.to_dict() for t in tasks]
    return jsonify({'project': data})


@projects_bp.route('', methods=['POST'])
@login_required
def create_project():
    data = request.get_json() or {}
    project = Project(
        name=data['name'],
        description=data.get('description'),
        status=data.get('status', 'planning'),
        health_status=data.get('health_status', 'on_track'),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
        created_by=g.current_user.id,
    )
    db.session.add(project)
    db.session.flush()
    for member_id in data.get('member_ids', []):
        db.session.add(ProjectMember(project_id=project.id, employee_id=member_id))
    for ms in data.get('milestones', []):
        db.session.add(ProjectMilestone(
            project_id=project.id, title=ms['title'],
            description=ms.get('description'),
            due_date=datetime.strptime(ms['due_date'], '%Y-%m-%d').date() if ms.get('due_date') else None,
        ))
    db.session.commit()
    log_activity(g.current_user.id, 'project_created', 'project', project.id)
    return jsonify({'project': project.to_dict(include_members=True)}), 201


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    for field in ['name', 'description', 'status', 'health_status', 'completion_percentage']:
        if field in data:
            setattr(project, field, data[field])
    if 'start_date' in data and data['start_date']:
        project.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    if 'end_date' in data and data['end_date']:
        project.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'project': project.to_dict(include_members=True)})


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@role_required('admin', 'manager')
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    project.status = 'archived'
    db.session.commit()
    return jsonify({'message': 'Project archived'})
