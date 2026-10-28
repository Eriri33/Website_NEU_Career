from flask import Blueprint, request, jsonify
from app.database import get_db
from app.auth.guards import roles_required

career_bp = Blueprint("career", __name__)


@career_bp.get("")
def list_published_content():
    rows = get_db().execute("""
        SELECT id, title, summary, category, created_at, updated_at
        FROM career_contents WHERE status = 'published' ORDER BY created_at DESC
    """).fetchall()
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
