from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for

admin_pages_bp = Blueprint("admin_pages", __name__)
STAFF_ROLES = {"admin", "moderator"}

def page_access(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("admin_pages.login_page"))
            if session.get("role") not in allowed_roles:
                return redirect(url_for("admin_pages.login_page"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

@admin_pages_bp.get("/login")
def login_page():
    if session.get("role") in STAFF_ROLES:
        return redirect(url_for("admin_pages.dashboard"))
    return render_template("admin/login.html")

@admin_pages_bp.get("/")
@page_access(*STAFF_ROLES)
def dashboard():
    return render_template("admin/dashboard.html")

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

@admin_pages_bp.get("/history")
@page_access(*STAFF_ROLES)
def history():
    return render_template("admin/history.html")
