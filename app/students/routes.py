import os
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, session, current_app, send_from_directory
from werkzeug.utils import secure_filename
from app.database import get_db
from app.auth.guards import roles_required

students_bp = Blueprint("students", __name__)
ALLOWED_CV_EXTENSIONS = {".pdf", ".doc", ".docx"}


@students_bp.route("/me", methods=["GET", "PUT"])
@roles_required("student")
def student_me():
    db = get_db()
    user_id = session["user_id"]
    if request.method == "GET":
        row = db.execute("""
            SELECT u.id, u.email, p.full_name, p.major, p.skills, p.phone, p.bio, p.updated_at
            FROM users u JOIN student_profiles p ON p.user_id = u.id WHERE u.id = ?
        """, (user_id,)).fetchone()
        return jsonify(dict(row)) if row else (jsonify({"error": "not_found"}), 404)

    data = request.get_json(silent=True) or {}
    db.execute("""
        UPDATE student_profiles SET full_name = ?, major = ?, skills = ?, phone = ?, bio = ?,
            updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    """, ((data.get("full_name") or "").strip(), (data.get("major") or "").strip(),
          (data.get("skills") or "").strip(), (data.get("phone") or "").strip(),
          (data.get("bio") or "").strip(), user_id))
    db.commit()
    return jsonify({"message": "Đã cập nhật hồ sơ sinh viên."})


@students_bp.get("/me/recommendations")
@roles_required("student")
def recommendations():
    """Simple rule-based recommendations; not an AI recommender."""
    db = get_db()
    profile = db.execute("SELECT major, skills FROM student_profiles WHERE user_id = ?",
                         (session["user_id"],)).fetchone()
    if not profile:
        return jsonify([])
    major = (profile["major"] or "").strip().lower()
    skills = {item.strip().lower() for item in (profile["skills"] or "").replace(";", ",").split(",") if item.strip()}
    rows = db.execute("""
        SELECT j.id, j.title, j.description, j.location, j.job_type, j.major_required,
               j.skills_required, j.deadline, c.company_name
        FROM jobs j JOIN companies c ON c.id = j.company_id
        JOIN users cu ON cu.id = c.user_id
        WHERE j.status = 'approved' AND c.approval_status = 'approved' AND cu.is_active = 1
          AND (j.deadline IS NULL OR date(j.deadline) >= date('now'))
    """).fetchall()
    output = []
    for row in rows:
        item = dict(row)
        required_major = (item.get("major_required") or "").lower()
        required_skills = {s.strip().lower() for s in (item.get("skills_required") or "").replace(";", ",").split(",") if s.strip()}
        score = 0
        if not required_major or (major and (major in required_major or required_major in major)):
            score += 2
        score += len(skills & required_skills)
        if score > 0:
            item["match_score"] = score
            output.append(item)
    output.sort(key=lambda x: (x["match_score"], x.get("deadline") or "9999-12-31"), reverse=True)
    return jsonify(output[:20])


@students_bp.get("/me/cvs")
@roles_required("student")
def list_cvs():
    rows = get_db().execute("""
        SELECT id, original_filename, created_at FROM student_cvs
        WHERE student_id = ? ORDER BY created_at DESC
    """, (session["user_id"],)).fetchall()
    return jsonify([dict(row) for row in rows])


@students_bp.post("/me/cvs")
@roles_required("student")
def upload_cv():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "missing_file", "message": "Hãy chọn file CV."}), 400
    original_name = secure_filename(file.filename)
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_CV_EXTENSIONS:
        return jsonify({"error": "invalid_file_type", "message": "Chỉ nhận PDF, DOC hoặc DOCX."}), 400
    stored_name = f"{uuid.uuid4().hex}{ext}"
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    file.save(upload_dir / stored_name)
    cur = get_db().execute("""
        INSERT INTO student_cvs (student_id, original_filename, stored_filename)
        VALUES (?, ?, ?)
    """, (session["user_id"], original_name, stored_name))
    get_db().commit()
    return jsonify({"message": "Đã tải CV lên.", "cv_id": cur.lastrowid, "filename": original_name}), 201


@students_bp.get("/me/cvs/<int:cv_id>")
@roles_required("student")
def get_cv(cv_id):
    """Read metadata for one CV owned by the current student."""
    row = get_db().execute("""
        SELECT id, original_filename, created_at FROM student_cvs
        WHERE id = ? AND student_id = ?
    """, (cv_id, session["user_id"])).fetchone()
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy CV."}), 404
    return jsonify(dict(row))


@students_bp.put("/me/cvs/<int:cv_id>")
@roles_required("student")
def replace_cv(cv_id):
    """Replace an existing CV file without changing its record ID."""
    db = get_db()
    row = db.execute("""
        SELECT stored_filename FROM student_cvs
        WHERE id = ? AND student_id = ?
    """, (cv_id, session["user_id"])).fetchone()
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy CV."}), 404

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "missing_file", "message": "Hãy chọn file CV mới."}), 400
    original_name = secure_filename(file.filename)
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_CV_EXTENSIONS:
        return jsonify({"error": "invalid_file_type", "message": "Chỉ nhận PDF, DOC hoặc DOCX."}), 400

    stored_name = f"{uuid.uuid4().hex}{ext}"
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    new_path = upload_dir / stored_name
    file.save(new_path)

    old_path = upload_dir / row["stored_filename"]
    try:
        db.execute("""
            UPDATE student_cvs SET original_filename = ?, stored_filename = ?
            WHERE id = ? AND student_id = ?
        """, (original_name, stored_name, cv_id, session["user_id"]))
        db.commit()
    except Exception:
        db.rollback()
        new_path.unlink(missing_ok=True)
        raise

    try:
        old_path.unlink(missing_ok=True)
    except OSError:
        current_app.logger.warning("Could not delete replaced CV file %s", old_path)
    return jsonify({"message": "Đã thay thế CV.", "cv_id": cv_id, "filename": original_name})


@students_bp.get("/me/cvs/<int:cv_id>/download")
@roles_required("student")
def download_cv(cv_id):
    row = get_db().execute("""
        SELECT original_filename, stored_filename FROM student_cvs
        WHERE id = ? AND student_id = ?
    """, (cv_id, session["user_id"])).fetchone()
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy CV."}), 404
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], row["stored_filename"],
                               as_attachment=True, download_name=row["original_filename"])


@students_bp.delete("/me/cvs/<int:cv_id>")
@roles_required("student")
def delete_cv(cv_id):
    row = get_db().execute("""
        SELECT stored_filename FROM student_cvs WHERE id = ? AND student_id = ?
    """, (cv_id, session["user_id"])).fetchone()
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy CV."}), 404
    path = Path(current_app.config["UPLOAD_FOLDER"]) / row["stored_filename"]
    get_db().execute("DELETE FROM student_cvs WHERE id = ?", (cv_id,))
    get_db().commit()
    try:
        path.unlink(missing_ok=True)
    except OSError:
        current_app.logger.warning("Could not delete CV file %s", path)
    return jsonify({"message": "Đã xóa CV."})
