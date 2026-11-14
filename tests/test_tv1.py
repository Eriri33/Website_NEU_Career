import unittest
import json
import sqlite3
import tempfile
from pathlib import Path
from app import create_app
from app.database import init_db


class TV1TestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.upload_dir = Path(self.temp_dir.name) / "cvs"
        self.app = create_app({
            "TESTING": True,
            "DATABASE": str(self.db_path),
            "UPLOAD_FOLDER": str(self.upload_dir),
            "SECRET_KEY": "test-key"
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()
            self._seed_test_data()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _seed_test_data(self):
        # Seed student, business, categories, jobs, career
        # Direct DB seeding for test isolation
        conn = sqlite3.connect(str(self.db_path))
        from werkzeug.security import generate_password_hash
        cur = conn.cursor()
        # Admin
        cur.execute("INSERT INTO users (email, password_hash, role) VALUES ('admin@test.com', ?, 'admin')",
                    (generate_password_hash("pass123"),))
        admin_id = cur.lastrowid
        # Student
        cur.execute("INSERT INTO users (email, password_hash, role) VALUES ('student@test.com', ?, 'student')",
                    (generate_password_hash("pass123"),))
        student_id = cur.lastrowid
        cur.execute("INSERT INTO student_profiles (user_id, full_name, major, skills) VALUES (?, 'Test Student', 'CNTT', 'Python, SQL')", (student_id,))
        # Business
        cur.execute("INSERT INTO users (email, password_hash, role) VALUES ('biz@test.com', ?, 'business')",
                    (generate_password_hash("pass123"),))
        biz_id = cur.lastrowid
        cur.execute("INSERT INTO companies (user_id, company_name, approval_status) VALUES (?, 'FPT Software', 'approved')", (biz_id,))
        comp_id = cur.lastrowid
        # Categories
        cur.execute("INSERT INTO job_categories (name) VALUES ('CNTT')")
        cat_id = cur.lastrowid
        cur.execute("INSERT INTO provinces (code, name) VALUES ('01', 'Thành phố Hà Nội')")
        cur.execute("INSERT INTO wards (code, name, level, province_code) VALUES ('00001', 'Phường Ba Đình', 'Phường', '01')")
        # Jobs (1 approved, 1 pending)
        cur.execute("""INSERT INTO jobs (company_id, category_id, title, description, location, job_type, salary_text, saturday_policy, status)
                       VALUES (?, ?, 'Python Developer', 'Desc', 'Hanoi', 'full_time', '15tr', 'off', 'approved')""",
                    (comp_id, cat_id))
        self.approved_job_id = cur.lastrowid

        cur.execute("""INSERT INTO jobs (company_id, category_id, title, description, location, job_type, salary_text, saturday_policy, status)
                       VALUES (?, ?, 'Secret Pending Job', 'Desc', 'Hanoi', 'internship', 'Thoa thuan', 'working', 'pending')""",
                    (comp_id, cat_id))
        self.pending_job_id = cur.lastrowid

        # Career contents (1 published, 1 draft)
        cur.execute("INSERT INTO career_contents (title, summary, body, category, status) VALUES ('CV Guide', 'Sum', 'Body', 'CV', 'published')")
        cur.execute("INSERT INTO career_contents (title, summary, body, category, status) VALUES ('Draft Guide', 'Sum', 'Body', 'Career', 'draft')")

        conn.commit()
        conn.close()

    def test_public_guest_cannot_see_pending_job(self):
        res = self.client.get("/api/jobs")
        self.assertEqual(res.status_code, 200)
        jobs = res.get_json()
        job_ids = [j["id"] for j in jobs]
        self.assertIn(self.approved_job_id, job_ids)
        self.assertNotIn(self.pending_job_id, job_ids)

    def test_public_career_contents_no_draft(self):
        res = self.client.get("/api/career-contents")
        self.assertEqual(res.status_code, 200)
        articles = res.get_json()
        titles = [a["title"] for a in articles]
        self.assertIn("CV Guide", titles)
        self.assertNotIn("Draft Guide", titles)

    def test_filter_saturday_and_job_type(self):
        res = self.client.get("/api/jobs?saturday_policy=off&job_type=full_time")
        self.assertEqual(res.status_code, 200)
        jobs = res.get_json()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Python Developer")

        res2 = self.client.get("/api/jobs?saturday_policy=working")
        self.assertEqual(len(res2.get_json()), 0)

    def test_student_apply_and_duplicate_check(self):
        # Guest apply fails
        res = self.client.post(f"/api/applications/jobs/{self.approved_job_id}", json={"cover_letter": "Xin chao"})
        self.assertEqual(res.status_code, 401)

        # Login student
        self.client.post("/api/auth/login", json={"email": "student@test.com", "password": "pass123"})

        # Apply success
        res = self.client.post(f"/api/applications/jobs/{self.approved_job_id}", json={"cover_letter": "Xin chao"})
        self.assertEqual(res.status_code, 201)

        # Duplicate apply returns 409
        res_dup = self.client.post(f"/api/applications/jobs/{self.approved_job_id}", json={"cover_letter": "Xin chao lai"})
        self.assertEqual(res_dup.status_code, 409)

    def test_student_applications_filter(self):
        self.client.post("/api/auth/login", json={"email": "student@test.com", "password": "pass123"})
        self.client.post(f"/api/applications/jobs/{self.approved_job_id}", json={"cover_letter": "Test"})

        res = self.client.get("/api/applications/me?status=submitted&q=Python")
        self.assertEqual(res.status_code, 200)
        apps = res.get_json()
        self.assertEqual(len(apps), 1)

        res_none = self.client.get("/api/applications/me?status=accepted")
        self.assertEqual(len(res_none.get_json()), 0)

    def test_shared_location_and_accent_insensitive_public_search(self):
        locations = self.client.get("/api/locations/provinces?q=ha noi")
        self.assertEqual(locations.status_code, 200)
        self.assertEqual(locations.get_json()[0]["code"], "01")

        jobs = self.client.get("/api/jobs", query_string={"q": "python", "location": "hanoi"})
        self.assertEqual(jobs.status_code, 200)
        self.assertEqual([job["id"] for job in jobs.get_json()], [self.approved_job_id])

    def test_admin_moderation_filters_share_business_data(self):
        self.client.post("/api/auth/login", json={"email": "admin@test.com", "password": "pass123"})

        pending = self.client.get("/api/admin/pending/jobs", query_string={"q": "secret", "job_type": "internship"})
        self.assertEqual(pending.status_code, 200)
        self.assertEqual([job["id"] for job in pending.get_json()], [self.pending_job_id])

        jobs = self.client.get("/api/admin/jobs", query_string={"status": "approved", "location": "hanoi"})
        self.assertEqual(jobs.status_code, 200)
        self.assertEqual([job["id"] for job in jobs.get_json()], [self.approved_job_id])

        users = self.client.get("/api/admin/users", query_string={"q": "test student", "role": "student"})
        self.assertEqual(users.status_code, 200)
        self.assertEqual(users.get_json()[0]["email"], "student@test.com")

    def test_q_matches_skills_and_parent_category_includes_children(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("UPDATE jobs SET skills_required = 'Docker, Kubernetes' WHERE id = ?", (self.approved_job_id,))
        parent = conn.execute("INSERT INTO job_categories (name, level) VALUES ('Nhóm nghề test', 1)").lastrowid
        child = conn.execute("INSERT INTO job_categories (name, parent_id, level) VALUES ('Nghề con test', ?, 2)",
                             (parent,)).lastrowid
        conn.execute("UPDATE jobs SET category_id = ? WHERE id = ?", (child, self.approved_job_id))
        conn.commit()
        conn.close()

        # q khớp cả kỹ năng (ô tìm kiếm ghi "Vị trí tuyển dụng, kỹ năng...")
        res = self.client.get("/api/jobs", query_string={"q": "kubernetes"})
        self.assertEqual([j["id"] for j in res.get_json()], [self.approved_job_id])

        # từ khóa phổ biến = tên danh mục -> q phải tìm được theo tên danh mục
        res = self.client.get("/api/jobs", query_string={"q": "nghe con test"})
        self.assertEqual([j["id"] for j in res.get_json()], [self.approved_job_id])

        # chọn danh mục cha phải ra tin của danh mục con
        res = self.client.get("/api/jobs", query_string={"category_ids": str(parent)})
        self.assertEqual([j["id"] for j in res.get_json()], [self.approved_job_id])

        # category_ids không tồn tại -> rỗng, không được bỏ lọc
        res = self.client.get("/api/jobs", query_string={"category_ids": "99999"})
        self.assertEqual(res.get_json(), [])

        cats = {c["id"]: c for c in self.client.get("/api/jobs/categories").get_json()}
        self.assertEqual(cats[parent]["job_count"], 1)
        self.assertEqual(cats[child]["job_count"], 1)

    def test_category_count_ignores_expired_jobs_and_suggestions_stats(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("UPDATE jobs SET deadline = '2000-01-01' WHERE id = ?", (self.approved_job_id,))
        conn.commit()
        conn.close()
        cats = self.client.get("/api/jobs/categories").get_json()
        self.assertEqual(sum(c["job_count"] for c in cats), 0)
        self.assertEqual(self.client.get("/api/jobs/suggestions").get_json()["stats"],
                         {"total_jobs": 0, "total_companies": 0})

    def test_career_search_is_accent_insensitive(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO career_contents (title, summary, body, category, status) "
                     "VALUES ('Phỏng vấn online', 's', 'b', 'Phỏng vấn', 'published')")
        conn.commit()
        conn.close()
        titles = [a["title"] for a in self.client.get("/api/career-contents", query_string={"q": "phong van"}).get_json()]
        self.assertEqual(titles, ["Phỏng vấn online"])

    def test_public_pages_are_separate(self):
        home = self.client.get("/")
        jobs = self.client.get("/jobs")
        blog = self.client.get("/blog")

        self.assertEqual(home.status_code, 200)
        self.assertIn(b"M\xe1\xbb\x9f l\xe1\xbb\x91i t\xc6\xb0\xc6\xa1ng lai", home.data)
        self.assertNotIn(b'id="searchForm"', home.data)
        self.assertEqual(jobs.status_code, 200)
        self.assertIn(b'id="searchForm"', jobs.data)
        self.assertEqual(blog.status_code, 200)
        self.assertIn(b'id="blogCards"', blog.data)


if __name__ == "__main__":
    unittest.main()
