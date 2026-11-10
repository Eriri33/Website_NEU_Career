import sqlite3
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db
from app.auth.guards import login_required

auth_bp = Blueprint("auth", __name__)
SELF_REGISTER_ROLES = {"student", "business"}


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "student").strip()
    if not email or "@" not in email or len(password) < 6:
        return jsonify({"error": "invalid_input", "message": "Email hợp lệ và mật khẩu tối thiểu 6 ký tự là bắt buộc."}), 400
    if role not in SELF_REGISTER_ROLES:
        return jsonify({"error": "invalid_role", "message": "Chỉ cho phép tự đăng ký vai trò student hoặc business."}), 400

    db = get_db()
    try:
        cur = db.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                         (email, generate_password_hash(password), role))
        user_id = cur.lastrowid
        if role == "student":
            db.execute("INSERT INTO student_profiles (user_id) VALUES (?)", (user_id,))
        else:
            db.execute("INSERT INTO companies (user_id, company_name) VALUES (?, ?)", (user_id, "Chưa cập nhật"))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "email_exists", "message": "Email đã được sử dụng."}), 409
    return jsonify({"message": "Tạo tài khoản thành công.", "user_id": user_id, "role": role}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = get_db().execute(
        "SELECT id, email, password_hash, role, is_active FROM users WHERE email = ?", (email,)
    ).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "invalid_credentials", "message": "Email hoặc mật khẩu không đúng."}), 401
    if not user["is_active"]:
        return jsonify({"error": "inactive_account", "message": "Tài khoản đã bị khóa."}), 403
    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    return jsonify({"message": "Đăng nhập thành công.", "user": {
        "id": user["id"], "email": user["email"], "role": user["role"]
    }}), 200


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Đã đăng xuất."}), 200


@auth_bp.get("/me")
@login_required
def me():
    row = get_db().execute(
        "SELECT id, email, role, is_active, created_at FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    if not row:
        session.clear()
        return jsonify({"error": "not_found"}), 404
    return jsonify(dict(row))


@auth_bp.put("/me")
@login_required
def update_me():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"error": "invalid_input", "message": "Cần cung cấp email hợp lệ."}), 400
    try:
        get_db().execute("UPDATE users SET email = ? WHERE id = ?", (email, session["user_id"]))
        get_db().commit()
    except sqlite3.IntegrityError:
        get_db().rollback()
        return jsonify({"error": "email_exists", "message": "Email đã được sử dụng."}), 409
    return jsonify({"message": "Đã cập nhật email."})


@auth_bp.put("/password")
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current = data.get("current_password") or ""
    new = data.get("new_password") or ""
    row = get_db().execute("SELECT password_hash FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    if not row or not check_password_hash(row["password_hash"], current):
        return jsonify({"error": "invalid_password", "message": "Mật khẩu hiện tại không đúng."}), 400
    if len(new) < 6:
        return jsonify({"error": "invalid_input", "message": "Mật khẩu mới phải có ít nhất 6 ký tự."}), 400
    get_db().execute("UPDATE users SET password_hash = ? WHERE id = ?",
                     (generate_password_hash(new), session["user_id"]))
    get_db().commit()
    return jsonify({"message": "Đã đổi mật khẩu."})


@auth_bp.delete("/me")
@login_required
def deactivate_me():
    """Soft-delete own account to keep application/review history intact."""
    get_db().execute("UPDATE users SET is_active = 0 WHERE id = ?", (session["user_id"],))
    get_db().commit()
    session.clear()
    return jsonify({"message": "Tài khoản đã được vô hiệu hóa; dữ liệu lịch sử được giữ lại."}), 200
