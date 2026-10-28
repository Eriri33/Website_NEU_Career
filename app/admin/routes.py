import sqlite3
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from app.database import get_db
from app.auth.guards import roles_required

admin_bp = Blueprint("admin", __name__)
STAFF_ROLES = {"admin", "moderator"}
ALL_ROLES = {"student", "business", "moderator", "admin"}


def _log_review(db, entity_type, entity_id, action, note):
    db.execute("""INSERT INTO review_histories (reviewer_id, entity_type, entity_id, action, note)
                  VALUES (?, ?, ?, ?, ?)""", (session["user_id"], entity_type, entity_id, action, note))


# ---------------------------- Dashboard / moderation ----------------------------
@admin_bp.get("/pending/companies")
@roles_required(*STAFF_ROLES)
def pending_companies():
    rows = get_db().execute("""
        SELECT c.id, c.company_name, c.description, c.website, c.created_at, u.email
        FROM companies c JOIN users u ON u.id = c.user_id
        WHERE c.approval_status = 'pending' AND u.is_active = 1 ORDER BY c.created_at
    """).fetchall()
    return jsonify([dict(row) for row in rows])


@admin_bp.get("/pending/jobs")
@roles_required(*STAFF_ROLES)
def pending_jobs():
    rows = get_db().execute("""
        SELECT j.id, j.title, j.description, j.created_at, c.company_name
        FROM jobs j JOIN companies c ON c.id = j.company_id JOIN users u ON u.id = c.user_id
        WHERE j.status = 'pending' AND c.approval_status = 'approved' AND u.is_active = 1
        ORDER BY j.created_at
    """).fetchall()
    return jsonify([dict(row) for row in rows])


@admin_bp.post("/companies/<int:company_id>/review")
@roles_required(*STAFF_ROLES)
def review_company(company_id):
    data = request.get_json(silent=True) or {}
    decision = data.get("decision")
    if decision not in ("approved", "rejected"):
        return jsonify({"error": "invalid_decision", "message": "decision phải là approved hoặc rejected."}), 400
    db = get_db()
    company = db.execute("SELECT id FROM companies WHERE id = ?", (company_id,)).fetchone()
    if not company:
        return jsonify({"error": "not_found", "message": "Không tìm thấy doanh nghiệp."}), 404
    note = (data.get("note") or "").strip()
    db.execute("""UPDATE companies SET approval_status = ?, review_note = ?, reviewed_by = ?,
                  reviewed_at = CURRENT_TIMESTAMP WHERE id = ?""",
               (decision, note, session["user_id"], company_id))
    _log_review(db, "company", company_id, decision, note)
    db.commit()
    return jsonify({"message": "Đã cập nhật kết quả duyệt doanh nghiệp.", "status": decision})


