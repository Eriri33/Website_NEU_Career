"""Nạp dữ liệu DEMO cho module Business (idempotent — chạy nhiều lần không nhân đôi).

    flask --app run.py init-db
    python scripts/import_administrative_units.py
    python scripts/seed_business_demo.py

Tài khoản demo (mật khẩu chỉ dùng để trình diễn, KHÔNG dùng cho môi trường thật):
    admin@demo.neu.vn / admin123          (admin)
    business@demo.neu.vn / demo1234       (doanh nghiệp đã duyệt)
    business2@demo.neu.vn / demo1234      (doanh nghiệp thứ hai, để thử quyền sở hữu)
    sv1..sv6@demo.neu.vn / demo1234       (sinh viên)
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from werkzeug.security import generate_password_hash
from app import create_app
from app.database import get_db, init_db

PW = generate_password_hash("demo1234")
HN = "Thành phố Hà Nội"
HCM = "Thành phố Hồ Chí Minh"


def d(days):
    return (date.today() + timedelta(days=days)).isoformat()


CATEGORIES = ["Kế toán - Kiểm toán", "Marketing - Truyền thông", "Tài chính - Ngân hàng", "Công nghệ thông tin",
              "Kinh doanh - Bán hàng", "Nhân sự - Hành chính", "Logistics - Chuỗi cung ứng"]

# (tiêu đề, mô tả, địa điểm, loại, ngành, kỹ năng, hạn, lương, thứ Bảy, danh mục, trạng thái, ghi chú duyệt)
JOBS = [
    ("Thực tập sinh Kế toán tổng hợp", "Hỗ trợ lập chứng từ, đối chiếu công nợ và theo dõi sổ sách hằng tháng. Được đào tạo quy trình kế toán thực tế.",
     f"Phường Đống Đa, {HN}", "internship", "Kế toán", "Excel, Kế toán tổng hợp", d(30), "5 - 7 triệu", "off", 1, "approved", ""),
    ("Chuyên viên Marketing Digital", "Lập kế hoạch và chạy quảng cáo đa kênh, phân tích hiệu quả chiến dịch, phối hợp với đội nội dung.",
     f"Phường Ba Đình, {HN}", "full_time", "Marketing", "SEO, Google Ads, Content", d(5), "12 - 18 triệu", "negotiable", 2, "approved", ""),
    ("Data Analyst thực tập", "Làm sạch dữ liệu, dựng dashboard và báo cáo định kỳ cho khối kinh doanh.",
     f"Phường Cầu Giấy, {HN}", "internship", "Khoa học dữ liệu", "SQL, Python, Power BI", d(45), "Thỏa thuận", "unknown", 4, "approved", ""),
    ("Nhân viên Kinh doanh B2B", "Tìm kiếm và chăm sóc khách hàng doanh nghiệp, tư vấn giải pháp, theo dõi hợp đồng.",
     HCM, "full_time", "Quản trị kinh doanh", "Giao tiếp, Đàm phán", d(20), "10 - 15 triệu + hoa hồng", "working", 5, "pending", ""),
    ("Thực tập sinh Nhân sự", "Hỗ trợ tuyển dụng, sàng lọc hồ sơ và tổ chức phỏng vấn.",
     f"Phường Hai Bà Trưng, {HN}", "internship", "Quản trị nhân lực", "Giao tiếp, Excel", d(25), "3 - 4 triệu", "off", 6, "pending", "Đã sửa mô tả"),
    ("Chuyên viên Phân tích Tín dụng", "Thẩm định hồ sơ vay doanh nghiệp, lập báo cáo rủi ro.",
     f"Phường Hoàn Kiếm, {HN}", "full_time", "Tài chính - Ngân hàng", "Phân tích tài chính", d(15), "Từ 15 triệu", "off", 3, "rejected", "Mô tả chưa nêu rõ yêu cầu kinh nghiệm và quyền lợi."),
    ("Cộng tác viên Content", "Viết bài cho fanpage và blog công ty.", f"Phường Cầu Giấy, {HN}", "part_time", "Marketing", "Viết lách",
     d(-3), "Thỏa thuận", "unknown", 2, "approved", ""),
    ("Thực tập Logistics", "Theo dõi đơn hàng và phối hợp vận chuyển.", f"Phường Long Biên, {HN}", "internship", "Logistics và quản lý chuỗi cung ứng",
     "Excel", d(10), "4 - 5 triệu", "off", 7, "closed", ""),
]

STUDENTS = [
    ("sv1", "Nguyễn Minh Anh", "Kế toán", "Excel, Kế toán tổng hợp, Tiếng Anh", "0912345601", "Sinh viên năm 3, mong muốn thực tập kế toán tại doanh nghiệp vừa và nhỏ."),
    ("sv2", "Trần Quốc Bảo", "Khoa học dữ liệu", "SQL, Python, Power BI", "0912345602", "Đã làm 2 dự án phân tích dữ liệu bán lẻ trên lớp."),
    ("sv3", "Lê Thu Hà", "Marketing", "SEO, Content, Google Ads", "0912345603", "Quản lý fanpage của câu lạc bộ sinh viên."),
    ("sv4", "Phạm Đức Huy", "Quản trị nhân lực", "Giao tiếp, Excel", "0912345604", ""),
    ("sv5", "Vũ Ngọc Lan", "Kế toán", "Excel, MISA", "0912345605", "Có chứng chỉ kế toán viên cơ bản."),
    ("sv6", "Đỗ Hoàng Nam", "Hệ thống thông tin quản lý", "SQL, Python, Tableau", "0912345606", ""),
]

# (sinh viên, chỉ số tin, trạng thái, thư ứng tuyển)
APPLICATIONS = [
    ("sv1", 0, "submitted", "Em xin ứng tuyển vị trí thực tập kế toán. Em có thể làm việc 4 buổi mỗi tuần."),
    ("sv5", 0, "reviewing", "Em đã quen với MISA và có thể bắt đầu từ tháng sau."),
    ("sv2", 2, "submitted", "Em quan tâm đến mảng phân tích dữ liệu và muốn học thêm về xây dựng dashboard."),
    ("sv6", 2, "accepted", "Em mong được tham gia dự án dữ liệu của công ty."),
    ("sv3", 1, "submitted", "Em có kinh nghiệm chạy quảng cáo Facebook cho dự án của câu lạc bộ."),
    ("sv4", 1, "rejected", ""),
    ("sv1", 1, "withdrawn", "Em xin rút đơn vì đã nhận lời công việc khác."),
]


def user(db, email, role, password_hash=PW):
    row = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if row:
        return row["id"]
    return db.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)", (email, password_hash, role)).lastrowid


def main():
    app = create_app()
    with app.app_context():
        db = get_db()
        if not db.execute("SELECT name FROM sqlite_master WHERE name = 'users'").fetchone():
            init_db()
        admin_id = user(db, "admin@demo.neu.vn", "admin", generate_password_hash("admin123"))
        for name in CATEGORIES:
            db.execute("INSERT OR IGNORE INTO job_categories (name) VALUES (?)", (name,))

        def company(email, name, desc, site, size="", industry="", address=""):
            uid = user(db, email, "business")
            if not db.execute("SELECT 1 FROM companies WHERE user_id = ?", (uid,)).fetchone():
                db.execute("INSERT INTO companies (user_id, company_name, description, website, company_size, industry, address, "
                           "approval_status, reviewed_by, reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'approved', ?, CURRENT_TIMESTAMP)",
                           (uid, name, desc, site, size, industry, address, admin_id))
            else:  # DB cũ đã seed trước khi có 3 trường mới: điền bổ sung nếu đang trống
                db.execute("UPDATE companies SET company_size = ?, industry = ?, address = ? WHERE user_id = ? AND company_size = '' AND industry = '' AND address = ''",
                           (size, industry, address, uid))
            return db.execute("SELECT id FROM companies WHERE user_id = ?", (uid,)).fetchone()["id"]

        c1 = company("business@demo.neu.vn", "Công ty Cổ phần Giải pháp Số Hoàng Long",
                     "Đơn vị tư vấn và triển khai giải pháp quản trị doanh nghiệp, thường xuyên nhận sinh viên NEU thực tập.", "https://example.com",
                     "25-99", "Công nghệ thông tin", f"Số 207 Giải Phóng, Phường Bạch Mai, {HN}")
        c2 = company("business2@demo.neu.vn", "Công ty TNHH Thương mại Đông Á", "Doanh nghiệp thương mại, dùng để kiểm tra quyền sở hữu dữ liệu.", "")

        cats = {r["name"]: r["id"] for r in db.execute("SELECT id, name FROM job_categories")}
        cat_ids = [cats[n] for n in CATEGORIES]
        job_ids = []
        for (title, desc, loc, jt, major, skills, dl, salary, sat, cat, status, note) in JOBS:
            row = db.execute("SELECT id FROM jobs WHERE company_id = ? AND title = ?", (c1, title)).fetchone()
            if row:
                job_ids.append(row["id"]); continue
            jid = db.execute("""INSERT INTO jobs (company_id, category_id, title, description, location, job_type, major_required,
                skills_required, deadline, salary_text, saturday_policy, status, review_note, reviewed_by, reviewed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (c1, cat_ids[cat - 1], title, desc, loc, jt, major, skills, dl, salary, sat, status,
                 note if status == "rejected" else "", admin_id)).lastrowid
            if status in ("approved", "rejected", "closed"):
                db.execute("INSERT INTO review_histories (reviewer_id, entity_type, entity_id, action, note) VALUES (?, 'job', ?, ?, ?)",
                           (admin_id, jid, "rejected" if status == "rejected" else "approved", note if status == "rejected" else ""))
            if title == "Thực tập sinh Nhân sự":  # từng được duyệt rồi sửa lại -> "chờ duyệt lại"
                db.execute("INSERT INTO review_histories (reviewer_id, entity_type, entity_id, action) VALUES (?, 'job', ?, 'approved')", (admin_id, jid))
            job_ids.append(jid)
        db.execute("INSERT OR IGNORE INTO jobs (company_id, title, description, status, location) SELECT ?, 'Tin của công ty khác', 'Dùng thử quyền sở hữu', 'approved', ? "
                   "WHERE NOT EXISTS (SELECT 1 FROM jobs WHERE company_id = ? AND title = 'Tin của công ty khác')", (c2, HN, c2))

        sids = {}
        for key, name, major, skills, phone, bio in STUDENTS:
            uid = user(db, f"{key}@demo.neu.vn", "student")
            sids[key] = uid
            if not db.execute("SELECT 1 FROM student_profiles WHERE user_id = ?", (uid,)).fetchone():
                db.execute("INSERT INTO student_profiles (user_id, full_name, major, skills, phone, bio) VALUES (?, ?, ?, ?, ?, ?)",
                           (uid, name, major, skills, phone, bio))
        for key, idx, status, letter in APPLICATIONS:
            if not db.execute("SELECT 1 FROM applications WHERE job_id = ? AND student_id = ?", (job_ids[idx], sids[key])).fetchone():
                db.execute("INSERT INTO applications (job_id, student_id, cover_letter, status) VALUES (?, ?, ?, ?)",
                           (job_ids[idx], sids[key], letter, status))
        db.commit()
    print("Đã nạp dữ liệu demo. Đăng nhập: business@demo.neu.vn / demo1234 tại /business/login")


if __name__ == "__main__":
    main()
