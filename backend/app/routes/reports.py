import csv
import io
from flask import Blueprint, request, jsonify, Response, g
from datetime import datetime
from app.models import Employee, Task, Project, Department, ActivityLog
from app.utils.auth import login_required, role_required

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/csv/<report_type>', methods=['GET'])
@login_required
def export_csv(report_type):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'employees':
        writer.writerow(['ID', 'Code', 'Name', 'Email', 'Department', 'Designation', 'Status'])
        for e in Employee.query.all():
            writer.writerow([
                e.id, e.employee_code, e.full_name,
                e.user.email if e.user else '', e.department.name if e.department else '',
                e.designation, e.employment_status,
            ])
    elif report_type == 'tasks':
        writer.writerow(['ID', 'Title', 'Status', 'Priority', 'Assignee', 'Due Date', 'Progress'])
        for t in Task.query.filter_by(is_archived=False).all():
            writer.writerow([
                t.id, t.title, t.status, t.priority,
                t.assignee.full_name if t.assignee else '',
                t.due_date.isoformat() if t.due_date else '', t.progress_percentage,
            ])
    elif report_type == 'projects':
        writer.writerow(['ID', 'Name', 'Status', 'Health', 'Completion', 'Start', 'End'])
        for p in Project.query.filter(Project.status != 'archived').all():
            writer.writerow([
                p.id, p.name, p.status, p.health_status,
                p.completion_percentage, p.start_date, p.end_date,
            ])
    elif report_type == 'overdue':
        writer.writerow(['ID', 'Title', 'Assignee', 'Due Date', 'Priority'])
        for t in Task.query.filter_by(status='overdue', is_archived=False).all():
            writer.writerow([
                t.id, t.title, t.assignee.full_name if t.assignee else '',
                t.due_date.isoformat() if t.due_date else '', t.priority,
            ])
    else:
        return jsonify({'error': 'Invalid report type'}), 400

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={report_type}_{datetime.now().strftime("%Y%m%d")}.csv'},
    )


@reports_bp.route('/pdf/<report_type>', methods=['GET'])
@login_required
def export_pdf(report_type):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        return jsonify({'error': 'PDF generation not available'}), 500

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(50, 750, f'TaskFlow Pro - {report_type.title()} Report')
    c.setFont('Helvetica', 10)
    c.drawString(50, 730, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    y = 700

    if report_type == 'tasks':
        for t in Task.query.filter_by(is_archived=False).limit(50).all():
            c.drawString(50, y, f'{t.id}. {t.title} - {t.status} ({t.priority})')
            y -= 15
            if y < 50:
                c.showPage()
                y = 750
    elif report_type == 'employees':
        for e in Employee.query.limit(50).all():
            c.drawString(50, y, f'{e.employee_code} - {e.full_name} - {e.designation or ""}')
            y -= 15
            if y < 50:
                c.showPage()
                y = 750
    elif report_type == 'projects':
        for p in Project.query.filter(Project.status != 'archived').limit(50).all():
            c.drawString(50, y, f'{p.name} - {p.status} ({p.completion_percentage}%)')
            y -= 15
            if y < 50:
                c.showPage()
                y = 750
    elif report_type == 'overdue':
        for t in Task.query.filter_by(status='overdue', is_archived=False).limit(50).all():
            assignee = t.assignee.full_name if t.assignee else 'Unassigned'
            c.drawString(50, y, f'{t.title} - {assignee} - due {t.due_date}')
            y -= 15
            if y < 50:
                c.showPage()
                y = 750
    else:
        return jsonify({'error': 'Invalid report type'}), 400

    c.save()
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={report_type}_{datetime.now().strftime("%Y%m%d")}.pdf'},
    )
