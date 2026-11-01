
from flask import Blueprint, request, jsonify
from app.database import get_db

locations_bp = Blueprint("locations", __name__)


@locations_bp.get("/provinces")
def get_provinces():
    """Get all provinces and centrally governed cities."""
    db = get_db()

    rows = db.execute("""
        SELECT code, name
        FROM provinces
        ORDER BY name
    """).fetchall()

    return jsonify([dict(row) for row in rows])


@locations_bp.get("/wards")
def get_wards():
    """Get wards belonging to a selected province."""
    province_code = (request.args.get("province_code") or "").strip()

    if not province_code:
        return jsonify({
            "error": "missing_province_code",
            "message": "Vui lòng cung cấp mã tỉnh/thành phố."
        }), 400

    db = get_db()

    province = db.execute("""
        SELECT code, name
        FROM provinces
        WHERE code = ?
    """, (province_code,)).fetchone()

    if not province:
        return jsonify({
            "error": "province_not_found",
            "message": "Không tìm thấy tỉnh/thành phố."
        }), 404

    rows = db.execute("""
        SELECT code, name, level, province_code
        FROM wards
        WHERE province_code = ?
        ORDER BY name
    """, (province_code,)).fetchall()

    return jsonify([dict(row) for row in rows])
