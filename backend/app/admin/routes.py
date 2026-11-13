import sqlite3
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from app.database import get_db
from app.auth.guards import roles_required
from app.textutil import like_pattern

admin_bp = Blueprint("admin", __name__)
STAFF_ROLES = {"admin", "moderator"}
ALL_ROLES = {"student", "business", "moderator", "admin"}


def _log_review(db, entity_type, entity_id, action, note):
    db.execute("""INSERT INTO review_histories (reviewer_id, entity_type, entity_id, action, note)
                  VALUES (?, ?, ?, ?, ?)""", (session["user_id"], entity_type, entity_id, action, note))


def _int_query(name):
    raw = request.args.get(name)
    if raw in (None, ""):
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, (jsonify({"error": "invalid_input", "message": f"{name} phải là số nguyên."}), 400)


# ---------------------------- Dashboard / moderation ----------------------------

@admin_bp.get("/pending/companies")
@roles_required(*STAFF_ROLES)
def pending_companies():
    q = (request.args.get("q") or "").strip()
    sort = request.args.get("sort") or "oldest"

    if sort not in {"oldest", "newest"}:
        return jsonify({"error": "invalid_sort", "message": "sort phải là oldest hoặc newest."}), 400

    sql = """
        SELECT c.id, c.company_name, c.description, c.website,
               c.created_at, u.email
        FROM companies c
        JOIN users u ON u.id = c.user_id
        WHERE c.approval_status = 'pending'
          AND u.is_active = 1
    """
    params = []

    if q:
        sql += " AND (fold(c.company_name) LIKE ? ESCAPE '\\' OR fold(u.email) LIKE ? ESCAPE '\\')"
        params.extend([like_pattern(q)] * 2)

    order = "ASC" if sort == "oldest" else "DESC"
    sql += f" ORDER BY c.created_at {order}, c.id {order}"

    rows = get_db().execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows])


@admin_bp.get("/pending/jobs")
@roles_required(*STAFF_ROLES)
def pending_jobs():
    q = (request.args.get("q") or "").strip()
    location = (request.args.get("location") or "").strip()
    job_type = (request.args.get("job_type") or "").strip()
    sort = request.args.get("sort") or "oldest"

    category_id, bad = _int_query("category_id")
    if bad:
        return bad

    if category_id is not None and category_id <= 0:
        return jsonify({"error": "invalid_category_id", "message": "category_id phải là số nguyên dương."}), 400

    if job_type and job_type not in {"internship", "full_time", "part_time", "contract"}:
        return jsonify({"error": "invalid_job_type", "message": "job_type không hợp lệ."}), 400

    if sort not in {"oldest", "newest"}:
        return jsonify({"error": "invalid_sort", "message": "sort phải là oldest hoặc newest."}), 400

    sql = """
        SELECT j.id, j.title, j.description, j.created_at,
            j.category_id, j.location, j.job_type,
            c.id AS company_id, c.company_name
        FROM jobs j
        JOIN companies c ON c.id = j.company_id
        JOIN users u ON u.id = c.user_id
        WHERE j.status = 'pending'
          AND c.approval_status = 'approved'
          AND u.is_active = 1
    """
    params = []

    if q:
        sql += """
            AND (
                fold(j.title) LIKE ? ESCAPE '\\'
                OR fold(j.description) LIKE ? ESCAPE '\\'
                OR fold(c.company_name) LIKE ? ESCAPE '\\'
            )
        """
        params.extend([like_pattern(q)] * 3)

    if category_id is not None:
        sql += " AND j.category_id = ?"
        params.append(category_id)

    if location:
        sql += " AND fold(j.location) LIKE ? ESCAPE '\\'"
        params.append(like_pattern(location))

    if job_type:
        sql += " AND j.job_type = ?"
        params.append(job_type)

    order = "ASC" if sort == "oldest" else "DESC"
    sql += f" ORDER BY j.created_at {order}, j.id {order}"

    rows = get_db().execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows])


