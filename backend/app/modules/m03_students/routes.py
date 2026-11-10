import sqlite3
from datetime import date
from flask import Blueprint, jsonify, request, session

from app.auth.guards import roles_required
from app.database import get_db

m03_students_bp = Blueprint("m03_students", __name__)
STAFF_ROLES = ("admin", "moderator")
ENROLLMENT_STATUSES = {"active", "leave", "suspended", "completed", "withdrawn"}


def _error(code, message, status):
    return jsonify({"error": code, "message": message}), status


def _text(data, field, required=False, limit=255):
    value = data.get(field, "")
    if not isinstance(value, str):
        return None, f"{field} phải là chuỗi."
    value = value.strip()
    if required and not value:
        return None, f"{field} không được để trống."
    if len(value) > limit:
        return None, f"{field} tối đa {limit} ký tự."
    return value, None


@m03_students_bp.post("/intakes")
@roles_required(*STAFF_ROLES)
def accept_intake():
    """Record a verified handoff for an existing student account."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("invalid_input", "Body phải là một đối tượng JSON.", 400)

    user_id = data.get("student_user_id")
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        return _error("invalid_input", "student_user_id phải là số nguyên.", 400)
    values = {}
    for field, required, limit in (
        ("student_code", True, 80),
        ("program_code", True, 80),
        ("program_name", True, 255),
        ("cohort", True, 80),
        ("source_system", True, 120),
        ("reason", True, 1000),
        ("effective_from", False, 32),
    ):
        value, error = _text(data, field, required, limit)
        if error:
            return _error("invalid_input", error, 400)
        values[field] = value
    if values["effective_from"]:
        try:
            date.fromisoformat(values["effective_from"])
        except ValueError:
            return _error("invalid_input", "effective_from phải là ngày YYYY-MM-DD.", 400)

    db = get_db()
    student = db.execute(
        "SELECT id FROM users WHERE id = ? AND role = 'student' AND is_active = 1",
        (user_id,),
    ).fetchone()
    if not student:
        return _error("student_not_found", "Không tìm thấy tài khoản sinh viên đang hoạt động.", 404)

    if db.execute("""
        SELECT 1 FROM student_enrollments
        WHERE user_id = ? AND program_code = ? AND cohort = ?
    """, (user_id, values["program_code"], values["cohort"])).fetchone():
        return _error("duplicate_intake", "Lần theo học này đã được ghi nhận.", 409)

    try:
        existing_identifier = db.execute("""
            SELECT id, user_id FROM student_identifiers
            WHERE identifier_type = 'institutional' AND identifier_value = ?
        """, (values["student_code"],)).fetchone()
        if existing_identifier and existing_identifier["user_id"] != user_id:
            return _error(
                "duplicate_student_identifier",
                "Mã sinh viên đã được cấp cho một tài khoản khác.",
                409,
            )
        if existing_identifier:
            identifier_id = existing_identifier["id"]
        else:
            cursor = db.execute("""
                INSERT INTO student_identifiers
                    (user_id, identifier_type, identifier_value, source_system, issued_by)
                VALUES (?, 'institutional', ?, ?, ?)
            """, (user_id, values["student_code"], values["source_system"], session["user_id"]))
            identifier_id = cursor.lastrowid
        enrollment = db.execute("""
            INSERT INTO student_enrollments
                (user_id, program_code, program_name, cohort, status, effective_from,
                 change_reason, source_system, created_by)
            VALUES (?, ?, ?, ?, 'active', COALESCE(NULLIF(?, ''), CURRENT_TIMESTAMP), ?, ?, ?)
        """, (user_id, values["program_code"], values["program_name"], values["cohort"],
              values["effective_from"], values["reason"], values["source_system"], session["user_id"]))
        enrollment_id = enrollment.lastrowid
        db.execute("""
            INSERT INTO student_enrollment_history
                (enrollment_id, old_status, new_status, reason, changed_by)
            VALUES (?, NULL, 'active', ?, ?)
        """, (enrollment_id, values["reason"], session["user_id"]))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return _error(
            "duplicate_student_identifier",
            "Mã sinh viên đã được cấp hoặc tài khoản đã có mã định danh chính thức.",
            409,
        )

    return jsonify({
        "message": "Đã ghi nhận bàn giao và quá trình theo học.",
        "identifier_id": identifier_id,
        "enrollment_id": enrollment_id,
    }), 201


@m03_students_bp.get("/records/<int:user_id>")
@roles_required(*STAFF_ROLES)
def student_record(user_id):
    db = get_db()
    student = db.execute("""
        SELECT u.id AS user_id, u.email, p.full_name, p.major, p.phone, p.bio
        FROM users u JOIN student_profiles p ON p.user_id = u.id
        WHERE u.id = ? AND u.role = 'student'
    """, (user_id,)).fetchone()
    if not student:
        return _error("student_not_found", "Không tìm thấy hồ sơ sinh viên.", 404)
    identifiers = db.execute("""
        SELECT id, identifier_type, identifier_value, source_system, issued_at
        FROM student_identifiers WHERE user_id = ? ORDER BY issued_at
    """, (user_id,)).fetchall()
    enrollments = db.execute("""
        SELECT id, program_code, program_name, cohort, status, effective_from,
               effective_to, change_reason, source_system
        FROM student_enrollments WHERE user_id = ? ORDER BY effective_from DESC, id DESC
    """, (user_id,)).fetchall()
    links = db.execute("""
        SELECT id, link_type, system_key, external_id, created_at
        FROM student_system_links WHERE user_id = ? ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    return jsonify({
        "student": dict(student),
        "identifiers": [dict(row) for row in identifiers],
        "enrollments": [dict(row) for row in enrollments],
        "system_links": [dict(row) for row in links],
    })


