from datetime import datetime
from app.extensions import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'manager', 'employee'), default='employee')
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    remember_token = db.Column(db.String(255))
    reset_token = db.Column(db.String(255))
    reset_token_expires = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    employee = db.relationship('Employee', backref='user', uselist=False)
    settings = db.relationship('UserSettings', backref='user', uselist=False)


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    head_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    employees = db.relationship('Employee', backref='department', foreign_keys='Employee.department_id')


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    employee_code = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    profile_picture = db.Column(db.String(500))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    designation = db.Column(db.String(100))
    joining_date = db.Column(db.Date)
    employment_status = db.Column(
        db.Enum('active', 'inactive', 'on_leave', 'terminated', 'archived'), default='active'
    )
    skills = db.Column(db.JSON)
    notes = db.Column(db.Text)
    attendance_percentage = db.Column(db.Numeric(5, 2), default=100.00)
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_tasks = db.relationship('Task', backref='assignee', foreign_keys='Task.assigned_to')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def to_dict(self, include_user=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'employee_code': self.employee_code,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'profile_picture': self.profile_picture,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'designation': self.designation,
            'joining_date': self.joining_date.isoformat() if self.joining_date else None,
            'employment_status': self.employment_status,
            'skills': self.skills or [],
            'notes': self.notes,
            'attendance_percentage': float(self.attendance_percentage or 0),
            'manager_id': self.manager_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_user and self.user:
            data['email'] = self.user.email
            data['role'] = self.user.role
        return data


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum('planning', 'active', 'on_hold', 'completed', 'cancelled', 'archived'), default='planning')
    health_status = db.Column(db.Enum('on_track', 'at_risk', 'off_track', 'completed'), default='on_track')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    completion_percentage = db.Column(db.Numeric(5, 2), default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tasks = db.relationship('Task', backref='project')
    members = db.relationship('ProjectMember', backref='project', cascade='all, delete-orphan')
    milestones = db.relationship('ProjectMilestone', backref='project', cascade='all, delete-orphan')

    def to_dict(self, include_members=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'health_status': self.health_status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'completion_percentage': float(self.completion_percentage or 0),
            'created_by': self.created_by,
            'task_count': len(self.tasks) if self.tasks else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_members:
            data['members'] = [m.to_dict() for m in self.members]
            data['milestones'] = [ms.to_dict() for ms in self.milestones]
        return data


class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    role = db.Column(db.String(50), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee = db.relationship('Employee')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
        }


class ProjectMilestone(db.Model):
    __tablename__ = 'project_milestones'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class Label(db.Model):
    __tablename__ = 'labels'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#3B82F6')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(
        db.Enum('not_started', 'in_progress', 'review', 'completed', 'cancelled', 'on_hold', 'overdue'),
        default='not_started'
    )
    priority = db.Column(db.Enum('low', 'medium', 'high', 'critical'), default='medium')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    due_date = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Numeric(6, 2), default=0)
    actual_hours = db.Column(db.Numeric(6, 2), default=0)
    progress_percentage = db.Column(db.Numeric(5, 2), default=0)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(50))
    is_favorite = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    position = db.Column(db.Integer, default=0)
    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    subtasks = db.relationship('Subtask', backref='task', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='task', cascade='all, delete-orphan')
    history = db.relationship('TaskHistory', backref='task', cascade='all, delete-orphan')

    def to_dict(self, detailed=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'assigned_to': self.assigned_to,
            'assignee_name': self.assignee.full_name if self.assignee else None,
            'created_by': self.created_by,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'estimated_hours': float(self.estimated_hours or 0),
            'actual_hours': float(self.actual_hours or 0),
            'progress_percentage': float(self.progress_percentage or 0),
            'is_recurring': self.is_recurring,
            'is_favorite': self.is_favorite,
            'is_archived': self.is_archived,
            'position': self.position,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
        if detailed:
            data['subtasks'] = [s.to_dict() for s in self.subtasks]
            data['comments'] = [c.to_dict() for c in self.comments]
            data['history'] = [h.to_dict() for h in self.history]
        return data


class Subtask(db.Model):
    __tablename__ = 'subtasks'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'is_completed': self.is_completed,
            'position': self.position,
        }


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author = db.relationship('User')

    def to_dict(self):
        emp = self.author.employee if self.author else None
        return {
            'id': self.id,
            'content': self.content,
            'user_id': self.user_id,
            'author_name': emp.full_name if emp else 'Unknown',
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class TaskHistory(db.Model):
    __tablename__ = 'task_history'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    link = db.Column(db.String(500))
    is_read = db.Column(db.Boolean, default=False)
    notification_metadata = db.Column('metadata', db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')

    def to_dict(self):
        emp = self.user.employee if self.user else None
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': emp.full_name if emp else 'System',
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    theme = db.Column(db.Enum('light', 'dark', 'system'), default='dark')
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    task_reminders = db.Column(db.Boolean, default=True)
    deadline_alerts = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default='en')
    dashboard_widgets = db.Column(db.JSON)

    def to_dict(self):
        return {
            'theme': self.theme,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'task_reminders': self.task_reminders,
            'deadline_alerts': self.deadline_alerts,
            'language': self.language,
            'dashboard_widgets': self.dashboard_widgets or [],
        }


class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Attachment(db.Model):
    __tablename__ = 'attachments'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