@admin_bp.get("/jobs")
@roles_required(*STAFF_ROLES)
def list_jobs_for_review():
    """Cross-role job list for moderation."""
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    location = (request.args.get("location") or "").strip()
    job_type = (request.args.get("job_type") or "").strip()

    category_id, bad = _int_query("category_id")
    if bad:
        return bad

    company_id, bad = _int_query("company_id")
    if bad:
        return bad

    if status and status not in {"pending", "approved", "rejected", "closed"}:
        return jsonify({"error": "invalid_status", "message": "status không hợp lệ."}), 400

    if job_type and job_type not in {"internship", "full_time", "part_time", "contract"}:
        return jsonify({"error": "invalid_input", "message": "job_type không hợp lệ."}), 400

    sql = """
        SELECT j.id, j.title, j.description, j.location, j.job_type,
               j.category_id, j.status, j.created_at, j.deadline,
               c.id AS company_id, c.company_name
        FROM jobs j
        JOIN companies c ON c.id = j.company_id
        JOIN users u ON u.id = c.user_id
        WHERE u.is_active = 1
    """
    params = []

    if q:
        sql += """
            AND (
                fold(j.title) LIKE ? ESCAPE '\\'
                OR fold(j.description) LIKE ? ESCAPE '\\'
                OR fold(c.company_name) LIKE ? ESCAPE '\\'
            )
        """
        params.extend([like_pattern(q)] * 3)

    if status:
        sql += " AND j.status = ?"
        params.append(status)

    if category_id is not None:
        sql += " AND j.category_id = ?"
        params.append(category_id)

    if location:
        sql += " AND fold(j.location) LIKE ? ESCAPE '\\'"
        params.append(like_pattern(location))

    if job_type:
        sql += " AND j.job_type = ?"
        params.append(job_type)

    if company_id is not None:
        sql += " AND c.id = ?"
        params.append(company_id)

    rows = get_db().execute(
        sql + " ORDER BY j.created_at DESC, j.id DESC", params
    ).fetchall()

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

    sql = """
        SELECT
            h.id,
            h.entity_type,
            h.entity_id,
            h.action,
            h.note,
            h.created_at,

            CASE
                WHEN h.entity_type = 'company' THEN c.company_name
                WHEN h.entity_type = 'job' THEN j.title
            END AS entity_name,

            u.email AS reviewer_email

        FROM review_histories h

        LEFT JOIN companies c
            ON h.entity_type = 'company'
            AND c.id = h.entity_id

        LEFT JOIN jobs j
            ON h.entity_type = 'job'
            AND j.id = h.entity_id

        LEFT JOIN users u
            ON u.id = h.reviewer_id

        WHERE 1=1
    """

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

    rows = get_db().execute(sql, params).fetchall()

    return jsonify([dict(row) for row in rows])


