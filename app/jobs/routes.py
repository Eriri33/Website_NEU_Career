from flask import Blueprint, request, jsonify
from app.database import get_db
from app.textutil import like_pattern

jobs_bp = Blueprint("jobs", __name__)


def expand_category_ids(db, ids):
    """Danh mục có 3 cấp (nhóm nghề > nghề > vị trí). Chọn cấp cha phải gồm cả tin của cấp con."""
    if not ids:
        return []
    marks = ",".join("?" for _ in ids)
    rows = db.execute(f"""
        WITH RECURSIVE tree(id) AS (
            SELECT id FROM job_categories WHERE id IN ({marks})
            UNION
            SELECT c.id FROM job_categories c JOIN tree t ON c.parent_id = t.id
        )
        SELECT id FROM tree
    """, ids).fetchall()
    return [row["id"] for row in rows]


@jobs_bp.get("")
def list_jobs():
    """Public read endpoint: list only approved jobs by active approved companies."""
    db = get_db()
    keyword = (request.args.get("q") or "").strip()
    major = (request.args.get("major") or "").strip()
    location = (request.args.get("location") or "").strip()
    job_type = (request.args.get("job_type") or "").strip()
    category_id = request.args.get("category_id", type=int)
    category_ids = [int(value) for value in (request.args.get("category_ids") or "").split(",") if value.strip().isdigit()]
    if category_id and category_id not in category_ids:
        category_ids.append(category_id)
    category_ids = expand_category_ids(db, category_ids) if category_ids else []
    category_filtered = bool(request.args.get("category_ids") or category_id)
    skills = (request.args.get("skills") or "").strip()
    saturday_policy = (request.args.get("saturday_policy") or "").strip()
    posted_within = request.args.get("posted_within", type=int)
    sort = request.args.get("sort") or "latest"
    sql = """
        SELECT j.id, j.title, j.description, j.location, j.job_type, j.major_required,
               j.skills_required, j.salary_text, j.saturday_policy, j.deadline, j.created_at, j.category_id,
               cat.name AS category_name, c.company_name
        FROM jobs j JOIN companies c ON c.id = j.company_id
        JOIN users cu ON cu.id = c.user_id
        LEFT JOIN job_categories cat ON cat.id = j.category_id
        WHERE j.status = 'approved' AND c.approval_status = 'approved' AND cu.is_active = 1
          AND (j.deadline IS NULL OR date(j.deadline) >= date('now'))
    """
    params = []
    if keyword:
        # Ô tìm kiếm ghi "Vị trí tuyển dụng, kỹ năng..." nên q phải khớp cả skills_required.
        sql += (" AND (fold(j.title) LIKE ? ESCAPE '\\' OR fold(j.description) LIKE ? ESCAPE '\\'"
                " OR fold(c.company_name) LIKE ? ESCAPE '\\' OR fold(j.skills_required) LIKE ? ESCAPE '\\'"
                " OR fold(cat.name) LIKE ? ESCAPE '\\')")  # "Từ khóa phổ biến" lấy từ tên danh mục
        params.extend([like_pattern(keyword)] * 5)
    if major:
        sql += " AND (j.major_required = '' OR fold(j.major_required) LIKE ? ESCAPE '\\')"
        params.append(like_pattern(major))
    if location:
        sql += " AND fold(j.location) LIKE ? ESCAPE '\\'"
        params.append(like_pattern(location))
    if job_type:
        sql += " AND j.job_type = ?"
        params.append(job_type)
    if category_filtered and not category_ids:
        sql += " AND 1 = 0"  # category_ids không tồn tại -> không có kết quả, không được bỏ lọc
    elif category_ids:
        sql += " AND j.category_id IN (" + ",".join("?" for _ in category_ids) + ")"
        params.extend(category_ids)
    if skills:
        sql += " AND (fold(j.skills_required) LIKE ? ESCAPE '\\' OR fold(j.description) LIKE ? ESCAPE '\\')"
        params.extend([like_pattern(skills)] * 2)
    if saturday_policy in {"off", "working", "negotiable", "unknown"}:
        sql += " AND j.saturday_policy = ?"
        params.append(saturday_policy)
    if posted_within in {1, 3, 7, 30}:
        sql += " AND datetime(j.created_at) >= datetime('now', ?)"
        params.append(f"-{posted_within} days")
    order_by = {"deadline": "j.deadline IS NULL, j.deadline ASC", "latest": "j.created_at DESC"}.get(sort, "j.created_at DESC")
    sql += " ORDER BY " + order_by
    rows = db.execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows])


@jobs_bp.get("/categories")
def list_categories():
    """Danh mục đang bật + số tin công khai hợp lệ (đã duyệt, chưa hết hạn, gồm cả danh mục con)."""
    rows = get_db().execute("""
        WITH RECURSIVE tree(root_id, id) AS (
            SELECT id, id FROM job_categories WHERE is_active = 1
            UNION
            SELECT t.root_id, c.id FROM job_categories c JOIN tree t ON c.parent_id = t.id
        )
        SELECT cat.id, cat.parent_id, cat.level, cat.name, cat.description,
               COUNT(DISTINCT CASE WHEN c.id IS NOT NULL AND u.id IS NOT NULL THEN j.id END) AS job_count
        FROM job_categories cat
        LEFT JOIN tree t ON t.root_id = cat.id
        LEFT JOIN jobs j ON j.category_id = t.id AND j.status = 'approved'
                        AND (j.deadline IS NULL OR date(j.deadline) >= date('now'))
        LEFT JOIN companies c ON c.id = j.company_id AND c.approval_status = 'approved'
        LEFT JOIN users u ON u.id = c.user_id AND u.is_active = 1
        WHERE cat.is_active = 1 GROUP BY cat.id ORDER BY job_count DESC, cat.name
    """).fetchall()
    return jsonify([dict(row) for row in rows])


@jobs_bp.get("/suggestions")
def suggestions():
    rows = get_db().execute("""
        SELECT j.id, j.title, j.location, j.job_type, j.salary_text, c.company_name
        FROM jobs j JOIN companies c ON c.id = j.company_id JOIN users u ON u.id = c.user_id
        WHERE j.status = 'approved' AND c.approval_status = 'approved' AND u.is_active = 1
          AND (j.deadline IS NULL OR date(j.deadline) >= date('now'))
        ORDER BY j.created_at DESC LIMIT 6
    """).fetchall()
    keywords = [row["name"] for row in get_db().execute("SELECT name FROM job_categories WHERE is_active = 1 ORDER BY name LIMIT 8").fetchall()]
    stats = get_db().execute("""
        SELECT COUNT(*) AS total_jobs, COUNT(DISTINCT c.id) AS total_companies
        FROM jobs j JOIN companies c ON c.id = j.company_id JOIN users u ON u.id = c.user_id
        WHERE j.status = 'approved' AND c.approval_status = 'approved' AND u.is_active = 1
          AND (j.deadline IS NULL OR date(j.deadline) >= date('now'))
    """).fetchone()
    return jsonify({"keywords": keywords, "jobs": [dict(row) for row in rows], "stats": dict(stats)})


@jobs_bp.get("/<int:job_id>")
def job_detail(job_id):
    row = get_db().execute("""
        SELECT j.id, j.title, j.description, j.location, j.job_type, j.major_required,
               j.skills_required, j.salary_text, j.saturday_policy, j.deadline, j.created_at, j.category_id,
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
