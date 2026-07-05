"""Seed database with demo data. Run after init_db.py."""
import bcrypt
from datetime import datetime, date
from app import create_app
from app.extensions import db
from app.models import (
    User, Employee, Department, UserSettings, Project, ProjectMember,
    ProjectMilestone, Task, Subtask, Comment, Notification, Label, ActivityLog,
)

app = create_app()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

with app.app_context():
    if User.query.first():
        print("Database already seeded. Skipping.")
        exit(0)

    pw = hash_password("Admin@123")

    depts = [
        Department(name="Engineering", description="Software development"),
        Department(name="Design", description="UI/UX design"),
        Department(name="Marketing", description="Marketing and growth"),
    ]
    db.session.add_all(depts)
    db.session.flush()

    users = [
        User(email="admin@taskflow.pro", password_hash=pw, role="admin", email_verified=True),
        User(email="manager@taskflow.pro", password_hash=pw, role="manager", email_verified=True),
        User(email="employee@taskflow.pro", password_hash=pw, role="employee", email_verified=True),
    ]
    db.session.add_all(users)
    db.session.flush()

    employees = [
        Employee(user_id=1, employee_code="EMP001", first_name="Alex", last_name="Johnson",
                 department_id=1, designation="System Administrator", joining_date=date(2023, 1, 15),
                 skills=["Leadership", "DevOps"]),
        Employee(user_id=2, employee_code="EMP002", first_name="Sarah", last_name="Chen",
                 department_id=1, designation="Engineering Manager", joining_date=date(2023, 3, 20),
                 skills=["Agile", "Python", "React"]),
        Employee(user_id=3, employee_code="EMP003", first_name="Mike", last_name="Williams",
                 department_id=1, designation="Software Developer", joining_date=date(2023, 6, 1),
                 skills=["TypeScript", "React", "Node.js"]),
    ]
    db.session.add_all(employees)

    for u in users:
        db.session.add(UserSettings(user_id=u.id, dashboard_widgets=["stats", "tasks", "activity", "deadlines"]))

    project = Project(name="TaskFlow Pro v2.0", description="Major platform upgrade",
                      status="active", health_status="on_track", completion_percentage=65,
                      start_date=date(2025, 1, 1), end_date=date(2025, 12, 31), created_by=1)
    db.session.add(project)
    db.session.flush()

    db.session.add_all([
        ProjectMember(project_id=project.id, employee_id=e.id) for e in employees
    ])
    db.session.add(ProjectMilestone(project_id=project.id, title="MVP Release", due_date=date(2025, 6, 30), is_completed=True))

    tasks = [
        Task(title="Implement authentication system", status="in_progress", priority="critical",
             project_id=project.id, assigned_to=3, created_by=1, progress_percentage=70,
             estimated_hours=40, due_date=datetime(2025, 7, 15, 17, 0)),
        Task(title="Design dashboard wireframes", status="completed", priority="high",
             project_id=project.id, assigned_to=3, created_by=2, progress_percentage=100,
             due_date=datetime(2025, 5, 15, 17, 0), completed_at=datetime.utcnow()),
        Task(title="Database optimization", status="overdue", priority="high",
             project_id=project.id, assigned_to=2, created_by=1, progress_percentage=60,
             due_date=datetime(2025, 6, 25, 17, 0)),
    ]
    db.session.add_all(tasks)
    db.session.flush()

    db.session.add_all([
        Subtask(task_id=tasks[0].id, title="Login page", is_completed=True, position=0),
        Subtask(task_id=tasks[0].id, title="Signup page", is_completed=True, position=1),
        Subtask(task_id=tasks[0].id, title="Password reset", is_completed=False, position=2),
    ])
    db.session.add(Comment(task_id=tasks[0].id, user_id=2, content="Great progress on auth!"))
    db.session.add(Notification(user_id=3, type="task_assigned", title="New Task Assigned",
                                message="You have been assigned: Implement authentication system",
                                link="/dashboard/tasks/1"))

    db.session.commit()
    print("Database seeded successfully!")
    print("Demo accounts: admin@taskflow.pro / manager@taskflow.pro / employee@taskflow.pro")
    print("Password: Admin@123")