# ------------------------------- Staff dashboard -------------------------------
@admin_bp.get("/dashboard/summary")
@roles_required(*STAFF_ROLES)
def dashboard_summary():
    """Return aggregate platform metrics and the latest moderation decisions."""
    db = get_db()

    def count(sql, params=()):
        row = db.execute(sql, params).fetchone()
        return int(row["total"] or 0)

    stats = {
        "active_users": count("SELECT COUNT(*) AS total FROM users WHERE is_active = 1"),
        "active_students": count(
            "SELECT COUNT(*) AS total FROM users WHERE role = 'student' AND is_active = 1"
        ),
        "active_business_accounts": count(
            "SELECT COUNT(*) AS total FROM users WHERE role = 'business' AND is_active = 1"
        ),
        "companies_total": count(
            """SELECT COUNT(*) AS total FROM companies c
               JOIN users u ON u.id = c.user_id WHERE u.is_active = 1"""
        ),
        "companies_approved": count(
            """SELECT COUNT(*) AS total FROM companies c
               JOIN users u ON u.id = c.user_id
               WHERE c.approval_status = 'approved' AND u.is_active = 1"""
        ),
        "companies_pending": count(
            """SELECT COUNT(*) AS total FROM companies c
               JOIN users u ON u.id = c.user_id
               WHERE c.approval_status = 'pending' AND u.is_active = 1"""
        ),
        "jobs_total": count("SELECT COUNT(*) AS total FROM jobs"),
        "jobs_approved": count(
            """SELECT COUNT(*) AS total FROM jobs j
               JOIN companies c ON c.id = j.company_id
               JOIN users u ON u.id = c.user_id
               WHERE j.status = 'approved' AND c.approval_status = 'approved'
               AND u.is_active = 1
               AND (j.deadline IS NULL OR date(j.deadline) >= date('now'))"""
        ),
        "jobs_pending": count(
            """SELECT COUNT(*) AS total FROM jobs j
               JOIN companies c ON c.id = j.company_id
               JOIN users u ON u.id = c.user_id
               WHERE j.status = 'pending' AND c.approval_status = 'approved'
               AND u.is_active = 1"""
        ),
        "applications_total": count("SELECT COUNT(*) AS total FROM applications"),
        "applications_pending": count(
            "SELECT COUNT(*) AS total FROM applications WHERE status IN ('submitted', 'reviewing')"
        ),
        "categories_total": count("SELECT COUNT(*) AS total FROM job_categories"),
        "categories_active": count("SELECT COUNT(*) AS total FROM job_categories WHERE is_active = 1"),
        "contents_total": count("SELECT COUNT(*) AS total FROM career_contents"),
        "contents_published": count(
            "SELECT COUNT(*) AS total FROM career_contents WHERE status = 'published'"
        ),
        "contents_draft": count(
            "SELECT COUNT(*) AS total FROM career_contents WHERE status = 'draft'"
        ),
        "reviews_today": count(
            "SELECT COUNT(*) AS total FROM review_histories WHERE date(created_at) = date('now')"
        ),
    }

    recent_reviews = db.execute("""
        SELECT
            h.id,
            h.entity_type,
            h.entity_id,
            h.action,
            h.note,
            h.created_at,
            reviewer.email AS reviewer_email,
            CASE
                WHEN h.entity_type = 'company'
                    THEN COALESCE(c.company_name, 'Doanh nghiệp #' || h.entity_id)
                ELSE COALESCE(j.title, 'Tin tuyển dụng #' || h.entity_id)
            END AS entity_name
        FROM review_histories h
        LEFT JOIN users reviewer ON reviewer.id = h.reviewer_id
        LEFT JOIN companies c
            ON h.entity_type = 'company' AND c.id = h.entity_id
        LEFT JOIN jobs j
            ON h.entity_type = 'job' AND j.id = h.entity_id
        ORDER BY h.created_at DESC, h.id DESC
        LIMIT 8
    """).fetchall()

    return jsonify({
        "role": session.get("role"),
        "stats": stats,
        "recent_reviews": [dict(row) for row in recent_reviews],
    })


# -------------------------------- User CRUD --------------------------------
@admin_bp.get("/users")
@roles_required("admin")
def list_users():
    q = (request.args.get("q") or "").strip()
    role = request.args.get("role")
    active = request.args.get("is_active")
    sql = """SELECT u.id, u.email, u.role, u.is_active, u.created_at,
                     p.full_name, c.company_name
              FROM users u LEFT JOIN student_profiles p ON p.user_id = u.id
              LEFT JOIN companies c ON c.user_id = u.id WHERE 1=1"""
    params = []
    if q:
        sql += " AND (fold(u.email) LIKE ? ESCAPE '\\' OR fold(p.full_name) LIKE ? ESCAPE '\\' OR fold(c.company_name) LIKE ? ESCAPE '\\')"
        params.extend([like_pattern(q)] * 3)
    if role:
        if role not in ALL_ROLES:
            return jsonify({"error": "invalid_role"}), 400
        sql += " AND role = ?"
        params.append(role)
    if active in ("0", "1"):
        sql += " AND is_active = ?"
        params.append(int(active))
    sql += " ORDER BY u.created_at DESC"
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
    q = (request.args.get("q") or "").strip()
    active = request.args.get("is_active")

    if active not in (None, "", "0", "1"):
        return jsonify({
            "error": "invalid_input",
            "message": "is_active phải là 0 hoặc 1."
        }), 400

    sql = """
        SELECT c.*, p.name AS parent_name
        FROM job_categories c
        LEFT JOIN job_categories p ON p.id = c.parent_id
        WHERE 1=1
    """
    params = []

    if q:
        sql += " AND fold(c.name) LIKE ? ESCAPE '\\'"
        params.append(like_pattern(q))

    if active in ("0", "1"):
        sql += " AND c.is_active = ?"
        params.append(int(active))

    sql += " ORDER BY c.level, c.name"

    rows = get_db().execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows])

