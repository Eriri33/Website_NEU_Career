import sqlite3
from datetime import date, datetime, timezone
from urllib.parse import urlparse

from flask import Blueprint, request, jsonify, session

from app.database import get_db
from app.auth.guards import roles_required
from app.textutil import like_pattern

companies_bp = Blueprint("companies", __name__)

VALID_JOB_TYPES = {"internship", "full_time", "part_time", "contract"}
VALID_SATURDAY_POLICIES = {"off", "working", "negotiable", "unknown"}
JOB_STATUSES = {"pending", "approved", "rejected", "closed"}
APPLICATION_STATUSES = ("submitted", "reviewing", "accepted", "rejected", "withdrawn")
STAFF_SETTABLE_STATUSES = {"reviewing", "accepted", "rejected"}

MAX_LEN = {
    "title": 150, "description": 10000, "location": 255, "major_required": 255,
    "skills_required": 500, "salary_text": 100,
    "company_name": 150, "company_description": 5000, "website": 255,
    "business_industries": 1000, "primary_industry": 255, "address": 500,
}
COMPANY_SIZES = {"", "1-9", "10-24", "25-99", "100-499", "500-999", "1000+"}

LIKE = "ESCAPE '\\'"


# helpers
def _error(code, message, status):
    return jsonify({"error": code, "message": message}), status


def _today():
    return datetime.now(timezone.utc).date()


def _json_body():
    """Trả về (dict, None) hoặc (None, response_lỗi)."""
    data = request.get_json(silent=True)
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, _error("invalid_input", "Body phải là một đối tượng JSON.", 400)
    return data, None


def _optional_int_arg(name):
    """Đọc tham số query kiểu số nguyên. Trả (giá_trị|None, lỗi|None)."""
    raw = request.args.get(name)
    if raw in (None, ""):
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, _error("invalid_input", f"{name} phải là số nguyên.", 400)


def _get_company(db, user_id):
    return db.execute("SELECT * FROM companies WHERE user_id = ?", (user_id,)).fetchone()


# Câu SELECT dùng chung cho tin của doanh nghiệp. `c.user_id = ?` luôn là điều kiện đầu tiên.
JOB_SELECT = """
    SELECT j.*, cat.name AS category_name,
           (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.id) AS application_count,
           (SELECT COUNT(*) FROM applications a
             WHERE a.job_id = j.id AND a.status = 'submitted') AS new_application_count,
           EXISTS(SELECT 1 FROM review_histories h
                   WHERE h.entity_type = 'job' AND h.entity_id = j.id) AS has_review_history
    FROM jobs j
    JOIN companies c ON c.id = j.company_id
    LEFT JOIN job_categories cat ON cat.id = j.category_id
"""


def _job_to_dict(row):
    item = dict(row)
    had_review = bool(item.pop("has_review_history", 0))
    # Tin quay lại pending sau khi từng được duyệt/từ chối = "chờ duyệt lại".
    item["needs_re_review"] = item["status"] == "pending" and had_review
    deadline = item.get("deadline")
    item["is_expired"] = bool(deadline) and deadline < _today().isoformat()
    return item


def _owned_job(db, job_id, user_id):
    return db.execute(JOB_SELECT + " WHERE j.id = ? AND c.user_id = ?", (job_id, user_id)).fetchone()


def _check_text_fields(data, keys):
    for key in keys:
        value = data.get(key)
        if value is not None and not isinstance(value, str):
            return f"{key} phải là chuỗi văn bản."
        if isinstance(value, str) and len(value.strip()) > MAX_LEN[key]:
            return f"{key} tối đa {MAX_LEN[key]} ký tự."
    return None


def _parse_category(db, data, current=None):
    """Trả (category_id|None, lỗi|None). Chỉ nhận danh mục đang hoạt động khi thay đổi giá trị."""
    raw = data.get("category_id")
    if raw in (None, ""):
        return None, None
    try:
        category_id = int(raw)
    except (TypeError, ValueError):
        return None, "category_id phải là số nguyên."
    if current is not None and category_id == current:
        return category_id, None
    row = db.execute("SELECT is_active FROM job_categories WHERE id = ?", (category_id,)).fetchone()
    if not row or not row["is_active"]:
        return None, "Danh mục không tồn tại hoặc đã bị tắt."
    return category_id, None