@admin_bp.post("/jobs/<int:job_id>/review")
@roles_required(*STAFF_ROLES)
def review_job(job_id):
    data = request.get_json(silent=True) or {}
    decision = data.get("decision")
    if decision not in ("approved", "rejected"):
        return jsonify({"error": "invalid_decision", "message": "decision phải là approved hoặc rejected."}), 400
    db = get_db()
    job = db.execute("""SELECT j.id, c.approval_status FROM jobs j
                        JOIN companies c ON c.id = j.company_id WHERE j.id = ?""", (job_id,)).fetchone()
    if not job:
        return jsonify({"error": "not_found", "message": "Không tìm thấy tin tuyển dụng."}), 404
    if job["approval_status"] != "approved":
        return jsonify({"error": "company_not_approved", "message": "Cần duyệt doanh nghiệp trước khi duyệt tin."}), 409
    note = (data.get("note") or "").strip()
    db.execute("""UPDATE jobs SET status = ?, review_note = ?, reviewed_by = ?,
                  reviewed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
               (decision, note, session["user_id"], job_id))
    _log_review(db, "job", job_id, decision, note)
    db.commit()
    return jsonify({"message": "Đã cập nhật kết quả duyệt tin.", "status": decision})


@admin_bp.get("/review-histories")
@roles_required(*STAFF_ROLES)
def review_histories():
    entity_type = request.args.get("entity_type")
    entity_id = request.args.get("entity_id", type=int)
    sql = """SELECT h.id, h.entity_type, h.entity_id, h.action, h.note, h.created_at,
                    u.email AS reviewer_email
             FROM review_histories h LEFT JOIN users u ON u.id = h.reviewer_id WHERE 1=1"""
    params = []
    if entity_type:
        if entity_type not in ("company", "job"):
            return jsonify({"error": "invalid_entity_type"}), 400
        sql += " AND h.entity_type = ?"
        params.append(entity_type)
    if entity_id is not None:
        sql += " AND h.entity_id = ?"
        params.append(entity_id)
    sql += " ORDER BY h.created_at DESC"
    return jsonify([dict(row) for row in get_db().execute(sql, params).fetchall()])


# -------------------------------- User CRUD --------------------------------
@admin_bp.get("/users")
@roles_required("admin")
def list_users():
    role = request.args.get("role")
    active = request.args.get("is_active")
    sql = "SELECT id, email, role, is_active, created_at FROM users WHERE 1=1"
    params = []
    if role:
        if role not in ALL_ROLES:
            return jsonify({"error": "invalid_role"}), 400
        sql += " AND role = ?"
        params.append(role)
    if active in ("0", "1"):
        sql += " AND is_active = ?"
        params.append(int(active))
    sql += " ORDER BY created_at DESC"
    return jsonify([dict(row) for row in get_db().execute(sql, params).fetchall()])


@admin_bp.post("/users")
@roles_required("admin")
def create_user():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role")
    if not email or "@" not in email or len(password) < 6 or role not in ALL_ROLES:
        return jsonify({"error": "invalid_input", "message": "Cần email hợp lệ, mật khẩu tối thiểu 6 ký tự và vai trò hợp lệ."}), 400
    db = get_db()
    try:
        cur = db.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                         (email, generate_password_hash(password), role))
        user_id = cur.lastrowid
        if role == "student":
            db.execute("INSERT INTO student_profiles (user_id) VALUES (?)", (user_id,))
        elif role == "business":
            db.execute("INSERT INTO companies (user_id, company_name) VALUES (?, ?)",
                       (user_id, (data.get("company_name") or "Chưa cập nhật").strip()))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "email_exists", "message": "Email đã tồn tại."}), 409
    return jsonify({"message": "Đã tạo tài khoản.", "user_id": user_id, "role": role}), 201


@admin_bp.get("/users/<int:user_id>")
@roles_required("admin")
def get_user(user_id):
    row = get_db().execute("""SELECT id, email, role, is_active, created_at FROM users WHERE id = ?""",
                           (user_id,)).fetchone()
    if not row:
        return jsonify({"error": "not_found"}), 404
    return jsonify(dict(row))


@admin_bp.put("/users/<int:user_id>")
@roles_required("admin")
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    user = db.execute("SELECT id, role, is_active FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return jsonify({"error": "not_found"}), 404
    new_role = data.get("role", user["role"])
    new_active = data.get("is_active", user["is_active"])
    if new_role not in ALL_ROLES or new_active not in (0, 1, True, False):
        return jsonify({"error": "invalid_input", "message": "role hoặc is_active không hợp lệ."}), 400
    if user_id == session["user_id"] and (new_role != "admin" or int(new_active) != 1):
        return jsonify({"error": "self_change_denied", "message": "Không thể tự hạ quyền hoặc tự khóa tài khoản đang đăng nhập."}), 409
    db.execute("UPDATE users SET role = ?, is_active = ? WHERE id = ?",
               (new_role, int(new_active), user_id))
    db.commit()
    return jsonify({"message": "Đã cập nhật tài khoản."})


@admin_bp.delete("/users/<int:user_id>")
@roles_required("admin")
def deactivate_user(user_id):
    if user_id == session["user_id"]:
        return jsonify({"error": "self_delete_denied", "message": "Không thể tự khóa tài khoản đang đăng nhập."}), 409
    db = get_db()
    cur = db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"message": "Đã vô hiệu hóa tài khoản; lịch sử được giữ lại."})


# ------------------------------- Category CRUD -------------------------------
@admin_bp.get("/categories")
@roles_required(*STAFF_ROLES)
def list_categories():
    rows = get_db().execute("SELECT * FROM job_categories ORDER BY name").fetchall()
    return jsonify([dict(row) for row in rows])


@admin_bp.post("/categories")
@roles_required("admin")
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "invalid_input", "message": "Tên danh mục là bắt buộc."}), 400
    try:
        cur = get_db().execute("INSERT INTO job_categories (name, description) VALUES (?, ?)",
                               (name, (data.get("description") or "").strip()))
        get_db().commit()
    except sqlite3.IntegrityError:
        get_db().rollback()
        return jsonify({"error": "category_exists", "message": "Tên danh mục đã tồn tại."}), 409
    return jsonify({"message": "Đã tạo danh mục.", "category_id": cur.lastrowid}), 201


@admin_bp.get("/categories/<int:category_id>")
@roles_required(*STAFF_ROLES)
def get_category(category_id):
    row = get_db().execute("SELECT * FROM job_categories WHERE id = ?", (category_id,)).fetchone()
    if not row:
        return jsonify({"error": "not_found"}), 404
    return jsonify(dict(row))


@admin_bp.put("/categories/<int:category_id>")
@roles_required("admin")
def update_category(category_id):
    data = request.get_json(silent=True) or {}
    row = get_db().execute("SELECT * FROM job_categories WHERE id = ?", (category_id,)).fetchone()
    if not row:
        return jsonify({"error": "not_found"}), 404
    name = (data.get("name", row["name"]) or "").strip()
    desc = (data.get("description", row["description"]) or "").strip()
    active = data.get("is_active", row["is_active"])
    if not name or active not in (0, 1, True, False):
        return jsonify({"error": "invalid_input"}), 400
    try:
        get_db().execute("UPDATE job_categories SET name = ?, description = ?, is_active = ? WHERE id = ?",
                         (name, desc, int(active), category_id))
        get_db().commit()
    except sqlite3.IntegrityError:
        get_db().rollback()
        return jsonify({"error": "category_exists"}), 409
    return jsonify({"message": "Đã cập nhật danh mục."})


@admin_bp.delete("/categories/<int:category_id>")
@roles_required("admin")
def delete_category(category_id):
    # Foreign-key ON DELETE SET NULL preserves jobs when their category is removed.
    cur = get_db().execute("DELETE FROM job_categories WHERE id = ?", (category_id,))
    get_db().commit()
    if cur.rowcount == 0:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"message": "Đã xóa danh mục; các tin cũ được giữ lại và bỏ liên kết danh mục."})


# ------------------------------ Career content CRUD ------------------------------
@admin_bp.get("/career-contents")
@roles_required(*STAFF_ROLES)
def list_all_career_contents():
    rows = get_db().execute("SELECT * FROM career_contents ORDER BY updated_at DESC").fetchall()
    return jsonify([dict(row) for row in rows])


@admin_bp.post("/career-contents")
@roles_required(*STAFF_ROLES)
def create_career_content():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    status = data.get("status", "draft")
    if not title or not body or status not in ("draft", "published"):
        return jsonify({"error": "invalid_input", "message": "Cần title, body và status hợp lệ."}), 400
    cur = get_db().execute("""INSERT INTO career_contents (title, summary, body, category, status, author_id)
                              VALUES (?, ?, ?, ?, ?, ?)""",
                           (title, (data.get("summary") or "").strip(), body,
                            (data.get("category") or "Hướng nghiệp").strip(), status, session["user_id"]))
    get_db().commit()
    return jsonify({"message": "Đã tạo nội dung hướng nghiệp.", "content_id": cur.lastrowid}), 201


@admin_bp.get("/career-contents/<int:content_id>")
@roles_required(*STAFF_ROLES)
def get_career_content(content_id):
    row = get_db().execute("SELECT * FROM career_contents WHERE id = ?", (content_id,)).fetchone()
    if not row:
        return jsonify({"error": "not_found"}), 404
    return jsonify(dict(row))


@admin_bp.put("/career-contents/<int:content_id>")
@roles_required(*STAFF_ROLES)
def update_career_content(content_id):
    db = get_db()
    row = db.execute("SELECT * FROM career_contents WHERE id = ?", (content_id,)).fetchone()
    if not row:
        return jsonify({"error": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    title = (data.get("title", row["title"]) or "").strip()
    body = (data.get("body", row["body"]) or "").strip()
    status = data.get("status", row["status"])
    if not title or not body or status not in ("draft", "published"):
        return jsonify({"error": "invalid_input", "message": "title/body không được rỗng; status phải là draft hoặc published."}), 400
    db.execute("""UPDATE career_contents SET title = ?, summary = ?, body = ?, category = ?, status = ?,
                  updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
               (title, (data.get("summary", row["summary"]) or "").strip(), body,
                (data.get("category", row["category"]) or "Hướng nghiệp").strip(), status, content_id))
    db.commit()
    return jsonify({"message": "Đã cập nhật nội dung hướng nghiệp."})


@admin_bp.delete("/career-contents/<int:content_id>")
@roles_required(*STAFF_ROLES)
def delete_career_content(content_id):
    cur = get_db().execute("DELETE FROM career_contents WHERE id = ?", (content_id,))
    get_db().commit()
    if cur.rowcount == 0:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"message": "Đã xóa nội dung hướng nghiệp."})
