import bcrypt
import re
import secrets
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from app.extensions import db
from app.models import Session, User, ActivityLog, LoginHistory
from app.config import Config


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> dict:
    score = 0
    feedback = []
    if len(password) >= 8:
        score += 1
    else:
        feedback.append('At least 8 characters')
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append('One uppercase letter')
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append('One lowercase letter')
    if re.search(r'\d', password):
        score += 1
    else:
        feedback.append('One number')
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback.append('One special character')
    strength = ['weak', 'weak', 'fair', 'good', 'strong', 'strong'][score]
    return {'score': score, 'strength': strength, 'feedback': feedback, 'valid': score >= 4}


def create_session(user_id: int, remember: bool = False) -> str:
    session_id = str(uuid.uuid4())
    hours = Config.SESSION_EXPIRY_HOURS * (30 if remember else 1)
    expires_at = datetime.utcnow() + timedelta(hours=hours)
    session = Session(id=session_id, user_id=user_id, expires_at=expires_at)
    db.session.add(session)
    db.session.commit()
    return session_id


def get_current_user():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = request.cookies.get('session_token')
    if not token:
        return None
    session = Session.query.filter_by(id=token).first()
    if not session or session.expires_at < datetime.utcnow():
        if session:
            db.session.delete(session)
            db.session.commit()
        return None
    return User.query.get(session.user_id)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_active:
            return jsonify({'error': 'Authentication required'}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            if g.current_user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def log_activity(user_id, action, entity_type=None, entity_id=None, details=None):
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.add(log)
    db.session.commit()


def log_login(user_id, success=True):
    entry = LoginHistory(
        user_id=user_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        success=success,
    )
    db.session.add(entry)
    db.session.commit()


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def paginate_query(query, page=1, per_page=10):
    page = max(1, int(page))
    per_page = min(100, max(1, int(per_page)))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
    }