def _validate_job_payload(data, partial=False, current_deadline=None):
    text_error = _check_text_fields(
        data, ("title", "description", "location", "major_required", "skills_required", "salary_text"))
    if text_error:
        return text_error
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
    policy = data.get("saturday_policy")
    if policy is not None and policy not in VALID_SATURDAY_POLICIES:
        return "saturday_policy phải là off, working, negotiable hoặc unknown."
    deadline = data.get("deadline")
    if deadline:
        try:
            parsed = date.fromisoformat(deadline)
        except (ValueError, TypeError):
            return "deadline phải có định dạng YYYY-MM-DD."
        # Chỉ chặn hạn đã qua khi hạn đó là giá trị mới (không chặn khi giữ nguyên hạn cũ).
        if parsed < _today() and deadline != current_deadline:
            return "Hạn nộp hồ sơ không được nằm trong quá khứ."
    return None


def _validate_website(website):
    """Chỉ nhận http/https để không render được liên kết javascript: ở trang công khai."""
    if not website:
        return None
    parsed = urlparse(website)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "Website phải bắt đầu bằng http:// hoặc https://."
    return None


def _company_profile_value(data, company, key):
    """Keep existing optional profile data unless the client explicitly changes it."""
    return (data.get(key) if key in data else company[key]) or ""


