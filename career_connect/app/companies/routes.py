import sqlite3
from datetime import date
from flask import Blueprint, request, jsonify, session
from app.database import get_db
from app.auth.guards import roles_required

companies_bp = Blueprint("companies", __name__)
VALID_JOB_TYPES = {"internship", "full_time", "part_time", "contract"}


def _get_company(db, user_id):
    return db.execute("SELECT * FROM companies WHERE user_id = ?", (user_id,)).fetchone()


def _owned_job(db, job_id, user_id):
    return db.execute("""
        SELECT j.* FROM jobs j JOIN companies c ON c.id = j.company_id
        WHERE j.id = ? AND c.user_id = ?
    """, (job_id, user_id)).fetchone()


def _validate_job_payload(data, partial=False):
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    if not partial and (not title or not description):
        return "Tiêu đề và mô tả công việc là bắt buộc."
    if "title" in data and not title:
        return "Tiêu đề không được để trống."
    if "description" in data and not description:
        return "Mô tả công việc không được để trống."
    job_type = data.get("job_type")
    if job_type is not None and job_type not in VALID_JOB_TYPES:
        return "job_type phải là internship, full_time, part_time hoặc contract."
    deadline = data.get("deadline")
    if deadline:
        try:
            date.fromisoformat(deadline)
        except (ValueError, TypeError):
            return "deadline phải có định dạng YYYY-MM-DD."
    return None


@companies_bp.route("/profile", methods=["GET", "PUT"])
@roles_required("business")
def company_profile():
    db = get_db()
    company = _get_company(db, session["user_id"])
    if not company:
        return jsonify({"error": "not_found", "message": "Chưa có hồ sơ doanh nghiệp."}), 404
    if request.method == "GET":
        return jsonify(dict(company))
    data = request.get_json(silent=True) or {}
    name = (data.get("company_name") or "").strip()
    if not name:
        return jsonify({"error": "invalid_input", "message": "Tên doanh nghiệp không được để trống."}), 400
    db.execute("""
        UPDATE companies SET company_name = ?, description = ?, website = ?,
            approval_status = 'pending', review_note = '', reviewed_by = NULL, reviewed_at = NULL
        WHERE user_id = ?
    """, (name, (data.get("description") or "").strip(), (data.get("website") or "").strip(), session["user_id"]))
    db.commit()
    return jsonify({"message": "Đã cập nhật hồ sơ; doanh nghiệp cần được duyệt lại."})


@companies_bp.get("/jobs")
@roles_required("business")
def list_my_jobs():
    rows = get_db().execute("""
        SELECT j.*, cat.name AS category_name FROM jobs j
        JOIN companies c ON c.id = j.company_id
        LEFT JOIN job_categories cat ON cat.id = j.category_id
        WHERE c.user_id = ? ORDER BY j.created_at DESC
    """, (session["user_id"],)).fetchall()
    return jsonify([dict(row) for row in rows])


