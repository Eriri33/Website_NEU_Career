from flask import Blueprint, request, jsonify
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

    rows = get_db().execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows])


def get_wards_by_province(province_code):
    db = get_db()

    province = db.execute(
        "SELECT code, name FROM provinces WHERE code = ?",
        (province_code,)
    ).fetchone()

    if not province:
        return None, jsonify({
            "error": "province_not_found",
            "message": "Không tìm thấy tỉnh/thành phố."
        }), 404

    q = (request.args.get("q") or "").strip()

    sql = """
        SELECT code, name, level, province_code
        FROM wards
        WHERE province_code = ?
    """
    params = [province_code]

    if q:
        sql += " AND fold(name) LIKE ? ESCAPE '\\'"
        params.append(like_pattern(q))

    sql += " ORDER BY name"

    rows = db.execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows]), None, None


@locations_bp.get("/wards")
def get_wards():
    province_code = (request.args.get("province_code") or "").strip()

    if not province_code:
        return jsonify({
            "error": "missing_province_code",
            "message": "Vui lòng cung cấp mã tỉnh/thành phố."
        }), 400

    result, error, status = get_wards_by_province(province_code)

    if error:
        return error, status

    return result


@locations_bp.get("/provinces/<province_code>/wards")
def list_wards(province_code):
    result, error, status = get_wards_by_province(province_code)

    if error:
        return error, status

    return result