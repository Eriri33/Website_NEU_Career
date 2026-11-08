from flask import Blueprint, jsonify, request, session

from app.auth.guards import login_required
from app.database import get_db

m12_support_bp = Blueprint("m12_support", __name__)
STAFF_ROLES = ("admin", "moderator")
STATUSES = {"new", "classifying", "assigned", "in_progress", "waiting_requester", "resolved", "closed"}
PRIORITIES = {"low", "normal", "high"}
MAX_BODY = 5000


def _error(code, message, status):
    return jsonify({"error": code, "message": message}), status


def _valid_text(data, field, required=True, maximum=255):
    value = data.get(field, "")
    if not isinstance(value, str):
        return None
    value = value.strip()
    if (required and not value) or len(value) > maximum:
        return None
    return value


def _visible_ticket(db, ticket_id):
    return db.execute("""
        SELECT t.* FROM support_tickets t
        WHERE t.id = ? AND (t.requester_id = ? OR ? IN ('admin', 'moderator'))
    """, (ticket_id, session["user_id"], session.get("role"))).fetchone()


@m12_support_bp.route("/tickets", methods=["GET", "POST"])
@login_required
def tickets():
    db = get_db()
    if request.method == "GET":
        if session.get("role") in STAFF_ROLES:
            rows = db.execute("""
                SELECT id, requester_id, category, subject, assigned_unit, assigned_to,
                       priority, status, created_at, updated_at
                FROM support_tickets ORDER BY updated_at DESC
            """).fetchall()
        else:
            rows = db.execute("""
                SELECT id, requester_id, category, subject, assigned_unit, assigned_to,
                       priority, status, created_at, updated_at
                FROM support_tickets WHERE requester_id = ? ORDER BY updated_at DESC
            """, (session["user_id"],)).fetchall()
        return jsonify([dict(row) for row in rows])

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("invalid_input", "Body phải là một đối tượng JSON.", 400)
    fields = {
        "category": (100, True),
        "subject": (255, True),
        "description": (MAX_BODY, True),
    }
    values = {}
    for name, (maximum, required) in fields.items():
        value = _valid_text(data, name, required, maximum)
        if value is None:
            return _error("invalid_input", f"{name} không hợp lệ.", 400)
        values[name] = value
    cursor = db.execute("""
        INSERT INTO support_tickets (requester_id, category, subject, description)
        VALUES (?, ?, ?, ?)
    """, (session["user_id"], values["category"], values["subject"], values["description"]))
    ticket_id = cursor.lastrowid
    db.execute("""
        INSERT INTO support_ticket_events (ticket_id, actor_id, event_type, detail)
        VALUES (?, ?, 'created', 'Yêu cầu được tiếp nhận.')
    """, (ticket_id, session["user_id"]))
    db.commit()
    return jsonify({"message": "Đã tiếp nhận yêu cầu hỗ trợ.", "ticket_id": ticket_id}), 201