@companies_bp.post("/jobs")
@roles_required("business")
def create_job():
    data = request.get_json(silent=True) or {}
    error = _validate_job_payload(data)
    if error:
        return jsonify({"error": "invalid_input", "message": error}), 400
    db = get_db()
    company = _get_company(db, session["user_id"])
    if not company:
        return jsonify({"error": "company_not_found"}), 404
    if company["approval_status"] != "approved":
        return jsonify({"error": "company_not_approved", "message": "Doanh nghiệp phải được duyệt trước khi đăng tin."}), 403
    try:
        cur = db.execute("""
            INSERT INTO jobs (company_id, category_id, title, description, location, job_type,
                major_required, skills_required, deadline, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (company["id"], data.get("category_id") or None, data["title"].strip(), data["description"].strip(),
              (data.get("location") or "").strip(), data.get("job_type") or "internship",
              (data.get("major_required") or "").strip(), (data.get("skills_required") or "").strip(),
              data.get("deadline") or None))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "invalid_category", "message": "Danh mục không tồn tại hoặc dữ liệu không hợp lệ."}), 400
    return jsonify({"message": "Đã tạo tin; tin đang chờ kiểm duyệt.", "job_id": cur.lastrowid, "status": "pending"}), 201


@companies_bp.route("/jobs/<int:job_id>", methods=["GET", "PUT", "DELETE"])
@roles_required("business")
def manage_job(job_id):
    db = get_db()
    job = _owned_job(db, job_id, session["user_id"])
    if not job:
        return jsonify({"error": "not_found", "message": "Không tìm thấy tin thuộc doanh nghiệp của bạn."}), 404

    if request.method == "GET":
        result = dict(job)
        return jsonify(result)

    if request.method == "DELETE":
        # Close instead of hard delete, preserving application history.
        db.execute("UPDATE jobs SET status = 'closed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (job_id,))
        db.commit()
        return jsonify({"message": "Đã đóng tin tuyển dụng; dữ liệu ứng tuyển được giữ lại."})

    data = request.get_json(silent=True) or {}
    error = _validate_job_payload(data, partial=True)
    if error:
        return jsonify({"error": "invalid_input", "message": error}), 400
    fields = {
        "title": (data.get("title") or job["title"]).strip(),
        "description": (data.get("description") or job["description"]).strip(),
        "location": (data.get("location") if "location" in data else job["location"]) or "",
        "job_type": data.get("job_type") or job["job_type"],
        "major_required": (data.get("major_required") if "major_required" in data else job["major_required"]) or "",
        "skills_required": (data.get("skills_required") if "skills_required" in data else job["skills_required"]) or "",
        "deadline": (data.get("deadline") if "deadline" in data else job["deadline"]) or None,
        "category_id": (data.get("category_id") if "category_id" in data else job["category_id"]) or None,
    }
    try:
        db.execute("""
            UPDATE jobs SET category_id = ?, title = ?, description = ?, location = ?, job_type = ?,
                major_required = ?, skills_required = ?, deadline = ?, status = 'pending',
                review_note = '', reviewed_by = NULL, reviewed_at = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (fields["category_id"], fields["title"], fields["description"], fields["location"],
              fields["job_type"], fields["major_required"], fields["skills_required"], fields["deadline"], job_id))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "invalid_category", "message": "Danh mục không tồn tại hoặc dữ liệu không hợp lệ."}), 400
    return jsonify({"message": "Đã cập nhật tin; tin quay lại trạng thái chờ duyệt."})


@companies_bp.get("/applications")
@roles_required("business")
def list_applications_for_company():
    job_id = request.args.get("job_id", type=int)
    sql = """
        SELECT a.id AS application_id, a.status, a.cover_letter, a.created_at, a.updated_at,
               j.id AS job_id, j.title, u.id AS student_id, u.email,
               p.full_name, p.major, p.skills
        FROM applications a JOIN jobs j ON j.id = a.job_id
        JOIN companies c ON c.id = j.company_id
        JOIN users u ON u.id = a.student_id
        LEFT JOIN student_profiles p ON p.user_id = u.id
        WHERE c.user_id = ?
    """
    params = [session["user_id"]]
    if job_id:
        sql += " AND j.id = ?"
        params.append(job_id)
    sql += " ORDER BY a.created_at DESC"
    rows = get_db().execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows])


@companies_bp.get("/applications/<int:application_id>")
@roles_required("business")
def company_application_detail(application_id):
    row = get_db().execute("""
        SELECT a.id AS application_id, a.status, a.cover_letter, a.created_at, a.updated_at,
               j.id AS job_id, j.title, u.id AS student_id, u.email,
               p.full_name, p.major, p.skills, p.phone
        FROM applications a JOIN jobs j ON j.id = a.job_id
        JOIN companies c ON c.id = j.company_id
        JOIN users u ON u.id = a.student_id
        LEFT JOIN student_profiles p ON p.user_id = u.id
        WHERE a.id = ? AND c.user_id = ?
    """, (application_id, session["user_id"])).fetchone()
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy đơn thuộc tin của doanh nghiệp."}), 404
    return jsonify(dict(row))


@companies_bp.patch("/applications/<int:application_id>/status")
@roles_required("business")
def update_application_status(application_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in {"reviewing", "accepted", "rejected"}:
        return jsonify({"error": "invalid_status", "message": "status phải là reviewing, accepted hoặc rejected."}), 400
    db = get_db()
    row = db.execute("""
        SELECT a.id, a.status FROM applications a JOIN jobs j ON j.id = a.job_id
        JOIN companies c ON c.id = j.company_id
        WHERE a.id = ? AND c.user_id = ?
    """, (application_id, session["user_id"])).fetchone()
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy đơn thuộc doanh nghiệp của bạn."}), 404
    if row["status"] == "withdrawn":
        return jsonify({"error": "invalid_transition", "message": "Ứng viên đã rút đơn; không thể cập nhật."}), 409
    db.execute("UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
               (status, application_id))
    db.commit()
    return jsonify({"message": "Đã cập nhật trạng thái đơn ứng tuyển.", "status": status})
