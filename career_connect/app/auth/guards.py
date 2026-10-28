from functools import wraps
from flask import session, jsonify


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "unauthorized", "message": "Bạn cần đăng nhập."}), 401
        return view(*args, **kwargs)
    return wrapped


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "unauthorized", "message": "Bạn cần đăng nhập."}), 401
            if session.get("role") not in allowed_roles:
                return jsonify({"error": "forbidden", "message": "Bạn không có quyền thực hiện thao tác này."}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator
