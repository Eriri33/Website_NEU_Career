from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, abort
from app.database import get_db

admin_pages_bp = Blueprint("admin_pages", __name__)
STAFF_ROLES = {"admin", "moderator"}

def page_access(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login_page"))

            if session.get("role") not in allowed_roles:
                return redirect(url_for("index"))

            return view(*args, **kwargs)
        return wrapped
    return decorator


@admin_pages_bp.get("/login")
def login_page():
    if session.get("role") in STAFF_ROLES:
        return redirect(url_for("admin_pages.dashboard"))

    return redirect(url_for("login_page"))

@admin_pages_bp.get("/")
@page_access(*STAFF_ROLES)
def dashboard():
    return render_template("admin/dashboard.html")

@admin_pages_bp.get("/profile")
@page_access(*STAFF_ROLES)
def profile():
    return render_template("admin/profile.html")

@admin_pages_bp.get("/companies")
@page_access(*STAFF_ROLES)
def companies():
    return render_template("admin/companies.html")

@admin_pages_bp.get("/jobs")
@page_access(*STAFF_ROLES)
def jobs():
    return render_template("admin/jobs.html")

@admin_pages_bp.get("/users")
@page_access("admin")
def users():
    return render_template("admin/users.html")

@admin_pages_bp.get("/categories")
@page_access(*STAFF_ROLES)
def categories():
    return render_template("admin/categories.html")

@admin_pages_bp.get("/contents")
@page_access(*STAFF_ROLES)
def contents():
    return render_template("admin/contents.html")

@admin_pages_bp.get("/contents/<int:content_id>")
@page_access(*STAFF_ROLES)
def content_detail(content_id):

    row = get_db().execute(
        "SELECT * FROM career_contents WHERE id = ?",
        (content_id,)
    ).fetchone()

    if not row:
        abort(404)

    return render_template(
        "admin/content_detail.html",
        content=dict(row)
    )

@admin_pages_bp.get("/history")
@page_access(*STAFF_ROLES)
def history():
    return render_template("admin/history.html")

@admin_pages_bp.get("/jobs/<int:job_id>")
@page_access(*STAFF_ROLES)
def job_detail(job_id):
    row = get_db().execute("""
        SELECT
            j.*,
            c.id AS company_id,
            c.company_name,
            c.description AS company_description,
            c.website AS company_website,
            c.approval_status AS company_status,
            cat.name AS category_name
        FROM jobs j
        JOIN companies c ON c.id = j.company_id
        LEFT JOIN job_categories cat ON cat.id = j.category_id
        WHERE j.id = ?
    """, (job_id,)).fetchone()

    if not row:
        from flask import abort
        abort(404)

    return render_template("admin/job_detail.html", job=dict(row))


@admin_pages_bp.get("/companies/<int:company_id>")
@page_access(*STAFF_ROLES)
def company_detail(company_id):
    row = get_db().execute("""
        SELECT
            c.id,
            c.company_name,
            c.description,
            c.website,
            c.approval_status,
            c.review_note,
            c.reviewed_at,
            c.created_at,
            u.is_active
        FROM companies c
        JOIN users u ON u.id = c.user_id
        WHERE c.id = ?
    """, (company_id,)).fetchone()

    if not row:
        from flask import abort
        abort(404)

    return render_template("admin/company_detail.html", company=dict(row))