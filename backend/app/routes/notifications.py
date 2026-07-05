from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import Notification
from app.utils.auth import login_required, paginate_query

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('', methods=['GET'])
@login_required
def list_notifications():
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 20)
    is_read = request.args.get('is_read')
    ntype = request.args.get('type')

    query = Notification.query.filter_by(user_id=g.current_user.id)
    if is_read is not None:
        query = query.filter(Notification.is_read == (is_read == 'true'))
    if ntype:
        query = query.filter(Notification.type == ntype)
    query = query.order_by(Notification.created_at.desc())
    result = paginate_query(query, page, per_page)
    unread_count = Notification.query.filter_by(user_id=g.current_user.id, is_read=False).count()
    return jsonify({
        'notifications': [n.to_dict() for n in result['items']],
        'unread_count': unread_count,
        'pagination': {k: v for k, v in result.items() if k != 'items'},
    })


@notifications_bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=g.current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'notification': notif.to_dict()})


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=g.current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read'})


@notifications_bp.route('/<int:notif_id>', methods=['DELETE'])
@login_required
def delete_notification(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=g.current_user.id).first_or_404()
    db.session.delete(notif)
    db.session.commit()
    return jsonify({'message': 'Notification deleted'})
