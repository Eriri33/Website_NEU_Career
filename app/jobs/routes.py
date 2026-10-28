from flask import Blueprint, request, jsonify
from app.database import get_db

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.get("")
def list_jobs():
    """Public read endpoint: list only approved jobs by active approved companies."""
    db = get_db()
    keyword = (request.args.get("q") or "").strip()
    major = (request.args.get("major") or "").strip()
    location = (request.args.get("location") or "").strip()
    job_type = (request.args.get("job_type") or "").strip()
    category_id = request.args.get("category_id", type=int)
    sql = """
        SELECT j.id, j.title, j.description, j.location, j.job_type, j.major_required,
               j.skills_required, j.deadline, j.created_at, j.category_id,
               cat.name AS category_name, c.company_name
        FROM jobs j JOIN companies c ON c.id = j.company_id
        JOIN users cu ON cu.id = c.user_id
        LEFT JOIN job_categories cat ON cat.id = j.category_id
        WHERE j.status = 'approved' AND c.approval_status = 'approved' AND cu.is_active = 1
          AND (j.deadline IS NULL OR date(j.deadline) >= date('now'))
    """
    params = []
    if keyword:
        sql += " AND (j.title LIKE ? OR j.description LIKE ? OR c.company_name LIKE ?)"
        params.extend([f"%{keyword}%"] * 3)
    if major:
        sql += " AND (j.major_required = '' OR j.major_required LIKE ?)"
        params.append(f"%{major}%")
    if location:
        sql += " AND j.location LIKE ?"
        params.append(f"%{location}%")
    if job_type:
        sql += " AND j.job_type = ?"
        params.append(job_type)
    if category_id:
        sql += " AND j.category_id = ?"
        params.append(category_id)
    sql += " ORDER BY j.created_at DESC"
    rows = db.execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows])


@jobs_bp.get("/<int:job_id>")
def job_detail(job_id):
    row = get_db().execute("""
        SELECT j.id, j.title, j.description, j.location, j.job_type, j.major_required,
               j.skills_required, j.deadline, j.created_at, j.category_id,
               cat.name AS category_name, c.company_name, c.description AS company_description,
               c.website AS company_website
        FROM jobs j JOIN companies c ON c.id = j.company_id
        JOIN users cu ON cu.id = c.user_id
        LEFT JOIN job_categories cat ON cat.id = j.category_id
        WHERE j.id = ? AND j.status = 'approved' AND c.approval_status = 'approved'
          AND cu.is_active = 1 AND (j.deadline IS NULL OR date(j.deadline) >= date('now'))
    """, (job_id,)).fetchone()
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy tin tuyển dụng đang công khai."}), 404
    return jsonify(dict(row))
