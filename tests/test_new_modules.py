import os
import tempfile
import unittest
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import create_app
from app.database import get_db, init_db


class ModuleTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": os.path.join(self.tmp.name, "test.db"),
            "UPLOAD_FOLDER": os.path.join(self.tmp.name, "uploads"),
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()
            db = get_db()
            db.executemany(
                "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                [
                    ("admin@example.com", generate_password_hash("secret123"), "admin"),
                    ("student@example.com", generate_password_hash("secret123"), "student"),
                    ("other@example.com", generate_password_hash("secret123"), "student"),
                ],
            )
            db.executemany(
                "INSERT INTO student_profiles (user_id, full_name) VALUES (?, ?)",
                [(2, "Student A"), (3, "Student B")],
            )
            db.commit()
        self.ids = {"admin": 1, "student": 2, "other": 3}

    def tearDown(self):
        self.tmp.cleanup()

    def login(self, email):
        response = self.client.post(
            "/api/auth/login", json={"email": email, "password": "secret123"}
        )
        self.assertEqual(response.status_code, 200, response.json)

    def test_frontend_is_served_from_separate_directory(self):
        self.assertEqual(Path(self.app.template_folder).parent.name, "frontend")
        self.assertEqual(Path(self.app.static_folder).parent.name, "frontend")
        self.assertEqual(self.client.get("/").status_code, 200)
        static_response = self.client.get("/static/js/app.js")
        self.assertEqual(static_response.status_code, 200)
        static_response.close()

    def test_student_intake_status_history_and_system_links(self):
        self.login("student@example.com")
        denied = self.client.post("/api/students/intakes", json={})
        self.assertEqual(denied.status_code, 403)
        self.client.post("/api/auth/logout")
        self.login("admin@example.com")

        payload = {
            "student_user_id": self.ids["student"],
            "student_code": "NEU-2026-001",
            "program_code": "IT",
            "program_name": "Information Technology",
            "cohort": "K68",
            "source_system": "Admissions",
            "reason": "Verified accepted-student handoff",
            "effective_from": "2026-09-01",
        }
        created = self.client.post("/api/students/intakes", json=payload)
        self.assertEqual(created.status_code, 201, created.json)
        duplicate = self.client.post("/api/students/intakes", json=payload)
        self.assertEqual(duplicate.status_code, 409)

        enrollment_id = created.json["enrollment_id"]
        second_program = dict(payload)
        second_program.update({
            "program_code": "BUSINESS",
            "program_name": "Business Administration",
            "cohort": "K68-2",
        })
        self.assertEqual(self.client.post("/api/students/intakes", json=second_program).status_code, 201)
        reused_code = dict(payload, student_user_id=self.ids["other"])
        self.assertEqual(self.client.post("/api/students/intakes", json=reused_code).status_code, 409)

        changed = self.client.patch(
            f"/api/students/enrollments/{enrollment_id}/status",
            json={"status": "leave", "reason": "Approved leave"},
        )
        self.assertEqual(changed.status_code, 200, changed.json)
        record = self.client.get(f"/api/students/records/{self.ids['student']}")
        self.assertEqual(record.status_code, 200)
        self.assertEqual(record.json["identifiers"][0]["identifier_value"], "NEU-2026-001")
        status_by_id = {row["id"]: row["status"] for row in record.json["enrollments"]}
        self.assertEqual(status_by_id[enrollment_id], "leave")
        enrollment_by_id = {row["id"]: row for row in record.json["enrollments"]}
        self.assertEqual(enrollment_by_id[enrollment_id]["effective_from"], "2026-09-01")

        link = self.client.post(
            f"/api/students/records/{self.ids['student']}/system-links",
            json={
                "link_type": "academic_results",
                "system_key": "sis",
                "external_id": "transcript-42",
            },
        )
        self.assertEqual(link.status_code, 201, link.json)
        self.assertEqual(
            self.client.get(f"/api/students/records/{self.ids['student']}").json
            ["system_links"][0]["external_id"],
            "transcript-42",
        )

    def test_support_tickets_are_private_and_reopenable(self):
        self.login("student@example.com")
        created = self.client.post("/api/support/tickets", json={
            "category": "Academic",
            "subject": "Course registration",
            "description": "Please help with a course registration issue.",
        })
        self.assertEqual(created.status_code, 201, created.json)
        ticket_id = created.json["ticket_id"]

        self.client.post("/api/auth/logout")
        self.login("other@example.com")
        self.assertEqual(self.client.get(f"/api/support/tickets/{ticket_id}").status_code, 404)

        self.client.post("/api/auth/logout")
        self.login("admin@example.com")
        assigned = self.client.patch(f"/api/support/tickets/{ticket_id}", json={
            "status": "resolved", "assigned_unit": "Student affairs", "priority": "high",
        })
        self.assertEqual(assigned.status_code, 200, assigned.json)
        detail = self.client.get(f"/api/support/tickets/{ticket_id}")
        self.assertEqual(detail.json["status"], "resolved")
        self.assertGreaterEqual(len(detail.json["history"]), 3)

        self.client.post("/api/auth/logout")
        self.login("student@example.com")
        reopened = self.client.patch(f"/api/support/tickets/{ticket_id}", json={"status": "new"})
        self.assertEqual(reopened.status_code, 200, reopened.json)
        self.assertEqual(self.client.get(f"/api/support/tickets/{ticket_id}").json["status"], "new")

    def test_partner_company_and_contact_are_separate_and_deduplicated(self):
        self.login("student@example.com")
        self.assertEqual(
            self.client.get("/api/partners").status_code, 403
        )
        self.client.post("/api/auth/logout")
        self.login("admin@example.com")
        created = self.client.post("/api/partners", json={
            "name": "Example Enterprise",
            "website": "https://example.test",
            "industry": "Technology",
            "source": "Career fair 2026",
        })
        self.assertEqual(created.status_code, 201, created.json)
        partner_id = created.json["partner_id"]
        duplicate = self.client.post("/api/partners", json={
            "name": "EXAMPLE ENTERPRISE",
            "source": "Duplicate import",
        })
        self.assertEqual(duplicate.status_code, 409)

        contact = self.client.post(f"/api/partners/{partner_id}/contacts", json={
            "full_name": "Contact Person",
            "job_title": "Recruiter",
            "email": "contact@example.test",
            "phone": "",
            "source": "Verified at event",
        })
        self.assertEqual(contact.status_code, 201, contact.json)
        detail = self.client.get(f"/api/partners/{partner_id}")
        self.assertEqual(detail.json["name"], "Example Enterprise")
        self.assertEqual(detail.json["contacts"][0]["full_name"], "Contact Person")
        verified = self.client.post(
            f"/api/partners/contacts/{contact.json['contact_id']}/verify"
        )
        self.assertEqual(verified.status_code, 200)
        self.assertIsNotNone(self.client.get(f"/api/partners/{partner_id}").json
                             ["contacts"][0]["verified_at"])
        updated = self.client.patch(
            f"/api/partners/contacts/{contact.json['contact_id']}",
            json={"email": "new@example.test"},
        )
        self.assertEqual(updated.status_code, 200, updated.json)
        self.assertIsNone(self.client.get(f"/api/partners/{partner_id}").json
                          ["contacts"][0]["verified_at"])
