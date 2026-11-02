"""
Chạy: python -m unittest tests.test_business -v
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import create_app
from app.database import get_db, init_db, migrate_db

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def future(days):
    return (date.today() + timedelta(days=days)).isoformat()


class BusinessBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True, "SECRET_KEY": "test-secret",
            "DATABASE": os.path.join(self.tmp.name, "test.db"),
            "UPLOAD_FOLDER": os.path.join(self.tmp.name, "uploads"),
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()
            db = get_db()
            db.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, 'admin')",
                       ("admin@example.com", generate_password_hash("admin123")))
            db.executemany("INSERT INTO job_categories (name, is_active) VALUES (?, ?)",
                           [("Kế toán", 1), ("Marketing", 1), ("Đã tắt", 0)])
            db.executemany("INSERT INTO provinces (code, name) VALUES (?, ?)",
                           [("01", "Thành phố Hà Nội"), ("79", "Thành phố Hồ Chí Minh")])
            db.executemany("INSERT INTO wards (code, name, level, province_code) VALUES (?, ?, ?, ?)",
                           [("00004", "Phường Ba Đình", "Phường", "01"),
                            ("00008", "Phường Ngọc Hà", "Phường", "01"),
                            ("26734", "Phường Sài Gòn", "Phường", "79")])
            db.commit()
        self.cat_accounting, self.cat_marketing, self.cat_inactive = 1, 2, 3

    def tearDown(self):
        self.tmp.cleanup()

    # helpers
    def as_user(self, email, password="secret123"):
        """Chuyển phiên đăng nhập sang tài khoản khác."""
        self.client.post("/api/auth/logout")
        r = self.client.post("/api/auth/login", json={"email": email, "password": password})
        self.assertEqual(r.status_code, 200, r.json)

    def register(self, email, role):
        r = self.client.post("/api/auth/register", json={"email": email, "password": "secret123", "role": role})
        self.assertEqual(r.status_code, 201, r.json)

    def approved_business(self, email, name):
        self.register(email, "business")
        self.as_user(email)
        self.assertEqual(self.client.put("/api/company/profile", json={
            "company_name": name, "description": "Mô tả", "website": "https://example.com"}).status_code, 200)
        with self.app.app_context():
            db = get_db()
            db.execute("UPDATE companies SET approval_status='approved' WHERE company_name=?", (name,))
            db.commit()

    def approve_job(self, job_id):
        self.as_user("admin@example.com", "admin123")
        r = self.client.post(f"/api/admin/jobs/{job_id}/review", json={"decision": "approved"})
        self.assertEqual(r.status_code, 200, r.json)

    def create_job(self, **overrides):
        payload = {"title": "Thực tập kế toán", "description": "Hỗ trợ sổ sách", "location": "Phường Ba Đình, Thành phố Hà Nội",
                   "job_type": "internship", "category_id": self.cat_accounting}
        payload.update(overrides)
        r = self.client.post("/api/company/jobs", json=payload)
        self.assertEqual(r.status_code, 201, r.json)
        return r.json["job_id"]

    def student_applies(self, email, job_id, full_name, major="", skills="", cover=""):
        self.register(email, "student")
        self.as_user(email)
        self.client.put("/api/students/me", json={"full_name": full_name, "major": major, "skills": skills})
        r = self.client.post(f"/api/applications/jobs/{job_id}", json={"cover_letter": cover})
        self.assertEqual(r.status_code, 201, r.json)
        return r.json["application_id"]


class CompanyProfileTests(BusinessBase):
    def test_profile_update_resets_approval_to_pending(self):
        self.approved_business("a@example.com", "Công ty A")
        self.assertEqual(self.client.get("/api/company/profile").json["approval_status"], "approved")
        r = self.client.put("/api/company/profile", json={"company_name": "Công ty A mới", "description": "x", "website": ""})
        self.assertEqual(r.status_code, 200)
        profile = self.client.get("/api/company/profile").json
        self.assertEqual(profile["approval_status"], "pending")
        self.assertEqual(profile["company_name"], "Công ty A mới")
        self.assertEqual(profile["email"], "a@example.com")

    def test_profile_validation(self):
        self.register("a@example.com", "business")
        self.as_user("a@example.com")
        put = lambda **kw: self.client.put("/api/company/profile", json=kw)
        self.assertEqual(put(company_name="  ").status_code, 400)
        self.assertEqual(put(company_name="X", website="javascript:alert(1)").status_code, 400)
        self.assertEqual(put(company_name="X", website="example.com").status_code, 400)
        self.assertEqual(put(company_name=123).status_code, 400)
        self.assertEqual(put(company_name="X" * 151).status_code, 400)
        self.assertEqual(put(company_name="X", website="https://ok.vn").status_code, 200)
        self.assertEqual(self.client.put("/api/company/profile", json=["bad"]).status_code, 400)

    def test_roles_and_anonymous(self):
        self.assertEqual(self.client.get("/api/company/profile").status_code, 401)
        self.register("s@example.com", "student")
        self.as_user("s@example.com")
        for path in ("/api/company/profile", "/api/company/jobs", "/api/company/applications",
                     "/api/company/applications/stats", "/api/company/categories"):
            self.assertEqual(self.client.get(path).status_code, 403, path)

    def test_categories_only_active(self):
        self.register("a@example.com", "business")
        self.as_user("a@example.com")
        names = [c["name"] for c in self.client.get("/api/company/categories").json]
        self.assertEqual(names, ["Kế toán", "Marketing"])


class CompanyJobTests(BusinessBase):
    def test_pending_company_cannot_create_job(self):
        self.register("a@example.com", "business")
        self.as_user("a@example.com")
        r = self.client.post("/api/company/jobs", json={"title": "T", "description": "D"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json["error"], "company_not_approved")

    def test_create_validation(self):
        self.approved_business("a@example.com", "Công ty A")
        post = lambda **kw: self.client.post("/api/company/jobs", json=kw)
        base = {"title": "T", "description": "D"}
        self.assertEqual(post(title="", description="D").status_code, 400)
        self.assertEqual(post(**{**base, "job_type": "freelance"}).status_code, 400)
        self.assertEqual(post(**{**base, "saturday_policy": "maybe"}).status_code, 400)
        self.assertEqual(post(**{**base, "deadline": "31/12/2030"}).status_code, 400)
        self.assertEqual(post(**{**base, "deadline": "2020-01-01"}).status_code, 400)
        self.assertEqual(post(**{**base, "category_id": 999}).status_code, 400)
        self.assertEqual(post(**{**base, "category_id": self.cat_inactive}).status_code, 400)
        self.assertEqual(post(**{**base, "category_id": "abc"}).status_code, 400)
        self.assertEqual(post(**{**base, "title": 5}).status_code, 400)
        self.assertEqual(post(**{**base, "title": "T" * 151}).status_code, 400)
        self.assertEqual(post(**{**base, "salary_text": "x" * 101}).status_code, 400)
        self.assertEqual(self.client.post("/api/company/jobs", json=[1]).status_code, 400)
        self.assertEqual(post(**base).status_code, 201)

    def test_new_fields_default_and_custom(self):
        self.approved_business("a@example.com", "Công ty A")
        j1 = self.create_job()
        j2 = self.create_job(title="Có lương", salary_text="10-12 triệu", saturday_policy="off", deadline=future(30))
        d1 = self.client.get(f"/api/company/jobs/{j1}").json
        d2 = self.client.get(f"/api/company/jobs/{j2}").json
        self.assertEqual((d1["salary_text"], d1["saturday_policy"], d1["status"]), ("Thỏa thuận", "unknown", "pending"))
        self.assertEqual((d2["salary_text"], d2["saturday_policy"], d2["deadline"]), ("10-12 triệu", "off", future(30)))
        self.assertEqual(d1["category_name"], "Kế toán")
        self.assertEqual(d1["application_count"], 0)

    def test_edit_returns_to_pending_and_flags_re_review(self):
        self.approved_business("a@example.com", "Công ty A")
        job_id = self.create_job()
        self.assertFalse(self.client.get(f"/api/company/jobs/{job_id}").json["needs_re_review"])
        self.approve_job(job_id)
        self.as_user("a@example.com")
        self.assertEqual(self.client.get(f"/api/company/jobs/{job_id}").json["status"], "approved")
        self.assertEqual(self.client.get("/api/jobs").json[0]["id"], job_id)  # đang công khai

        r = self.client.put(f"/api/company/jobs/{job_id}", json={"salary_text": "15 triệu"})
        self.assertEqual(r.status_code, 200)
        job = self.client.get(f"/api/company/jobs/{job_id}").json
        self.assertEqual(job["status"], "pending")
        self.assertTrue(job["needs_re_review"])
        self.assertEqual(job["salary_text"], "15 triệu")
        self.assertEqual(job["title"], "Thực tập kế toán")  # field không gửi giữ nguyên
        self.assertEqual(self.client.get("/api/jobs").json, [])  # không còn công khai

    def test_edit_keeps_unchanged_past_deadline_but_rejects_new_past_deadline(self):
        self.approved_business("a@example.com", "Công ty A")
        job_id = self.create_job(deadline=future(5))
        with self.app.app_context():
            db = get_db()
            db.execute("UPDATE jobs SET deadline='2020-01-01' WHERE id=?", (job_id,))
            db.commit()
        self.assertEqual(self.client.put(f"/api/company/jobs/{job_id}", json={"title": "Đổi tên", "deadline": "2020-01-01"}).status_code, 200)
        self.assertEqual(self.client.put(f"/api/company/jobs/{job_id}", json={"deadline": "2020-02-02"}).status_code, 400)
        self.assertTrue(self.client.get(f"/api/company/jobs/{job_id}").json["is_expired"])

    def test_edit_can_clear_optional_fields(self):
        self.approved_business("a@example.com", "Công ty A")
        job_id = self.create_job(deadline=future(10), skills_required="Excel")
        self.client.put(f"/api/company/jobs/{job_id}", json={"deadline": None, "category_id": None, "skills_required": ""})
        job = self.client.get(f"/api/company/jobs/{job_id}").json
        self.assertIsNone(job["deadline"])
        self.assertIsNone(job["category_id"])
        self.assertEqual(job["skills_required"], "")

    def test_delete_closes_job_and_keeps_applications(self):
        self.approved_business("a@example.com", "Công ty A")
        job_id = self.create_job()
        self.approve_job(job_id)
        app_id = self.student_applies("s@example.com", job_id, "Nguyễn Văn A")
        self.as_user("a@example.com")
        self.assertEqual(self.client.delete(f"/api/company/jobs/{job_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/company/jobs/{job_id}").json["status"], "closed")
        self.assertEqual(self.client.get(f"/api/company/applications/{app_id}").status_code, 200)
        self.assertEqual(self.client.get("/api/jobs").json, [])

    def test_job_list_filters(self):
        self.approved_business("a@example.com", "Công ty A")
        ids = {
            "ke_toan": self.create_job(title="Thực tập Kế toán", location="Phường Ba Đình, Thành phố Hà Nội",
                                       job_type="internship", category_id=self.cat_accounting, deadline=future(40)),
            "mkt": self.create_job(title="Content Marketing", description="Viết bài", location="Phường Sài Gòn, Thành phố Hồ Chí Minh",
                                   job_type="full_time", category_id=self.cat_marketing, deadline=future(5)),
            "none": self.create_job(title="Nhân viên 100% remote", description="Làm tại nhà", location="", job_type="part_time",
                                    category_id=None),
        }
        self.approve_job(ids["mkt"])
        self.as_user("a@example.com")
        get = lambda **qs: [j["id"] for j in self.client.get("/api/company/jobs", query_string=qs).json]

        self.assertEqual(set(get()), set(ids.values()))
        self.assertEqual(get(q="ke toan"), [ids["ke_toan"]])          # không dấu khớp có dấu
        self.assertEqual(get(q="KẾ TOÁN"), [ids["ke_toan"]])          # hoa/thường + dấu
        self.assertEqual(get(q="viet bai"), [ids["mkt"]])             # tìm trong mô tả
        self.assertEqual(get(status="approved"), [ids["mkt"]])
        self.assertEqual(set(get(status="pending")), {ids["ke_toan"], ids["none"]})
        self.assertEqual(get(category_id=self.cat_marketing), [ids["mkt"]])
        self.assertEqual(get(location="ha noi"), [ids["ke_toan"]])
        self.assertEqual(get(location="Hồ Chí Minh"), [ids["mkt"]])
        self.assertEqual(get(job_type="part_time"), [ids["none"]])
        self.assertEqual(get(q="thuc tap", location="ha noi", status="pending", job_type="internship",
                             category_id=self.cat_accounting), [ids["ke_toan"]])
        self.assertEqual(get(q="thuc tap", status="approved"), [])     # AND giữa các nhóm
        self.assertEqual(get(q="%"), [ids["none"]])                      # '%' chỉ khớp ký tự % thật, không là wildcard
        self.assertEqual(get(q="_"), [])
        self.assertEqual(get(sort="deadline_soon"), [ids["mkt"], ids["ke_toan"], ids["none"]])  # NULL cuối
        self.assertEqual(get(sort="latest")[0], ids["none"])

        for bad in ({"status": "weird"}, {"job_type": "x"}, {"sort": "random"}, {"category_id": "abc"}):
            self.assertEqual(self.client.get("/api/company/jobs", query_string=bad).status_code, 400, bad)

    def test_job_counts_in_list(self):
        self.approved_business("a@example.com", "Công ty A")
        job_id = self.create_job()
        self.approve_job(job_id)
        a1 = self.student_applies("s1@example.com", job_id, "SV Một")
        self.student_applies("s2@example.com", job_id, "SV Hai")
        self.as_user("a@example.com")
        self.client.patch(f"/api/company/applications/{a1}/status", json={"status": "reviewing"})
        job = self.client.get("/api/company/jobs").json[0]
        self.assertEqual((job["application_count"], job["new_application_count"]), (2, 1))


class OwnershipTests(BusinessBase):
    def setUp(self):
        super().setUp()
        self.approved_business("a@example.com", "Công ty A")
        self.job_a = self.create_job(title="Việc của A")
        self.approve_job(self.job_a)
        self.app_a = self.student_applies("s@example.com", self.job_a, "Sinh Viên Một", major="Kế toán", skills="Excel")
        self.approved_business("b@example.com", "Công ty B")
        self.job_b = self.create_job(title="Việc của B")
        self.approve_job(self.job_b)
        self.as_user("b@example.com")

    def test_cannot_touch_other_business_job(self):
        c = self.client
        self.assertEqual(c.get(f"/api/company/jobs/{self.job_a}").status_code, 404)
        self.assertEqual(c.put(f"/api/company/jobs/{self.job_a}", json={"title": "Hack"}).status_code, 404)
        self.assertEqual(c.delete(f"/api/company/jobs/{self.job_a}").status_code, 404)
        self.assertEqual([j["id"] for j in c.get("/api/company/jobs").json], [self.job_b])
        self.assertEqual(c.get("/api/company/jobs", query_string={"q": "của A"}).json, [])
        self.as_user("a@example.com")
        job = self.client.get(f"/api/company/jobs/{self.job_a}").json
        self.assertEqual((job["title"], job["status"]), ("Việc của A", "approved"))  # không bị thay đổi

    def test_cannot_see_other_business_applicants(self):
        c = self.client
        self.assertEqual(c.get("/api/company/applications").json, [])
        self.assertEqual(c.get("/api/company/applications", query_string={"job_id": self.job_a}).json, [])
        self.assertEqual(c.get("/api/company/applications", query_string={"q": "Sinh Viên"}).json, [])
        self.assertEqual(c.get(f"/api/company/applications/{self.app_a}").status_code, 404)
        self.assertEqual(c.get("/api/company/applications/stats", query_string={"job_id": self.job_a}).json["total"], 0)

    def test_cannot_update_other_business_application(self):
        r = self.client.patch(f"/api/company/applications/{self.app_a}/status", json={"status": "accepted"})
        self.assertEqual(r.status_code, 404)
        self.as_user("a@example.com")
        self.assertEqual(self.client.get(f"/api/company/applications/{self.app_a}").json["status"], "submitted")


class CompanyApplicationTests(BusinessBase):
    def setUp(self):
        super().setUp()
        self.approved_business("a@example.com", "Công ty A")
        self.job1 = self.create_job(title="Kế toán thực tập")
        self.job2 = self.create_job(title="Marketing thực tập", category_id=self.cat_marketing)
        self.approve_job(self.job1)
        self.approve_job(self.job2)
        self.a1 = self.student_applies("an@student.vn", self.job1, "Nguyễn Văn An", major="Kế toán", skills="Excel, SQL", cover="Em quan tâm")
        self.a2 = self.student_applies("binh@student.vn", self.job1, "Trần Thị Bình", major="Marketing", skills="SEO, Content")
        self.a3 = self.student_applies("chi@student.vn", self.job2, "Lê Chi", major="Hệ thống thông tin", skills="Python")
        self.as_user("a@example.com")

    def ids(self, **qs):
        return [a["application_id"] for a in self.client.get("/api/company/applications", query_string=qs).json]

    def test_filters(self):
        self.assertEqual(self.ids(), [self.a3, self.a2, self.a1])                   # latest
        self.assertEqual(self.ids(sort="oldest"), [self.a1, self.a2, self.a3])
        self.assertEqual(self.ids(job_id=self.job1), [self.a2, self.a1])
        self.assertEqual(self.ids(q="nguyen van"), [self.a1])                       # tên không dấu
        self.assertEqual(self.ids(q="binh@student"), [self.a2])                     # email
        self.assertEqual(self.ids(q="he thong"), [self.a3])                         # ngành
        self.assertEqual(self.ids(q="seo"), [self.a2])                              # kỹ năng
        self.assertEqual(self.ids(q="python", job_id=self.job1), [])                # AND
        self.assertEqual(self.ids(q="python", job_id=self.job2), [self.a3])
        self.assertEqual(self.ids(q="%"), [])
        r = self.client.patch(f"/api/company/applications/{self.a2}/status", json={"status": "reviewing"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.ids(status="reviewing"), [self.a2])
        self.assertEqual(self.ids(status="submitted", job_id=self.job1), [self.a1])
        for bad in ({"status": "pending"}, {"sort": "x"}, {"job_id": "abc"}):
            self.assertEqual(self.client.get("/api/company/applications", query_string=bad).status_code, 400, bad)

    def test_stats(self):
        self.client.patch(f"/api/company/applications/{self.a1}/status", json={"status": "accepted"})
        self.client.patch(f"/api/company/applications/{self.a2}/status", json={"status": "rejected"})
        stats = self.client.get("/api/company/applications/stats").json
        self.assertEqual(stats, {"submitted": 1, "reviewing": 0, "accepted": 1, "rejected": 1, "withdrawn": 0, "total": 3})
        scoped = self.client.get("/api/company/applications/stats", query_string={"job_id": self.job1}).json
        self.assertEqual((scoped["accepted"], scoped["rejected"], scoped["submitted"], scoped["total"]), (1, 1, 0, 2))
        searched = self.client.get("/api/company/applications/stats", query_string={"q": "python"}).json
        self.assertEqual((searched["submitted"], searched["total"]), (1, 1))

    def test_detail_and_status_flow(self):
        detail = self.client.get(f"/api/company/applications/{self.a1}").json
        self.assertEqual((detail["full_name"], detail["major"], detail["cover_letter"], detail["status"]),
                         ("Nguyễn Văn An", "Kế toán", "Em quan tâm", "submitted"))
        for status in ("reviewing", "accepted", "rejected", "reviewing"):
            r = self.client.patch(f"/api/company/applications/{self.a1}/status", json={"status": status})
            self.assertEqual((r.status_code, r.json["status"]), (200, status))
        self.assertEqual(self.client.get(f"/api/company/applications/{self.a1}").json["status"], "reviewing")
        for bad in ("submitted", "withdrawn", "whatever", None):
            self.assertEqual(self.client.patch(f"/api/company/applications/{self.a1}/status",
                                               json={"status": bad}).status_code, 400, bad)
        self.assertEqual(self.client.patch("/api/company/applications/9999/status", json={"status": "accepted"}).status_code, 404)

    def test_withdrawn_cannot_be_updated_and_student_sees_new_status(self):
        self.client.patch(f"/api/company/applications/{self.a2}/status", json={"status": "accepted"})
        self.as_user("binh@student.vn")
        self.assertEqual(self.client.get("/api/applications/me").json[0]["status"], "accepted")
        self.assertEqual(self.client.delete(f"/api/applications/{self.a2}").status_code, 409)  # đã accepted
        self.as_user("an@student.vn")
        self.assertEqual(self.client.delete(f"/api/applications/{self.a1}").status_code, 200)
        self.as_user("a@example.com")
        r = self.client.patch(f"/api/company/applications/{self.a1}/status", json={"status": "accepted"})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.ids(status="withdrawn"), [self.a1])


class LocationAndMigrationTests(BusinessBase):
    def test_locations_api(self):
        provinces = self.client.get("/api/locations/provinces").json
        self.assertEqual([p["code"] for p in provinces], ["01", "79"])
        self.assertEqual([p["code"] for p in self.client.get("/api/locations/provinces", query_string={"q": "ho chi minh"}).json], ["79"])
        wards = self.client.get("/api/locations/provinces/01/wards").json
        self.assertEqual([w["name"] for w in wards], ["Phường Ba Đình", "Phường Ngọc Hà"])
        self.assertEqual([w["code"] for w in self.client.get("/api/locations/provinces/01/wards", query_string={"q": "ngoc"}).json], ["00008"])
        self.assertEqual(self.client.get("/api/locations/provinces/99/wards").status_code, 404)

    def test_real_csv_has_hanoi_and_wards(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            import import_administrative_units as imp
        finally:
            sys.path.pop(0)
        provinces, wards = imp.read_csv()
        with self.app.app_context():
            db = get_db()
            imp.import_data(db, provinces, wards)
        self.assertEqual(len(self.client.get("/api/locations/provinces").json), 34)
        hn = self.client.get("/api/locations/provinces", query_string={"q": "ha noi"}).json
        self.assertEqual([p["name"] for p in hn], ["Thành phố Hà Nội"])
        self.assertGreater(len(self.client.get(f"/api/locations/provinces/{hn[0]['code']}/wards").json), 50)

    def test_migration_is_idempotent_and_keeps_data(self):
        path = os.path.join(self.tmp.name, "old.db")
        db = sqlite3.connect(path)
        db.executescript("""
            CREATE TABLE jobs (id INTEGER PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending');
            INSERT INTO jobs (title) VALUES ('Tin cũ');
        """)
        db.row_factory = sqlite3.Row
        migrate_db(db)
        migrate_db(db)  # chạy lần hai không lỗi
        row = db.execute("SELECT * FROM jobs").fetchone()
        self.assertEqual((row["title"], row["saturday_policy"], row["salary_text"]), ("Tin cũ", "unknown", "Thỏa thuận"))
        db.close()


class BusinessPagesTests(BusinessBase):
    def test_pages_redirect_when_not_business_and_render_when_business(self):
        for path in ("/business/dashboard", "/business/jobs", "/business/jobs/new", "/business/jobs/1",
                     "/business/jobs/1/edit", "/business/applicants", "/business/profile"):
            r = self.client.get(path)
            self.assertEqual(r.status_code, 302, path)
            self.assertIn("/business/login", r.headers["Location"])
        self.assertEqual(self.client.get("/business/login").status_code, 200)
        self.register("s@example.com", "student")
        self.as_user("s@example.com")
        self.assertIn("reason=role", self.client.get("/business/dashboard").headers["Location"])
        self.register("a@example.com", "business")
        self.as_user("a@example.com")
        for path in ("/business/dashboard", "/business/jobs", "/business/jobs/new", "/business/jobs/1",
                     "/business/jobs/1/edit", "/business/applicants", "/business/profile"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.assertEqual(self.client.get("/business/login").status_code, 302)  # đã đăng nhập -> dashboard


if __name__ == "__main__":
    unittest.main()
