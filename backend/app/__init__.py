from pathlib import Path
from flask import Flask, jsonify, redirect, render_template, session, url_for
from backend.config import Config
from app.database import init_app, init_db_command


def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder=Config.TEMPLATE_FOLDER,
        static_folder=Config.STATIC_FOLDER,
        static_url_path="/static",
    )
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    init_app(app)
    app.cli.add_command(init_db_command)

    if Path(app.config["DATABASE"]).exists():
        from app.database import get_db, migrate_db
        with app.app_context():
            migrate_db(get_db())

    from app.auth.routes import auth_bp
    from app.students.routes import students_bp
    from app.modules.m03_students.routes import m03_students_bp
    from app.modules.m12_support.routes import m12_support_bp
    from app.modules.m13_partners.routes import m13_partners_bp
    from app.companies.routes import companies_bp
    from app.jobs.routes import jobs_bp
    from app.applications.routes import applications_bp
    from app.admin.routes import admin_bp
    from app.admin.pages import admin_pages_bp
    from app.career.routes import career_bp
    from app.locations.routes import locations_bp
    from app.categories.routes import categories_bp
    from app.business_ui.routes import business_ui_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(m03_students_bp, url_prefix="/api/students")
    app.register_blueprint(m12_support_bp, url_prefix="/api/support")
    app.register_blueprint(m13_partners_bp, url_prefix="/api/partners")
    app.register_blueprint(companies_bp, url_prefix="/api/company")
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(applications_bp, url_prefix="/api/applications")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_pages_bp, url_prefix="/admin")
    app.register_blueprint(career_bp, url_prefix="/api/career-contents")
    app.register_blueprint(locations_bp, url_prefix="/api/locations")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(business_ui_bp, url_prefix="/business")
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/jobs")
    def jobs_page():
        return render_template("jobs.html")

    @app.get("/blog")
    def blog_page():
        return render_template("blog.html")

    @app.get("/login")
    def login_page():
        return render_template("auth.html", mode="login")

    @app.get("/register")
    def register_page():
        return render_template("auth.html", mode="register")

    @app.get("/dashboard")
    def dashboard():
        if not session.get("user_id"):
            return redirect(url_for("login_page"))

        role = session.get("role")

        if role == "business":
            return redirect(url_for("business_ui.dashboard"))

        if role in {"admin", "moderator"}:
            return redirect(url_for("admin_pages.dashboard"))

        if role != "student":
            return redirect(url_for("login_page"))

        return render_template("dashboard.html", role=role)

    @app.get("/student/profile")
    def student_profile_page():
        if not session.get("user_id"):
            return redirect(url_for("login_page", next="/student/profile"))

        if session.get("role") != "student":
            if session.get("role") == "business":
                return redirect(url_for("business_ui.dashboard"))

            if session.get("role") in {"admin", "moderator"}:
                return redirect(url_for("admin_pages.dashboard"))

            return redirect(url_for("login_page"))

        return render_template("student/profile.html")

    @app.get("/companies/<int:company_id>")
    def public_company_page(company_id):
        return render_template("company_public.html", company_id=company_id)
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "Career Connect API is running"})

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "not_found", "message": "Không tìm thấy đường dẫn."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "method_not_allowed", "message": "Phương thức HTTP không được hỗ trợ."}), 405

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"error": "file_too_large", "message": "Dữ liệu tải lên vượt quá giới hạn cho phép."}), 413

    return app