# profile
@companies_bp.route("/profile", methods=["GET", "PUT"])
@roles_required("business")
def company_profile():
    db = get_db()
    company = _get_company(db, session["user_id"])
    if not company:
        return _error("not_found", "Chưa có hồ sơ doanh nghiệp.", 404)
    if request.method == "GET":
        result = dict(company)
        user = db.execute("SELECT email FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        result["email"] = user["email"] if user else ""
        return jsonify(result)

    data, bad = _json_body()
    if bad:
        return bad
    name = data.get("company_name")
    if not isinstance(name, str) or not name.strip():
        return _error("invalid_input", "Tên doanh nghiệp không được để trống.", 400)
    description = _company_profile_value(data, company, "description")
    website = _company_profile_value(data, company, "website")
    company_size = _company_profile_value(data, company, "company_size")
    business_industries = _company_profile_value(data, company, "business_industries")
    primary_industry = _company_profile_value(data, company, "primary_industry")
    address = _company_profile_value(data, company, "address")
    for label, value, limit in (("Tên doanh nghiệp", name, MAX_LEN["company_name"]),
                                ("Mô tả", description, MAX_LEN["company_description"]),
                                ("Website", website, MAX_LEN["website"])):
        if value is not None and not isinstance(value, str):
            return _error("invalid_input", f"{label} phải là chuỗi văn bản.", 400)
        if value and len(value.strip()) > limit:
            return _error("invalid_input", f"{label} tối đa {limit} ký tự.", 400)
    website = (website or "").strip()
    site_error = _validate_website(website)
    if site_error:
        return _error("invalid_input", site_error, 400)
    for label, value, limit in (("Lĩnh vực kinh doanh", business_industries, MAX_LEN["business_industries"]),
                                ("Ngành nghề chính", primary_industry, MAX_LEN["primary_industry"]),
                                ("Địa chỉ", address, MAX_LEN["address"])):
        if not isinstance(value, str):
            return _error("invalid_input", f"{label} phải là chuỗi văn bản.", 400)
        if len(value.strip()) > limit:
            return _error("invalid_input", f"{label} tối đa {limit} ký tự.", 400)
    if not isinstance(company_size, str) or company_size not in COMPANY_SIZES:
        return _error("invalid_input", "Quy mô công ty không hợp lệ.", 400)
    db.execute("""
        UPDATE companies SET company_name = ?, description = ?, website = ?, company_size = ?,
            business_industries = ?, primary_industry = ?, address = ?,
            approval_status = 'pending', review_note = '', reviewed_by = NULL, reviewed_at = NULL
        WHERE user_id = ?
    """, (name.strip(), description.strip(), website, company_size, business_industries.strip(),
          primary_industry.strip(), address.strip(), session["user_id"]))
    db.commit()
    return jsonify({"message": "Đã cập nhật hồ sơ; doanh nghiệp cần được duyệt lại."})


@companies_bp.get("/public/<int:company_id>")
def public_company_profile(company_id):
    """A safe public profile used by the share link and student discovery pages."""
    row = get_db().execute("""
        SELECT c.id, c.company_name, c.description, c.website, c.company_size,
               c.business_industries, c.primary_industry, c.address, c.created_at
        FROM companies c JOIN users u ON u.id = c.user_id
        WHERE c.id = ? AND c.approval_status = 'approved' AND u.is_active = 1
    """, (company_id,)).fetchone()
    if not row:
        return _error("not_found", "Không tìm thấy hồ sơ doanh nghiệp công khai.", 404)
    return jsonify(dict(row))


@companies_bp.get("/categories")
@roles_required("business")
def list_categories():
    """Danh mục đang hoạt động để chọn khi đăng tin (không phụ thuộc endpoint staff/public)."""
    rows = get_db().execute(
        "SELECT id, name FROM job_categories WHERE is_active = 1 ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])


# jobs
@companies_bp.get("/jobs")
@roles_required("business")
def list_my_jobs():
    args = request.args
    q = (args.get("q") or "").strip()
    status = (args.get("status") or "").strip()
    location = (args.get("location") or "").strip()
    job_type = (args.get("job_type") or "").strip()
    sort = (args.get("sort") or "latest").strip()
    category_id, bad = _optional_int_arg("category_id")
    if bad:
        return bad
    if status and status not in JOB_STATUSES:
        return _error("invalid_status", "status phải là pending, approved, rejected hoặc closed.", 400)
    if job_type and job_type not in VALID_JOB_TYPES:
        return _error("invalid_input", "job_type không hợp lệ.", 400)
    if sort not in ("latest", "deadline_soon"):
        return _error("invalid_sort", "sort phải là latest hoặc deadline_soon.", 400)

    sql = JOB_SELECT + " WHERE c.user_id = ?"  # ràng buộc sở hữu trước mọi bộ lọc
    params = [session["user_id"]]
    if q:
        sql += f" AND (fold(j.title) LIKE ? {LIKE} OR fold(j.description) LIKE ? {LIKE})"
        params.extend([like_pattern(q)] * 2)
    if status:
        sql += " AND j.status = ?"
        params.append(status)
    if category_id is not None:
        sql += " AND j.category_id = ?"
        params.append(category_id)
    if location:
        sql += f" AND fold(j.location) LIKE ? {LIKE}"
        params.append(like_pattern(location))
    if job_type:
        sql += " AND j.job_type = ?"
        params.append(job_type)
    if sort == "deadline_soon":
        sql += " ORDER BY (j.deadline IS NULL OR j.deadline = ''), j.deadline ASC, j.created_at DESC, j.id DESC"
    else:
        sql += " ORDER BY j.created_at DESC, j.id DESC"
    rows = get_db().execute(sql, params).fetchall()
    return jsonify([_job_to_dict(row) for row in rows])


@companies_bp.post("/jobs")
@roles_required("business")
def create_job():
    data, bad = _json_body()
    if bad:
        return bad
    error = _validate_job_payload(data)
    if error:
        return _error("invalid_input", error, 400)
    db = get_db()
    company = _get_company(db, session["user_id"])
    if not company:
        return _error("company_not_found", "Chưa có hồ sơ doanh nghiệp.", 404)
    if company["approval_status"] != "approved":
        return _error("company_not_approved", "Doanh nghiệp phải được duyệt trước khi đăng tin.", 403)
    category_id, cat_error = _parse_category(db, data)
    if cat_error:
        return _error("invalid_category", cat_error, 400)
    try:
        cur = db.execute("""
            INSERT INTO jobs (company_id, category_id, title, description, location, job_type,
                major_required, skills_required, deadline, salary_text, saturday_policy, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (company["id"], category_id, data["title"].strip(), data["description"].strip(),
              (data.get("location") or "").strip(), data.get("job_type") or "internship",
              (data.get("major_required") or "").strip(), (data.get("skills_required") or "").strip(),
              data.get("deadline") or None,
              (data.get("salary_text") or "").strip() or "Thỏa thuận",
              data.get("saturday_policy") or "unknown"))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return _error("invalid_category", "Danh mục không tồn tại hoặc dữ liệu không hợp lệ.", 400)
    return jsonify({"message": "Đã tạo tin; tin đang chờ kiểm duyệt.",
                    "job_id": cur.lastrowid, "status": "pending"}), 201


@companies_bp.route("/jobs/<int:job_id>", methods=["GET", "PUT", "DELETE"])
@roles_required("business")
def manage_job(job_id):
    db = get_db()
    job = _owned_job(db, job_id, session["user_id"])
    if not job:
        return _error("not_found", "Không tìm thấy tin thuộc doanh nghiệp của bạn.", 404)

    if request.method == "GET":
        return jsonify(_job_to_dict(job))

    if request.method == "DELETE":
        # Đóng tin thay vì xóa cứng để giữ lịch sử ứng tuyển.
        db.execute("UPDATE jobs SET status = 'closed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (job_id,))
        db.commit()
        return jsonify({"message": "Đã đóng tin tuyển dụng; dữ liệu ứng tuyển được giữ lại."})

    data, bad = _json_body()
    if bad:
        return bad
    error = _validate_job_payload(data, partial=True, current_deadline=job["deadline"])
    if error:
        return _error("invalid_input", error, 400)
    if "category_id" in data:
        category_id, cat_error = _parse_category(db, data, current=job["category_id"])
        if cat_error:
            return _error("invalid_category", cat_error, 400)
    else:
        category_id = job["category_id"]

    def keep(key):  # field không gửi -> giữ giá trị cũ
        return ((data.get(key) if key in data else job[key]) or "")

    fields = {
        "title": (data.get("title") or job["title"]).strip(),
        "description": (data.get("description") or job["description"]).strip(),
        "location": keep("location").strip(),
        "job_type": data.get("job_type") or job["job_type"],
        "major_required": keep("major_required").strip(),
        "skills_required": keep("skills_required").strip(),
        "deadline": (data.get("deadline") if "deadline" in data else job["deadline"]) or None,
        "salary_text": (keep("salary_text").strip() or "Thỏa thuận"),
        "saturday_policy": data.get("saturday_policy") or job["saturday_policy"],
    }
    try:
        # Sửa tin luôn đưa tin về pending để kiểm duyệt lại.
        db.execute("""
            UPDATE jobs SET category_id = ?, title = ?, description = ?, location = ?, job_type = ?,
                major_required = ?, skills_required = ?, deadline = ?, salary_text = ?, saturday_policy = ?,
                status = 'pending', review_note = '', reviewed_by = NULL, reviewed_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (category_id, fields["title"], fields["description"], fields["location"], fields["job_type"],
              fields["major_required"], fields["skills_required"], fields["deadline"],
              fields["salary_text"], fields["saturday_policy"], job_id))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return _error("invalid_category", "Danh mục không tồn tại hoặc dữ liệu không hợp lệ.", 400)
    return jsonify({"message": "Đã cập nhật tin; tin quay lại trạng thái chờ duyệt.", "status": "pending"})


# applications
APPLICATION_BASE = """
    FROM applications a
    JOIN jobs j ON j.id = a.job_id
    JOIN companies c ON c.id = j.company_id
    JOIN users u ON u.id = a.student_id
    LEFT JOIN student_profiles p ON p.user_id = u.id
    WHERE c.user_id = ?
"""


def _application_scope_filters(include_status=True):
    """Bộ lọc dùng chung cho danh sách và thống kê. Trả (sql_bổ_sung, params, lỗi)."""
    args = request.args
    job_id, bad = _optional_int_arg("job_id")
    if bad:
        return None, None, bad
    status = (args.get("status") or "").strip()
    q = (args.get("q") or "").strip()
    if include_status and status and status not in APPLICATION_STATUSES:
        return None, None, _error(
            "invalid_status", "status phải là submitted, reviewing, accepted, rejected hoặc withdrawn.", 400)
    sql, params = "", []
    if job_id is not None:
        sql += " AND j.id = ?"
        params.append(job_id)
    if include_status and status:
        sql += " AND a.status = ?"
        params.append(status)
    if q:
        sql += (f" AND (fold(p.full_name) LIKE ? {LIKE} OR fold(u.email) LIKE ? {LIKE}"
                f" OR fold(p.major) LIKE ? {LIKE} OR fold(p.skills) LIKE ? {LIKE})")
        params.extend([like_pattern(q)] * 4)
    return sql, params, None


@companies_bp.get("/applications")
@roles_required("business")
def list_applications_for_company():
    sort = (request.args.get("sort") or "latest").strip()
    if sort not in ("latest", "oldest"):
        return _error("invalid_sort", "sort phải là latest hoặc oldest.", 400)
    extra, params, bad = _application_scope_filters()
    if bad:
        return bad
    order = "a.created_at ASC, a.id ASC" if sort == "oldest" else "a.created_at DESC, a.id DESC"
    sql = f"""
        SELECT a.id AS application_id, a.status, a.cover_letter, a.created_at, a.updated_at,
               j.id AS job_id, j.title, u.id AS student_id, u.email,
               p.full_name, p.major, p.skills
        {APPLICATION_BASE} {extra} ORDER BY {order}
    """
    rows = get_db().execute(sql, [session["user_id"]] + params).fetchall()
    return jsonify([dict(row) for row in rows])


@companies_bp.get("/applications/stats")
@roles_required("business")
def application_stats():
    """Số đơn theo trạng thái trong phạm vi job_id/q (không áp dụng status) — dùng cho tab đếm."""
    extra, params, bad = _application_scope_filters(include_status=False)
    if bad:
        return bad
    rows = get_db().execute(
        f"SELECT a.status AS status, COUNT(*) AS n {APPLICATION_BASE} {extra} GROUP BY a.status",
        [session["user_id"]] + params).fetchall()
    counts = {status: 0 for status in APPLICATION_STATUSES}
    for row in rows:
        counts[row["status"]] = row["n"]
    counts["total"] = sum(counts[s] for s in APPLICATION_STATUSES)
    return jsonify(counts)


@companies_bp.get("/applications/<int:application_id>")
@roles_required("business")
def company_application_detail(application_id):
    row = get_db().execute(f"""
        SELECT a.id AS application_id, a.status, a.cover_letter, a.created_at, a.updated_at,
               j.id AS job_id, j.title, j.status AS job_status, u.id AS student_id, u.email,
               p.full_name, p.major, p.skills, p.phone, p.bio
        {APPLICATION_BASE} AND a.id = ?
    """, (session["user_id"], application_id)).fetchone()
    if not row:
        return _error("not_found", "Không tìm thấy đơn thuộc tin của doanh nghiệp.", 404)
    return jsonify(dict(row))


@companies_bp.patch("/applications/<int:application_id>/status")
@roles_required("business")
def update_application_status(application_id):
    data, bad = _json_body()
    if bad:
        return bad
    status = data.get("status")
    if status not in STAFF_SETTABLE_STATUSES:
        return _error("invalid_status", "status phải là reviewing, accepted hoặc rejected.", 400)
    db = get_db()
    row = db.execute("""
        SELECT a.id, a.status FROM applications a JOIN jobs j ON j.id = a.job_id
        JOIN companies c ON c.id = j.company_id
        WHERE a.id = ? AND c.user_id = ?
    """, (application_id, session["user_id"])).fetchone()
    if not row:
        return _error("not_found", "Không tìm thấy đơn thuộc doanh nghiệp của bạn.", 404)
    if row["status"] == "withdrawn":
        return _error("invalid_transition", "Ứng viên đã rút đơn; không thể cập nhật.", 409)
    db.execute("UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
               (status, application_id))
    db.commit()
    return jsonify({"message": "Đã cập nhật trạng thái đơn ứng tuyển.", "status": status})
