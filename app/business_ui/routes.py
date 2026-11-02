from functools import wraps
from urllib.parse import quote
from flask import Blueprint, redirect, render_template, request, session, url_for

business_ui_bp = Blueprint("business_ui", __name__)


def business_page(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "business" or "user_id" not in session:
            reason = "role" if "user_id" in session else "auth"
            target = quote(request.full_path.rstrip("?"), safe="/")
            return redirect(url_for("business_ui.login", next=target, reason=reason))
        return view(*args, **kwargs)
    return wrapped


@business_ui_bp.get("/")
def home():
    return redirect(url_for("business_ui.dashboard"))


@business_ui_bp.get("/login")
def login():
    if session.get("role") == "business":
        return redirect(url_for("business_ui.dashboard"))
    return render_template("business/login.html")


@business_ui_bp.get("/dashboard")
@business_page
def dashboard():
    return render_template("business/dashboard.html", page="dashboard")


@business_ui_bp.get("/jobs")
@business_page
def jobs():
    return render_template("business/jobs.html", page="jobs")


@business_ui_bp.get("/jobs/new")
@business_page
def job_new():
    return render_template("business/job_form.html", page="jobs", mode="create", job_id="")


@business_ui_bp.get("/jobs/<int:job_id>")
@business_page
def job_detail(job_id):
    return render_template("business/job_detail.html", page="jobs", job_id=job_id)


@business_ui_bp.get("/jobs/<int:job_id>/edit")
@business_page
def job_edit(job_id):
    return render_template("business/job_form.html", page="jobs", mode="edit", job_id=job_id)


@business_ui_bp.get("/applicants")
@business_page
def applicants():
    return render_template("business/applicants.html", page="applicants")


@business_ui_bp.get("/profile")
@business_page
def profile():
    return render_template("business/profile.html", page="profile")
