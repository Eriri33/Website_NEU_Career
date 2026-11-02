from flask import Blueprint, jsonify, request
from app.database import get_db
from app.textutil import like_pattern

locations_bp = Blueprint("locations", __name__)


@locations_bp.get("/provinces")
def list_provinces():
    q = (request.args.get("q") or "").strip()
    sql = "SELECT code, name FROM provinces"
    params = []
    if q:
        sql += " WHERE fold(name) LIKE ? ESCAPE '\\'"
        params.append(like_pattern(q))
    sql += " ORDER BY name"
    return jsonify([dict(r) for r in get_db().execute(sql, params).fetchall()])


@locations_bp.get("/provinces/<province_code>/wards")
def list_wards(province_code):
    db = get_db()
    province = db.execute("SELECT code, name FROM provinces WHERE code = ?", (province_code,)).fetchone()
    if not province:
        return jsonify({"error": "not_found", "message": "Không tìm thấy tỉnh/thành phố."}), 404
    q = (request.args.get("q") or "").strip()
    sql = "SELECT code, name, level FROM wards WHERE province_code = ?"
    params = [province_code]
    if q:
        sql += " AND fold(name) LIKE ? ESCAPE '\\'"
        params.append(like_pattern(q))
    sql += " ORDER BY name"
    return jsonify([dict(r) for r in db.execute(sql, params).fetchall()])
