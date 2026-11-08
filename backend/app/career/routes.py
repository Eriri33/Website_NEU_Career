from flask import Blueprint, request, jsonify
from app.database import get_db
from app.auth.guards import roles_required
from app.textutil import like_pattern

career_bp = Blueprint("career", __name__)


@career_bp.get("")
def list_published_content():
    keyword = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    sql = """
        SELECT id, title, summary, category, created_at, updated_at
        FROM career_contents WHERE status = 'published'
    """
    params = []
    if keyword:
        sql += (" AND (fold(title) LIKE ? ESCAPE '\\' OR fold(summary) LIKE ? ESCAPE '\\'"
                " OR fold(body) LIKE ? ESCAPE '\\')")
        params.extend([like_pattern(keyword)] * 3)
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY created_at DESC"
    rows = get_db().execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows])


@career_bp.get("/<int:content_id>")
def published_content_detail(content_id):
    row = get_db().execute("""
        SELECT id, title, summary, body, category, created_at, updated_at
        FROM career_contents WHERE id = ? AND status = 'published'
    """, (content_id,)).fetchone()
    if not row:
        return jsonify({"error": "not_found", "message": "Không tìm thấy bài hướng nghiệp đã xuất bản."}), 404
    return jsonify(dict(row))


# Private CRUD endpoints for admin/moderator are intentionally grouped under /api/admin.
