import sqlite3
from flask import Blueprint, request, jsonify, session
from app.database import get_db
from app.auth.guards import roles_required
from app.textutil import like_pattern

applications_bp = Blueprint("applications", __name__)


def _student_owned_application(db, application_id, student_id):
    return db.execute("SELECT * FROM applications WHERE id = ? AND student_id = ?",
                      (application_id, student_id)).fetchone()


@applications_bp.post("/jobs/<int:job_id>")
@roles_required("student")
def apply_to_job(job_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    job = db.execute("""
        SELECT j.id FROM jobs j JOIN companies c ON c.id = j.company_id
        JOIN users cu ON cu.id = c.user_id
        WHERE j.id = ? AND j.status = 'approved' AND c.approval_status = 'approved'
          AND cu.is_active = 1 AND (j.deadline IS NULL OR date(j.deadline) >= date('now'))
    """, (job_id,)).fetchone()
    if not job:
        return jsonify({"error": "job_unavailable", "message": "Tin không tồn tại, chưa được duyệt hoặc đã hết hạn."}), 404
    try:
        cur = db.execute("INSERT INTO applications (job_id, student_id, cover_letter) VALUES (?, ?, ?)",
                         (job_id, session["user_id"], (data.get("cover_letter") or "").strip()))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "already_applied", "message": "Bạn đã ứng tuyển tin này."}), 409
    return jsonify({"message": "Ứng tuyển thành công.", "application_id": cur.lastrowid}), 201


@applications_bp.get("/me")
@roles_required("student")
def my_applications():
    db = get_db()
    keyword = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    sort = request.args.get("sort") or "latest"
    sql = """
        SELECT a.id AS application_id, a.status, a.cover_letter, a.created_at, a.updated_at,
               j.id AS job_id, j.title, c.company_name
        FROM applications a JOIN jobs j ON j.id = a.job_id JOIN companies c ON c.id = j.company_id
        WHERE a.student_id = ?
    """
    params = [session["user_id"]]
    if keyword:
        sql += " AND (fold(j.title) LIKE ? ESCAPE '\\' OR fold(c.company_name) LIKE ? ESCAPE '\\')"
        params.extend([like_pattern(keyword)] * 2)
    if status in {"submitted", "reviewing", "accepted", "rejected", "withdrawn"}:
        sql += " AND a.status = ?"
        params.append(status)
    order = "a.created_at ASC" if sort == "oldest" else "a.created_at DESC"
    sql += " ORDER BY " + order
    rows = db.execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows])


@applications_bp.get("/<int:application_id>")
@roles_required("student")
def application_detail(application_id):
    row = get_db().execute("""
        SELECT a.id AS application_id, a.status, a.cover_letter, a.created_at, a.updated_at,
               j.id AS job_id, j.title, c.company_name
        FROM applications a JOIN jobs j ON j.id = a.job_id JOIN companies c ON c.id = j.company_id
        WHERE a.id = ? AND a.student_id = ?
    """, (application_id, session["user_id"])).fetchone()
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy đơn ứng tuyển."}), 404
    return jsonify(dict(row))


@applications_bp.put("/<int:application_id>")
@roles_required("student")
def update_application(application_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    row = _student_owned_application(db, application_id, session["user_id"])
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy đơn ứng tuyển."}), 404
    if row["status"] != "submitted":
        return jsonify({"error": "invalid_transition", "message": "Chỉ có thể sửa lời nhắn khi đơn đang ở trạng thái submitted."}), 409
    cover_letter = (data.get("cover_letter") or "").strip()
    db.execute("UPDATE applications SET cover_letter = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
               (cover_letter, application_id))
    db.commit()
    return jsonify({"message": "Đã cập nhật đơn ứng tuyển."})


@applications_bp.delete("/<int:application_id>")
@roles_required("student")
def withdraw_application(application_id):
    db = get_db()
    row = _student_owned_application(db, application_id, session["user_id"])
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy đơn ứng tuyển."}), 404
    if row["status"] not in ("submitted", "reviewing"):
        return jsonify({"error": "invalid_transition", "message": "Chỉ có thể rút đơn khi đang submitted hoặc reviewing."}), 409
    db.execute("UPDATE applications SET status = 'withdrawn', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
               (application_id,))
    db.commit()
    return jsonify({"message": "Đã rút đơn ứng tuyển; lịch sử được giữ lại."})
