"""Seed script: tạo dữ liệu demo để test TV1 (Public Discovery + Student Journey)."""
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent / "db" / "career_connect.db"


def seed():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ===== USERS =====
    users = [
        ("admin@neu.edu.vn", generate_password_hash("admin123"), "admin"),
        ("mod@neu.edu.vn", generate_password_hash("mod123"), "moderator"),
        ("student1@sv.neu.edu.vn", generate_password_hash("student123"), "student"),
        ("student2@sv.neu.edu.vn", generate_password_hash("student123"), "student"),
        ("abc@company.vn", generate_password_hash("business123"), "business"),
        ("tech@company.vn", generate_password_hash("business123"), "business"),
        ("marketing@company.vn", generate_password_hash("business123"), "business"),
    ]
    user_ids = {}
    for email, pw, role in users:
        try:
            cur.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)", (email, pw, role))
            uid = cur.lastrowid
            user_ids[email] = uid
            if role == "student":
                cur.execute("INSERT INTO student_profiles (user_id) VALUES (?)", (uid,))
            elif role == "business":
                cur.execute("INSERT INTO companies (user_id, company_name) VALUES (?, ?)", (uid, "Chưa cập nhật"))
        except sqlite3.IntegrityError:
            existing = cur.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                user_ids[email] = existing[0]

    conn.commit()

    # ===== UPDATE STUDENT PROFILES =====
    s1 = user_ids.get("student1@sv.neu.edu.vn")
    s2 = user_ids.get("student2@sv.neu.edu.vn")
    if s1:
        cur.execute("""UPDATE student_profiles SET full_name='Nguyễn Văn An', major='Hệ thống thông tin quản lý',
            skills='Python, SQL, Excel, Power BI', phone='0901234567', bio='Sinh viên năm 3, đam mê phân tích dữ liệu.'
            WHERE user_id=?""", (s1,))
    if s2:
        cur.execute("""UPDATE student_profiles SET full_name='Trần Thị Bình', major='Marketing',
            skills='Content Marketing, SEO, Canva, Facebook Ads', phone='0912345678', bio='Sinh viên năm 4 chuyên ngành Marketing.'
            WHERE user_id=?""", (s2,))
    conn.commit()

    # ===== UPDATE COMPANY PROFILES =====
    companies = {
        "abc@company.vn": ("ABC Technology", "Công ty phần mềm hàng đầu Việt Nam, chuyên về giải pháp ERP và BI.", "https://abc-tech.vn"),
        "tech@company.vn": ("FPT Software", "Công ty công nghệ thông tin thuộc tập đoàn FPT.", "https://fpt-software.com"),
        "marketing@company.vn": ("Ogilvy Vietnam", "Agency marketing quốc tế với hơn 20 năm tại Việt Nam.", "https://ogilvy.vn"),
    }
    for email, (name, desc, web) in companies.items():
        uid = user_ids.get(email)
        if uid:
            cur.execute("""UPDATE companies SET company_name=?, description=?, website=?,
                approval_status='approved', reviewed_by=?, reviewed_at=CURRENT_TIMESTAMP
                WHERE user_id=?""", (name, desc, web, user_ids.get("admin@neu.edu.vn"), uid))
    conn.commit()

    # ===== JOB CATEGORIES =====
    categories = [
        ("Công nghệ thông tin", "Phát triển phần mềm, quản trị hệ thống, dữ liệu"),
        ("Marketing", "Marketing, quảng cáo, truyền thông, PR"),
        ("Tài chính - Ngân hàng", "Ngân hàng, chứng khoán, bảo hiểm, kế toán"),
        ("Kinh doanh", "Sales, kinh doanh, phát triển thị trường"),
        ("Nhân sự", "Tuyển dụng, đào tạo, C&B"),
        ("Kế toán - Kiểm toán", "Kế toán, kiểm toán, thuế"),
        ("Logistics", "Chuỗi cung ứng, xuất nhập khẩu, vận tải"),
        ("Thiết kế", "Graphic Design, UI/UX, Video Production"),
    ]
    cat_ids = {}
    for name, desc in categories:
        try:
            cur.execute("INSERT INTO job_categories (name, description) VALUES (?, ?)", (name, desc))
            cat_ids[name] = cur.lastrowid
        except sqlite3.IntegrityError:
            row = cur.execute("SELECT id FROM job_categories WHERE name = ?", (name,)).fetchone()
            if row:
                cat_ids[name] = row[0]
    conn.commit()

    # ===== JOBS =====
    c1 = cur.execute("SELECT id FROM companies WHERE user_id=?", (user_ids.get("abc@company.vn"),)).fetchone()
    c2 = cur.execute("SELECT id FROM companies WHERE user_id=?", (user_ids.get("tech@company.vn"),)).fetchone()
    c3 = cur.execute("SELECT id FROM companies WHERE user_id=?", (user_ids.get("marketing@company.vn"),)).fetchone()

    jobs_data = [
        (c1[0] if c1 else 1, cat_ids.get("Công nghệ thông tin"), "Python Backend Intern",
         "Tham gia phát triển hệ thống ERP bằng Python/Flask. Được mentor trực tiếp bởi Senior Developer.",
         "Hà Nội", "internship", "Hệ thống thông tin quản lý", "Python, SQL, Git", "5-8 triệu/tháng", "off", "2027-03-31"),
        (c1[0] if c1 else 1, cat_ids.get("Công nghệ thông tin"), "Data Analyst Fresher",
         "Phân tích dữ liệu kinh doanh, xây dựng dashboard và báo cáo BI cho các dự án enterprise.",
         "Hà Nội", "full_time", "Hệ thống thông tin quản lý", "SQL, Power BI, Excel, Python", "12-18 triệu/tháng", "off", "2027-02-28"),
        (c2[0] if c2 else 1, cat_ids.get("Công nghệ thông tin"), "Full Stack Developer",
         "Phát triển ứng dụng web full-stack sử dụng React + Node.js. Làm việc theo Agile/Scrum.",
         "Hà Nội", "full_time", "", "JavaScript, React, Node.js, MongoDB", "15-25 triệu/tháng", "negotiable", "2027-04-30"),
        (c2[0] if c2 else 1, cat_ids.get("Công nghệ thông tin"), "QA Tester Intern",
         "Kiểm thử phần mềm, viết test case, báo cáo bug. Cơ hội được đào tạo về automation testing.",
         "Đà Nẵng", "internship", "", "Kiểm thử phần mềm, Jira", "4-6 triệu/tháng", "work", "2027-03-15"),
        (c3[0] if c3 else 1, cat_ids.get("Marketing"), "Content Marketing Intern",
         "Sáng tạo nội dung cho các kênh social media, viết blog và email marketing.",
         "Hồ Chí Minh", "internship", "Marketing", "Content Writing, SEO, Canva", "5-7 triệu/tháng", "off", "2027-01-31"),
        (c3[0] if c3 else 1, cat_ids.get("Marketing"), "Digital Marketing Executive",
         "Quản lý chiến dịch quảng cáo trên Facebook, Google Ads. Phân tích và tối ưu ROAS.",
         "Hà Nội", "full_time", "Marketing", "Facebook Ads, Google Ads, Analytics", "15-20 triệu/tháng", "off", "2027-05-31"),
        (c1[0] if c1 else 1, cat_ids.get("Kinh doanh"), "Business Analyst Intern",
         "Phân tích yêu cầu khách hàng, viết tài liệu nghiệp vụ cho các dự án phần mềm.",
         "Hà Nội", "internship", "Quản trị kinh doanh", "Excel, SQL, Communication", "6-8 triệu/tháng", "off", "2027-02-15"),
        (c2[0] if c2 else 1, cat_ids.get("Nhân sự"), "HR Intern",
         "Hỗ trợ quy trình tuyển dụng, sàng lọc hồ sơ, sắp xếp phỏng vấn.",
         "Hà Nội", "internship", "Quản trị nhân lực", "MS Office, Communication", "Thỏa thuận", "off", "2027-03-31"),
        (c1[0] if c1 else 1, cat_ids.get("Tài chính - Ngân hàng"), "Kế toán viên Part-time",
         "Hỗ trợ ghi sổ, đối soát công nợ và xử lý chứng từ kế toán.",
         "Hà Nội", "part_time", "Kế toán", "Kế toán, Excel, MISA", "Thỏa thuận", "off", "2027-04-15"),
        (c3[0] if c3 else 1, cat_ids.get("Thiết kế"), "Graphic Design Intern",
         "Thiết kế ấn phẩm truyền thông, social media posts, banner quảng cáo.",
         "Hồ Chí Minh", "internship", "Thiết kế đồ họa", "Photoshop, Illustrator, Figma", "5-7 triệu/tháng", "negotiable", "2027-02-28"),
    ]

    reviewer_id = user_ids.get("admin@neu.edu.vn")
    for company_id, cat_id, title, desc, loc, jtype, major, skills, salary, sat, deadline in jobs_data:
        try:
            cur.execute("""INSERT INTO jobs (company_id, category_id, title, description, location, job_type,
                major_required, skills_required, salary_text, saturday_policy, deadline, status,
                reviewed_by, reviewed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?, CURRENT_TIMESTAMP)""",
                (company_id, cat_id, title, desc, loc, jtype, major, skills, salary, sat, deadline, reviewer_id))
        except sqlite3.IntegrityError:
            pass
    conn.commit()

    # ===== CAREER CONTENTS =====
    career_items = [
        ("Cách viết CV ấn tượng cho sinh viên thực tập", "Hướng dẫn viết CV chuyên nghiệp thu hút nhà tuyển dụng.",
         """Một CV tốt nên ngắn gọn, súc tích và nổi bật kỹ năng phù hợp với vị trí ứng tuyển.

1. Thông tin cá nhân: Đầy đủ nhưng không lan man
2. Mục tiêu nghề nghiệp: Cụ thể cho từng vị trí
3. Kinh nghiệm và dự án: Dùng số liệu để minh họa
4. Kỹ năng: Liệt kê những kỹ năng liên quan trực tiếp
5. Hoạt động ngoại khóa: Thể hiện soft skills""",
         "CV", "published"),
        ("Top 5 kỹ năng doanh nghiệp tìm kiếm ở sinh viên mới ra trường",
         "Khảo sát từ 200 doanh nghiệp tuyển dụng tại NEU Career Fair 2026.",
         """Kết quả khảo sát cho thấy 5 kỹ năng được đánh giá cao nhất:

1. Giao tiếp và thuyết trình
2. Tư duy phân tích và giải quyết vấn đề
3. Làm việc nhóm
4. Quản lý thời gian
5. Kỹ năng số (Digital Literacy)

Sinh viên nên rèn luyện các kỹ năng này song song với kiến thức chuyên ngành.""",
         "Kỹ năng", "published"),
        ("Hướng dẫn phỏng vấn online hiệu quả",
         "Mẹo chuẩn bị cho buổi phỏng vấn trực tuyến thành công.",
         """Phỏng vấn online ngày càng phổ biến. Để tạo ấn tượng tốt:

- Kiểm tra kết nối internet, camera và micro trước 30 phút
- Chọn không gian yên tĩnh, ánh sáng tốt
- Mặc trang phục lịch sự giống phỏng vấn trực tiếp
- Chuẩn bị CV, bài tập (nếu có) sẵn trên màn hình
- Nhìn vào camera khi nói, không nhìn vào hình mình trên màn hình""",
         "Phỏng vấn", "published"),
    ]
    for title, summary, body, category, status in career_items:
        try:
            cur.execute("""INSERT INTO career_contents (title, summary, body, category, status, author_id)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (title, summary, body, category, status, user_ids.get("admin@neu.edu.vn")))
        except sqlite3.IntegrityError:
            pass
    conn.commit()

    # ===== LOG REVIEWS =====
    # Log review for companies
    for email in ["abc@company.vn", "tech@company.vn", "marketing@company.vn"]:
        uid = user_ids.get(email)
        if uid:
            comp = cur.execute("SELECT id FROM companies WHERE user_id=?", (uid,)).fetchone()
            if comp:
                try:
                    cur.execute("""INSERT INTO review_histories (reviewer_id, entity_type, entity_id, action, note)
                        VALUES (?, 'company', ?, 'approved', 'Doanh nghiệp hợp lệ.')""",
                        (reviewer_id, comp[0]))
                except:
                    pass
    conn.commit()

    conn.close()
    print("[OK] Seed data created successfully!")
    print()
    print("=== TAI KHOAN DEMO ===")
    print("Admin:     admin@neu.edu.vn / admin123")
    print("Moderator: mod@neu.edu.vn / mod123")
    print("Student 1: student1@sv.neu.edu.vn / student123")
    print("Student 2: student2@sv.neu.edu.vn / student123")
    print("Business:  abc@company.vn / business123")
    print("Business:  tech@company.vn / business123")
    print("Business:  marketing@company.vn / business123")


if __name__ == "__main__":
    seed()