@m12_support_bp.get("/tickets/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    db = get_db()
    ticket = _visible_ticket(db, ticket_id)
    if not ticket:
        return _error("not_found", "Không tìm thấy yêu cầu hỗ trợ.", 404)
    messages = db.execute("""
        SELECT m.id, m.sender_id, u.email AS sender_email, m.body, m.created_at
        FROM support_messages m JOIN users u ON u.id = m.sender_id
        WHERE m.ticket_id = ? ORDER BY m.created_at, m.id
    """, (ticket_id,)).fetchall()
    events = db.execute("""
        SELECT e.id, e.actor_id, e.event_type, e.detail, e.created_at
        FROM support_ticket_events e WHERE e.ticket_id = ? ORDER BY e.created_at, e.id
    """, (ticket_id,)).fetchall()
    result = dict(ticket)
    result["messages"] = [dict(row) for row in messages]
    result["history"] = [dict(row) for row in events]
    return jsonify(result)


@m12_support_bp.post("/tickets/<int:ticket_id>/messages")
@login_required
def add_message(ticket_id):
    db = get_db()
    if not _visible_ticket(db, ticket_id):
        return _error("not_found", "Không tìm thấy yêu cầu hỗ trợ.", 404)
    data = request.get_json(silent=True)
    body = _valid_text(data, "body", True, MAX_BODY) if isinstance(data, dict) else None
    if body is None:
        return _error("invalid_input", "Nội dung trao đổi không hợp lệ.", 400)
    cursor = db.execute("""
        INSERT INTO support_messages (ticket_id, sender_id, body) VALUES (?, ?, ?)
    """, (ticket_id, session["user_id"], body))
    db.execute("UPDATE support_tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (ticket_id,))
    db.execute("""
        INSERT INTO support_ticket_events (ticket_id, actor_id, event_type, detail)
        VALUES (?, ?, 'message', 'Đã thêm trao đổi.')
    """, (ticket_id, session["user_id"]))
    db.commit()
    return jsonify({"message": "Đã ghi nhận trao đổi.", "message_id": cursor.lastrowid}), 201


@m12_support_bp.patch("/tickets/<int:ticket_id>")
@login_required
def update_ticket(ticket_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("invalid_input", "Body phải là một đối tượng JSON.", 400)
    db = get_db()
    ticket = db.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        return _error("not_found", "Không tìm thấy yêu cầu hỗ trợ.", 404)
    is_staff = session.get("role") in STAFF_ROLES
    if not is_staff and ticket["requester_id"] != session["user_id"]:
        return _error("not_found", "Không tìm thấy yêu cầu hỗ trợ.", 404)
    allowed = {"status", "priority", "assigned_unit", "assigned_to"}
    if not data or set(data) - allowed:
        return _error("invalid_input", "Chỉ được cập nhật status, priority, assigned_unit hoặc assigned_to.", 400)
    changes = {}
    if "status" in data:
        status = data["status"]
        can_reopen = not is_staff and ticket["status"] in {"resolved", "closed"} and status == "new"
        if not isinstance(status, str) or status not in STATUSES or (not is_staff and not can_reopen):
            return _error("invalid_input", "Trạng thái yêu cầu không hợp lệ.", 400)
        changes["status"] = status
    if not is_staff and set(data) != {"status"}:
        return _error("forbidden", "Người gửi chỉ có thể mở lại yêu cầu đã hoàn tất.", 403)
    if "priority" in data:
        priority = data["priority"]
        if not isinstance(priority, str) or priority not in PRIORITIES:
            return _error("invalid_input", "Mức ưu tiên không hợp lệ.", 400)
        changes["priority"] = priority
    if "assigned_unit" in data:
        unit = _valid_text(data, "assigned_unit", False, 255)
        if unit is None:
            return _error("invalid_input", "Đơn vị xử lý không hợp lệ.", 400)
        changes["assigned_unit"] = unit
    if "assigned_to" in data:
        assigned_to = data["assigned_to"]
        if assigned_to is not None and (not isinstance(assigned_to, int) or isinstance(assigned_to, bool)):
            return _error("invalid_input", "assigned_to phải là mã tài khoản hoặc null.", 400)
        if assigned_to is not None:
            assignee = db.execute("""
                SELECT id FROM users WHERE id = ? AND role IN ('admin', 'moderator') AND is_active = 1
            """, (assigned_to,)).fetchone()
            if not assignee:
                return _error("invalid_assignee", "Người xử lý không hợp lệ.", 400)
        changes["assigned_to"] = assigned_to
    assignments = ", ".join(f"{key} = ?" for key in changes)
    db.execute(
        f"UPDATE support_tickets SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (*changes.values(), ticket_id),
    )
    for field, value in changes.items():
        old_value = ticket[field]
        if old_value != value:
            db.execute("""
                INSERT INTO support_ticket_events (ticket_id, actor_id, event_type, detail)
                VALUES (?, ?, ?, ?)
            """, (ticket_id, session["user_id"], field, f"{old_value or ''} -> {value or ''}"))
    db.commit()
    return jsonify({"message": "Đã cập nhật yêu cầu hỗ trợ."})
