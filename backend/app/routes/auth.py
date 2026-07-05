from flask import Blueprint, request, jsonify, g
from datetime import datetime
from app.extensions import db
from app.models import User, Employee, UserSettings, Department
from app.utils.auth import (
    hash_password, verify_password, validate_email, validate_password_strength,
    create_session, login_required, log_activity, log_login, generate_reset_token
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()

    if not all([email, password, first_name, last_name]):
        return jsonify({'error': 'All fields are required'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    strength = validate_password_strength(password)
    if not strength['valid']:
        return jsonify({'error': 'Password too weak', 'feedback': strength['feedback']}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(email=email, password_hash=hash_password(password), role='employee')
    db.session.add(user)
    db.session.flush()

    dept = Department.query.first()
    if not dept:
        dept = Department(name='General', description='Default department')
        db.session.add(dept)
        db.session.flush()
    emp = Employee(
        user_id=user.id,
        employee_code=f'EMP{user.id:03d}',
        first_name=first_name,
        last_name=last_name,
        department_id=dept.id if dept else None,
        designation='Team Member',
        joining_date=datetime.utcnow().date(),
    )
    db.session.add(emp)
    db.session.add(UserSettings(user_id=user.id))
    db.session.commit()

    log_activity(user.id, 'register', 'user', user.id)
    session_token = create_session(user.id)
    return jsonify({
        'message': 'Registration successful',
        'token': session_token,
        'user': _user_response(user),
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    remember = data.get('remember', False)

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        if user:
            log_login(user.id, success=False)
        return jsonify({'error': 'Invalid credentials'}), 401
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403

    user.last_login = datetime.utcnow()
    db.session.commit()
    log_login(user.id)
    log_activity(user.id, 'login', 'user', user.id)
    session_token = create_session(user.id, remember=remember)

    resp = jsonify({'message': 'Login successful', 'token': session_token, 'user': _user_response(user)})
    return resp


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = request.cookies.get('session_token')
    from app.models import Session
    session = Session.query.filter_by(id=token).first()
    if session:
        db.session.delete(session)
        db.session.commit()
    log_activity(g.current_user.id, 'logout', 'user', g.current_user.id)
    return jsonify({'message': 'Logged out successfully'})


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({'user': _user_response(g.current_user)})


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    import os
    from datetime import timedelta
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    user = User.query.filter_by(email=email).first()
    response = {'message': 'If the email exists, a reset link has been sent'}
    if user:
        token = generate_reset_token()
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        log_activity(user.id, 'password_reset_requested', 'user', user.id)
        # In development, return reset link (no email server configured)
        if os.getenv('FLASK_DEBUG', '0') == '1':
            response['reset_link'] = f'http://localhost:3000/reset-password?token={token}'
            response['dev_note'] = 'Email not configured — use reset_link above in development'
    return jsonify(response)


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token = data.get('token', '')
    password = data.get('password', '')
    if not token or not password:
        return jsonify({'error': 'Token and password required'}), 400
    strength = validate_password_strength(password)
    if not strength['valid']:
        return jsonify({'error': 'Password too weak', 'feedback': strength['feedback']}), 400

    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        return jsonify({'error': 'Invalid or expired reset token'}), 400

    user.password_hash = hash_password(password)
    user.reset_token = None
    user.reset_token_expires = None
    db.session.commit()
    log_activity(user.id, 'password_reset', 'user', user.id)
    return jsonify({'message': 'Password reset successful'})


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json() or {}
    current = data.get('current_password', '')
    new_pass = data.get('new_password', '')
    if not verify_password(current, g.current_user.password_hash):
        return jsonify({'error': 'Current password is incorrect'}), 400
    strength = validate_password_strength(new_pass)
    if not strength['valid']:
        return jsonify({'error': 'Password too weak'}), 400
    g.current_user.password_hash = hash_password(new_pass)
    db.session.commit()
    log_activity(g.current_user.id, 'password_change', 'user', g.current_user.id)
    return jsonify({'message': 'Password changed successfully'})


@auth_bp.route('/validate-password', methods=['POST'])
def validate_password():
    data = request.get_json() or {}
    return jsonify(validate_password_strength(data.get('password', '')))


def _user_response(user):
    emp = user.employee
    settings = user.settings
    return {
        'id': user.id,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'employee': emp.to_dict() if emp else None,
        'settings': settings.to_dict() if settings else None,
    }
