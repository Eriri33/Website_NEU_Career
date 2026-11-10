from flask import Blueprint, jsonify, request, session

from app.auth.guards import roles_required
from app.database import get_db
from app.textutil import fold_text

m13_partners_bp = Blueprint("m13_partners", __name__)
STAFF_ROLES = ("admin", "moderator")


def _error(code, message, status):
    return jsonify({"error": code, "message": message}), status


def _text(data, field, required=False, maximum=255):
    value = data.get(field, "")
    if not isinstance(value, str):
        return None
    value = value.strip()
    if (required and not value) or len(value) > maximum:
        return None
    return value


@m13_partners_bp.route("", methods=["GET", "POST"])
@roles_required(*STAFF_ROLES)
def partner_collection():
    db = get_db()
    if request.method == "GET":
        query = (request.args.get("q") or "").strip()
        sql = """
            SELECT p.id, p.name, p.website, p.industry, p.source, p.verified_at, p.created_at,
                   COUNT(c.id) AS contact_count
            FROM partners p LEFT JOIN partner_contacts c ON c.partner_id = p.id
        """
        params = ()
        if query:
            pattern = f"%{fold_text(query)}%"
            sql += " WHERE fold(p.name) LIKE ? OR fold(p.website) LIKE ? OR fold(p.industry) LIKE ?"
            params = (pattern, pattern, pattern)
        sql += " GROUP BY p.id ORDER BY p.name COLLATE NOCASE"
        return jsonify([dict(row) for row in db.execute(sql, params).fetchall()])

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("invalid_input", "Body phải là một đối tượng JSON.", 400)
    values = {}
    for field, required, maximum in (
        ("name", True, 255), ("website", False, 255), ("industry", False, 255),
        ("source", True, 255),
    ):
        value = _text(data, field, required, maximum)
        if value is None:
            return _error("invalid_input", f"{field} không hợp lệ.", 400)
        values[field] = value
    duplicate = db.execute("""
        SELECT id, name FROM partners
        WHERE fold(name) = ? OR (? <> '' AND fold(website) = ?)
        LIMIT 1
    """, (fold_text(values["name"]), fold_text(values["website"]),
          fold_text(values["website"]))).fetchone()
    if duplicate:
        return jsonify({
            "error": "possible_duplicate",
            "message": "Đã có đối tác trùng tên hoặc website; hãy kiểm tra trước khi tạo.",
            "partner_id": duplicate["id"],
            "name": duplicate["name"],
        }), 409
    cursor = db.execute("""
        INSERT INTO partners (name, website, industry, source, created_by)
        VALUES (?, ?, ?, ?, ?)
    """, (values["name"], values["website"], values["industry"], values["source"],
          session["user_id"]))
    db.commit()
    return jsonify({"message": "Đã tạo hồ sơ đối tác.", "partner_id": cursor.lastrowid}), 201


@m13_partners_bp.get("/<int:partner_id>")
@roles_required(*STAFF_ROLES)
def partner_detail(partner_id):
    db = get_db()
    partner = db.execute("SELECT * FROM partners WHERE id = ?", (partner_id,)).fetchone()
    if not partner:
        return _error("not_found", "Không tìm thấy doanh nghiệp đối tác.", 404)
    contacts = db.execute("""
        SELECT id, full_name, job_title, email, phone, source, verified_at
        FROM partner_contacts WHERE partner_id = ? ORDER BY full_name COLLATE NOCASE
    """, (partner_id,)).fetchall()
    result = dict(partner)
    result.pop("created_by", None)
    result["contacts"] = [dict(row) for row in contacts]
    return jsonify(result)


