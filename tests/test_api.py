import os
import tempfile
import unittest
from io import BytesIO
from werkzeug.security import generate_password_hash
from app import create_app
from app.database import get_db, init_db


class CareerConnectAPITestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        self.upload_path = os.path.join(self.tmp.name, "uploads")
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": self.db_path,
            "UPLOAD_FOLDER": self.upload_path,
            "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()
            db = get_db()
            db.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, 'admin')",
                       ("admin@example.com", generate_password_hash("admin123")))
            db.commit()

    def tearDown(self):
        self.tmp.cleanup()

    def register(self, email, role):
        return self.client.post("/api/auth/register", json={
            "email": email, "password": "secret123", "role": role
        })

    def login(self, email, password="secret123"):
        return self.client.post("/api/auth/login", json={"email": email, "password": password})

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

    def test_student_profile_and_application_flow(self):
        self.assertEqual(self.register("student@example.com", "student").status_code, 201)
        self.login("student@example.com")
        response = self.client.put("/api/students/me", json={
            "full_name": "Test Student", "major": "IT", "skills": "Python, SQL"
        })
        self.assertEqual(response.status_code, 200)
        profile = self.client.get("/api/students/me")
        self.assertEqual(profile.json["full_name"], "Test Student")

        self.client.post("/api/auth/logout")
        self.assertEqual(self.register("company@example.com", "business").status_code, 201)
        self.login("company@example.com")
        self.assertEqual(self.client.put("/api/company/profile", json={
            "company_name": "Test Company", "description": "Test", "website": ""
        }).status_code, 200)
        # Business profile edit resets approval to pending, so cannot create a job yet.
        denied = self.client.post("/api/company/jobs", json={"title": "Dev", "description": "Work"})
        self.assertEqual(denied.status_code, 403)

        self.client.post("/api/auth/logout")
        self.login("admin@example.com", "admin123")
        companies = self.client.get("/api/admin/pending/companies").json
        company_id = companies[0]["id"]
        self.assertEqual(self.client.post(f"/api/admin/companies/{company_id}/review", json={
            "decision": "approved", "note": "Valid"
        }).status_code, 200)
        self.client.post("/api/auth/logout")

        self.login("company@example.com")
        created = self.client.post("/api/company/jobs", json={
            "title": "Python Intern", "description": "Internship", "major_required": "IT",
            "skills_required": "Python, SQL", "job_type": "internship"
        })
        self.assertEqual(created.status_code, 201)
        job_id = created.json["job_id"]
        self.client.post("/api/auth/logout")
        self.login("admin@example.com", "admin123")
        approved = self.client.post(f"/api/admin/jobs/{job_id}/review", json={"decision": "approved"})
        self.assertEqual(approved.status_code, 200)
        self.client.post("/api/auth/logout")
        self.login("student@example.com")
        applied = self.client.post(f"/api/applications/jobs/{job_id}", json={"cover_letter": "Hello"})
        self.assertEqual(applied.status_code, 201)
        duplicate = self.client.post(f"/api/applications/jobs/{job_id}", json={"cover_letter": "Again"})
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(self.client.get("/api/applications/me").status_code, 200)

    def test_student_cv_crud_and_ownership(self):
        self.assertEqual(self.register("cvstudent@example.com", "student").status_code, 201)
        self.login("cvstudent@example.com")

        created = self.client.post(
            "/api/students/me/cvs",
            data={"file": (BytesIO(b"fake pdf bytes"), "resume.pdf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(created.status_code, 201)
        cv_id = created.json["cv_id"]

        detail = self.client.get(f"/api/students/me/cvs/{cv_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json["original_filename"], "resume.pdf")

        replaced = self.client.put(
            f"/api/students/me/cvs/{cv_id}",
            data={"file": (BytesIO(b"updated cv bytes"), "resume.docx")},
            content_type="multipart/form-data",
        )
        self.assertEqual(replaced.status_code, 200)
        self.assertEqual(self.client.get(f"/api/students/me/cvs/{cv_id}").json["original_filename"],
                         "resume.docx")

        self.client.post("/api/auth/logout")
        self.register("otherstudent@example.com", "student")
        self.login("otherstudent@example.com")
        self.assertEqual(self.client.get(f"/api/students/me/cvs/{cv_id}").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/students/me/cvs/{cv_id}").status_code, 404)

        self.client.post("/api/auth/logout")
        self.login("cvstudent@example.com")
        self.assertEqual(self.client.delete(f"/api/students/me/cvs/{cv_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/students/me/cvs/{cv_id}").status_code, 404)

    def test_student_cannot_use_admin_endpoint(self):
        self.register("student@example.com", "student")
        self.login("student@example.com")
        response = self.client.get("/api/admin/users")
        self.assertEqual(response.status_code, 403)

    def test_staff_dashboard_summary_requires_staff_and_returns_real_counts(self):
        # Anonymous users cannot read staff dashboard data.
        anonymous = self.client.get("/api/admin/dashboard/summary")
        self.assertEqual(anonymous.status_code, 401)

        # A student account cannot read staff dashboard data.
        self.assertEqual(self.register("dashboard-student@example.com", "student").status_code, 201)
        self.login("dashboard-student@example.com")
        forbidden = self.client.get("/api/admin/dashboard/summary")
        self.assertEqual(forbidden.status_code, 403)

        # Admin can read aggregate metrics from the test database.
        self.client.post("/api/auth/logout")
        self.login("admin@example.com", "admin123")
        response = self.client.get("/api/admin/dashboard/summary")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["role"], "admin")
        self.assertEqual(payload["stats"]["active_users"], 2)
        self.assertEqual(payload["stats"]["active_students"], 1)
        self.assertEqual(payload["stats"]["companies_pending"], 0)
        self.assertEqual(payload["stats"]["jobs_pending"], 0)
        self.assertEqual(payload["stats"]["applications_total"], 0)
        self.assertEqual(payload["recent_reviews"], [])

    def test_job_list_is_empty_without_approved_job(self):
        self.assertEqual(self.client.get("/api/jobs").status_code, 200)
        self.assertEqual(self.client.get("/api/jobs").json, [])


if __name__ == "__main__":
    unittest.main()
