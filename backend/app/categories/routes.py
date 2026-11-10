
from flask import Blueprint, jsonify
from app.database import get_db


categories_bp = Blueprint("categories", __name__)


@categories_bp.get("/")
def list_public_categories():
    rows = get_db().execute("""
        SELECT id, parent_id, level, name
        FROM job_categories
        WHERE is_active = 1
        ORDER BY level, name
    """).fetchall()

    # Chuyển các dòng dữ liệu thành dictionary
    categories = {}

    for row in rows:
        categories[row["id"]] = {
            "id": row["id"],
            "name": row["name"],
            "level": row["level"],
            "children": []
        }

    # Xây dựng cây danh mục
    result = []

    for row in rows:
        category = categories[row["id"]]
        parent_id = row["parent_id"]

        if parent_id is None:
            # Danh mục cấp 1
            result.append(category)

        elif parent_id in categories:
            # Danh mục cấp 2 hoặc cấp 3
            categories[parent_id]["children"].append(category)

    return jsonify(result)