@m03_students_bp.post("/records/<int:user_id>/system-links")
@roles_required(*STAFF_ROLES)
def add_system_link(user_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("invalid_input", "Body phải là một đối tượng JSON.", 400)
    values = {}
    for field in ("link_type", "system_key", "external_id"):
        value, error = _text(data, field, True, 160)
        if error:
            return _error("invalid_input", error, 400)
        values[field] = value
    if values["link_type"] not in {
        "academic_results", "financial_obligations", "support", "graduation"
    }:
        return _error("invalid_input", "Loại liên kết hồ sơ không hợp lệ.", 400)
    db = get_db()
    if not db.execute(
        "SELECT 1 FROM users WHERE id = ? AND role = 'student'", (user_id,)
    ).fetchone():
        return _error("student_not_found", "Không tìm thấy hồ sơ sinh viên.", 404)
    try:
        cursor = db.execute("""
            INSERT INTO student_system_links (user_id, link_type, system_key, external_id, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, values["link_type"], values["system_key"], values["external_id"],
              session["user_id"]))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return _error("duplicate_system_link", "Liên kết hệ thống này đã tồn tại.", 409)
    return jsonify({"message": "Đã liên kết hồ sơ với hệ thống nguồn.", "link_id": cursor.lastrowid}), 201


@m03_students_bp.patch("/enrollments/<int:enrollment_id>/status")
@roles_required(*STAFF_ROLES)
def change_enrollment_status(enrollment_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("invalid_input", "Body phải là một đối tượng JSON.", 400)
    status, error = _text(data, "status", True, 30)
    if error or status not in ENROLLMENT_STATUSES:
        return _error("invalid_input", error or "Trạng thái quá trình theo học không hợp lệ.", 400)
    reason, error = _text(data, "reason", True, 1000)
    if error:
        return _error("invalid_input", error, 400)
    effective_at, error = _text(data, "effective_at", False, 32)
    if error:
        return _error("invalid_input", error, 400)
    if effective_at:
        try:
            date.fromisoformat(effective_at)
        except ValueError:
            return _error("invalid_input", "effective_at phải là ngày YYYY-MM-DD.", 400)
    db = get_db()
    enrollment = db.execute(
        "SELECT status FROM student_enrollments WHERE id = ?", (enrollment_id,)
    ).fetchone()
    if not enrollment:
        return _error("enrollment_not_found", "Không tìm thấy quá trình theo học.", 404)
    old_status = enrollment["status"]
    if old_status == status:
        return _error("no_status_change", "Trạng thái mới trùng với trạng thái hiện tại.", 409)
    if old_status in {"completed", "withdrawn"}:
        return _error(
            "invalid_transition",
            "Quá trình đã hoàn tất/kết thúc; cần tạo lần theo học mới để tiếp tục.",
            409,
        )

    db.execute("""
        UPDATE student_enrollments
        SET status = ?, effective_to = CASE
                WHEN ? IN ('completed', 'withdrawn') THEN COALESCE(NULLIF(?, ''), CURRENT_TIMESTAMP)
                ELSE effective_to END,
            change_reason = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, status, effective_at, reason, enrollment_id))
    db.execute("""
        INSERT INTO student_enrollment_history
            (enrollment_id, old_status, new_status, effective_at, reason, changed_by)
        VALUES (?, ?, ?, COALESCE(NULLIF(?, ''), CURRENT_TIMESTAMP), ?, ?)
    """, (enrollment_id, old_status, status, effective_at, reason, session["user_id"]))
    db.commit()
    return jsonify({"message": "Đã cập nhật trạng thái quá trình theo học."})
