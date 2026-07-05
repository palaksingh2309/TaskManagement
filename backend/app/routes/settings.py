from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import UserSettings, LoginHistory, Session, Employee
from app.utils.auth import login_required, log_activity

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('', methods=['GET'])
@login_required
def get_settings():
    settings = g.current_user.settings
    if not settings:
        settings = UserSettings(user_id=g.current_user.id)
        db.session.add(settings)
        db.session.commit()
    return jsonify({'settings': settings.to_dict()})


@settings_bp.route('', methods=['PUT'])
@login_required
def update_settings():
    settings = g.current_user.settings
    if not settings:
        settings = UserSettings(user_id=g.current_user.id)
        db.session.add(settings)
    data = request.get_json() or {}
    for field in ['theme', 'email_notifications', 'push_notifications',
                  'task_reminders', 'deadline_alerts', 'language', 'dashboard_widgets']:
        if field in data:
            setattr(settings, field, data[field])
    db.session.commit()
    log_activity(g.current_user.id, 'settings_updated', 'user', g.current_user.id)
    return jsonify({'settings': settings.to_dict()})


@settings_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json() or {}
    emp = g.current_user.employee
    if not emp:
        return jsonify({'error': 'No employee profile'}), 404
    for field in ['first_name', 'last_name', 'phone', 'profile_picture']:
        if field in data:
            setattr(emp, field, data[field])
    db.session.commit()
    log_activity(g.current_user.id, 'profile_updated', 'employee', emp.id)
    return jsonify({'employee': emp.to_dict(include_user=True)})


@settings_bp.route('/login-history', methods=['GET'])
@login_required
def login_history():
    history = LoginHistory.query.filter_by(user_id=g.current_user.id).order_by(
        LoginHistory.created_at.desc()
    ).limit(20).all()
    return jsonify({'history': [
        {'id': h.id, 'ip_address': h.ip_address, 'success': h.success,
         'created_at': h.created_at.isoformat() if h.created_at else None}
        for h in history
    ]})


@settings_bp.route('/sessions', methods=['GET'])
@login_required
def list_sessions():
    sessions = Session.query.filter_by(user_id=g.current_user.id).all()
    return jsonify({'sessions': [
        {'id': s.id, 'created_at': s.created_at.isoformat() if s.created_at else None,
         'expires_at': s.expires_at.isoformat() if s.expires_at else None}
        for s in sessions
    ]})


@settings_bp.route('/sessions/<session_id>', methods=['DELETE'])
@login_required
def revoke_session(session_id):
    session = Session.query.filter_by(id=session_id, user_id=g.current_user.id).first_or_404()
    db.session.delete(session)
    db.session.commit()
    return jsonify({'message': 'Session revoked'})
