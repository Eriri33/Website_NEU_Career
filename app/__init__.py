from flask import Flask, jsonify, render_template
from config import Config
from app.database import init_app, init_db_command


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    init_app(app)
    app.cli.add_command(init_db_command)

    from app.auth.routes import auth_bp
    from app.students.routes import students_bp
    from app.companies.routes import companies_bp
    from app.jobs.routes import jobs_bp
    from app.applications.routes import applications_bp
    from app.admin.routes import admin_bp
    from app.career.routes import career_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(companies_bp, url_prefix="/api/company")
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(applications_bp, url_prefix="/api/applications")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(career_bp, url_prefix="/api/career-contents")

    @app.get("/")
    def index():
        return render_template("index.html")

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