@m13_partners_bp.patch("/<int:partner_id>")
@roles_required(*STAFF_ROLES)
def update_partner(partner_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data or set(data) - {"name", "website", "industry", "source"}:
        return _error("invalid_input", "Body chỉ nhận name, website, industry, source.", 400)
    db = get_db()
    partner = db.execute("SELECT id FROM partners WHERE id = ?", (partner_id,)).fetchone()
    if not partner:
        return _error("not_found", "Không tìm thấy doanh nghiệp đối tác.", 404)
    limits = {"name": (True, 255), "website": (False, 255), "industry": (False, 255), "source": (True, 255)}
    changes = {}
    for field, raw in data.items():
        value = _text(data, field, *limits[field])
        if value is None:
            return _error("invalid_input", f"{field} không hợp lệ.", 400)
        changes[field] = value
    if "name" in changes or "website" in changes:
        duplicate = db.execute("""
            SELECT id FROM partners
            WHERE id <> ? AND (fold(name) = ? OR (? <> '' AND fold(website) = ?))
            LIMIT 1
        """, (partner_id, fold_text(changes.get("name", "")), fold_text(changes.get("website", "")),
              fold_text(changes.get("website", "")))).fetchone()
        if duplicate:
            return _error("possible_duplicate", f"Thông tin trùng với đối tác {duplicate['id']}.", 409)
    assignments = ", ".join(f"{field} = ?" for field in changes)
    verification_reset = ", verified_at = NULL, verified_by = NULL" if {
        "name", "website"
    } & changes.keys() else ""
    db.execute(
        f"UPDATE partners SET {assignments}{verification_reset}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (*changes.values(), partner_id),
    )
    db.commit()
    return jsonify({"message": "Đã cập nhật doanh nghiệp đối tác."})


@m13_partners_bp.post("/<int:partner_id>/contacts")
@roles_required(*STAFF_ROLES)
def add_contact(partner_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("invalid_input", "Body phải là một đối tượng JSON.", 400)
    db = get_db()
    if not db.execute("SELECT 1 FROM partners WHERE id = ?", (partner_id,)).fetchone():
        return _error("not_found", "Không tìm thấy doanh nghiệp đối tác.", 404)
    values = {}
    for field, required, limit in (
        ("full_name", True, 255), ("job_title", False, 255), ("email", False, 255),
        ("phone", False, 80), ("source", True, 255),
    ):
        value = _text(data, field, required, limit)
        if value is None:
            return _error("invalid_input", f"{field} không hợp lệ.", 400)
        values[field] = value
    cursor = db.execute("""
        INSERT INTO partner_contacts (partner_id, full_name, job_title, email, phone, source, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (partner_id, values["full_name"], values["job_title"], values["email"],
          values["phone"], values["source"], session["user_id"]))
    db.commit()
    return jsonify({"message": "Đã thêm đầu mối liên hệ.", "contact_id": cursor.lastrowid}), 201


@m13_partners_bp.post("/<int:partner_id>/verify")
@roles_required(*STAFF_ROLES)
def verify_partner(partner_id):
    db = get_db()
    cursor = db.execute("""
        UPDATE partners SET verified_at = CURRENT_TIMESTAMP, verified_by = ?,
            updated_at = CURRENT_TIMESTAMP WHERE id = ?
    """, (session["user_id"], partner_id))
    if cursor.rowcount == 0:
        return _error("not_found", "Không tìm thấy doanh nghiệp đối tác.", 404)
    db.commit()
    return jsonify({"message": "Đã xác nhận thông tin đối tác."})


@m13_partners_bp.patch("/contacts/<int:contact_id>")
@roles_required(*STAFF_ROLES)
def update_contact(contact_id):
    data = request.get_json(silent=True)
    allowed = {"full_name", "job_title", "email", "phone", "source"}
    if not isinstance(data, dict) or not data or set(data) - allowed:
        return _error("invalid_input", "Body chỉ nhận full_name, job_title, email, phone, source.", 400)
    db = get_db()
    if not db.execute("SELECT 1 FROM partner_contacts WHERE id = ?", (contact_id,)).fetchone():
        return _error("not_found", "Không tìm thấy đầu mối liên hệ.", 404)
    limits = {
        "full_name": (True, 255), "job_title": (False, 255), "email": (False, 255),
        "phone": (False, 80), "source": (True, 255),
    }
    changes = {}
    for field in data:
        value = _text(data, field, *limits[field])
        if value is None:
            return _error("invalid_input", f"{field} không hợp lệ.", 400)
        changes[field] = value
    assignments = ", ".join(f"{field} = ?" for field in changes)
    db.execute(
        f"UPDATE partner_contacts SET {assignments}, verified_at = NULL WHERE id = ?",
        (*changes.values(), contact_id),
    )
    db.commit()
    return jsonify({"message": "Đã cập nhật đầu mối liên hệ."})


@m13_partners_bp.post("/contacts/<int:contact_id>/verify")
@roles_required(*STAFF_ROLES)
def verify_contact(contact_id):
    db = get_db()
    cursor = db.execute("""
        UPDATE partner_contacts SET verified_at = CURRENT_TIMESTAMP WHERE id = ?
    """, (contact_id,))
    if cursor.rowcount == 0:
        return _error("not_found", "Không tìm thấy đầu mối liên hệ.", 404)
    db.commit()
    return jsonify({"message": "Đã xác nhận thông tin đầu mối liên hệ."})