@admin_bp.post("/categories")
@roles_required("admin")
def create_category():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    active = data.get("is_active", 1)
    parent_id = data.get("parent_id")
    
    print("DEBUG CATEGORY:", repr(data))
    print("DEBUG NAME:", repr(name))
    print("DEBUG ACTIVE:", repr(active), type(active))
    print("DEBUG CONDITION:", not name, active not in (0, 1, True, False))

    if not name or active not in (0, 1, True, False):
        return jsonify({
            "error": "invalid_input",
            "message": "Tên danh mục và trạng thái không hợp lệ."
        }), 400

    # Mặc định danh mục không có cha là cấp 1
    level = 1

    if parent_id not in (None, ""):
        try:
            parent_id = int(parent_id)
        except (ValueError, TypeError):
            return jsonify({
                "error": "invalid_parent",
                "message": "Danh mục cha không hợp lệ."
            }), 400

        parent = get_db().execute("""
            SELECT id, level
            FROM job_categories
            WHERE id = ?
        """, (parent_id,)).fetchone()

        if not parent:
            return jsonify({
                "error": "parent_not_found",
                "message": "Danh mục cha không tồn tại."
            }), 404

        level = parent["level"] + 1

        if level > 3:
            return jsonify({
                "error": "max_level_reached",
                "message": "Không thể tạo danh mục cấp 4."
            }), 400

    try:
        cur = get_db().execute("""
            INSERT INTO job_categories (
                parent_id, level, name, description, is_active
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            parent_id if parent_id not in (None, "") else None,
            level,
            name,
            description,
            int(active)
        ))

        get_db().commit()

    except sqlite3.IntegrityError:
        get_db().rollback()
        return jsonify({
            "error": "category_exists",
            "message": "Tên danh mục đã tồn tại."
        }), 409

    return jsonify({
        "message": "Đã tạo danh mục.",
        "category_id": cur.lastrowid,
        "level": level
    }), 201

@admin_bp.get("/categories/<int:category_id>")
@roles_required(*STAFF_ROLES)
def get_category(category_id):
    row = get_db().execute("""
        SELECT
            c.*,
            p.name AS parent_name
        FROM job_categories c
        LEFT JOIN job_categories p ON p.id = c.parent_id
        WHERE c.id = ?
    """, (category_id,)).fetchone()

    if not row:
        return jsonify({
            "error": "not_found",
            "message": "Danh mục không tồn tại."
        }), 404

    return jsonify(dict(row))

@admin_bp.put("/categories/<int:category_id>")
@roles_required("admin")
def update_category(category_id):
    db = get_db()
    data = request.get_json(silent=True) or {}

    row = db.execute("""
        SELECT *
        FROM job_categories
        WHERE id = ?
    """, (category_id,)).fetchone()

    if not row:
        return jsonify({
            "error": "not_found",
            "message": "Danh mục không tồn tại."
        }), 404

    name = (data.get("name", row["name"]) or "").strip()
    description = (
        data.get("description", row["description"]) or ""
    ).strip()
    active = data.get("is_active", row["is_active"])

    # Nếu request không gửi parent_id thì giữ nguyên danh mục cha
    parent_id = data.get("parent_id", row["parent_id"])

    if not name or active not in (0, 1, True, False):
        return jsonify({
            "error": "invalid_input",
            "message": "Tên danh mục và trạng thái không hợp lệ."
        }), 400

    # Xác định cấp danh mục mới
    level = 1

    if parent_id not in (None, ""):
        try:
            parent_id = int(parent_id)
        except (ValueError, TypeError):
            return jsonify({
                "error": "invalid_parent",
                "message": "Danh mục cha không hợp lệ."
            }), 400

        parent = db.execute("""
            SELECT id, level
            FROM job_categories
            WHERE id = ?
        """, (parent_id,)).fetchone()

        if not parent:
            return jsonify({
                "error": "parent_not_found",
                "message": "Danh mục cha không tồn tại."
            }), 404

        # Không cho một danh mục làm danh mục cha của chính nó
        # hoặc của một danh mục nằm trong nhánh con của nó
        ancestor_id = parent_id

        while ancestor_id is not None:
            if ancestor_id == category_id:
                return jsonify({
                    "error": "category_cycle",
                    "message": "Không thể chọn danh mục hiện tại hoặc danh mục con làm danh mục cha."
                }), 400

            ancestor = db.execute("""
                SELECT parent_id
                FROM job_categories
                WHERE id = ?
            """, (ancestor_id,)).fetchone()

            ancestor_id = ancestor["parent_id"] if ancestor else None

        level = parent["level"] + 1

        if level > 3:
            return jsonify({
                "error": "max_level_reached",
                "message": "Không thể tạo danh mục cấp 4."
            }), 400

    # Nếu danh mục đang có danh mục con, không cho thay đổi cấp
    has_children = db.execute("""
        SELECT 1
        FROM job_categories
        WHERE parent_id = ?
        LIMIT 1
    """, (category_id,)).fetchone()

    if has_children and level != row["level"]:
        return jsonify({
            "error": "category_has_children",
            "message": "Không thể thay đổi cấp của danh mục đang có danh mục con."
        }), 409

    try:
        db.execute("""
            UPDATE job_categories
            SET
                parent_id = ?,
                level = ?,
                name = ?,
                description = ?,
                is_active = ?
            WHERE id = ?
        """, (
            parent_id if parent_id not in (None, "") else None,
            level,
            name,
            description,
            int(active),
            category_id
        ))

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({
            "error": "category_exists",
            "message": "Tên danh mục đã tồn tại."
        }), 409

    return jsonify({
        "message": "Đã cập nhật danh mục.",
        "level": level
    })


@admin_bp.delete("/categories/<int:category_id>")
@roles_required("admin")
def delete_category(category_id):
    db = get_db()

    row = db.execute("""
        SELECT id
        FROM job_categories
        WHERE id = ?
    """, (category_id,)).fetchone()

    if not row:
        return jsonify({
            "error": "not_found",
            "message": "Danh mục không tồn tại."
        }), 404

    # Không cho xóa danh mục đang có danh mục con
    has_children = db.execute("""
        SELECT 1
        FROM job_categories
        WHERE parent_id = ?
        LIMIT 1
    """, (category_id,)).fetchone()

    if has_children:
        return jsonify({
            "error": "category_has_children",
            "message": "Không thể xóa danh mục đang có danh mục con. Hãy xóa hoặc chuyển danh mục con trước."
        }), 409

    try:
        cur = db.execute("""
            DELETE FROM job_categories
            WHERE id = ?
        """, (category_id,))

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({
            "error": "delete_failed",
            "message": "Không thể xóa danh mục này."
        }), 409

    if cur.rowcount == 0:
        return jsonify({
            "error": "not_found",
            "message": "Danh mục không tồn tại."
        }), 404

    return jsonify({
        "message": "Đã xóa danh mục. Các tin tuyển dụng cũ vẫn được giữ lại."
    })

# ------------------------------ Career content CRUD ------------------------------
@admin_bp.get("/career-contents")
@roles_required(*STAFF_ROLES)
def list_all_career_contents():
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    status = (request.args.get("status") or "").strip()
    if status and status not in {"draft", "published"}:
        return jsonify({"error": "invalid_status", "message": "status phải là draft hoặc published."}), 400
    sql = "SELECT * FROM career_contents WHERE 1=1"
    params = []
    if q:
        sql += " AND (fold(title) LIKE ? ESCAPE '\\' OR fold(summary) LIKE ? ESCAPE '\\' OR fold(body) LIKE ? ESCAPE '\\')"
        params.extend([like_pattern(q)] * 3)
    if category:
        sql += " AND category = ?"
        params.append(category)
    if status:
        sql += " AND status = ?"
        params.append(status)
    rows = get_db().execute(sql + " ORDER BY updated_at DESC", params).fetchall()
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
