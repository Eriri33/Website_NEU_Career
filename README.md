# Career Connect — Website kết nối doanh nghiệp với sinh viên

Career Connect là website hỗ trợ kết nối sinh viên tìm việc/thực tập với doanh nghiệp tuyển dụng, đồng thời cung cấp nội dung hướng nghiệp cơ bản.

> **Phạm vi MVP:** ưu tiên hoàn thành quy trình tuyển dụng từ đầu đến cuối trong 1 tuần. Các tính năng như chatbot AI, email tự động, phỏng vấn video và tích hợp ATS không thuộc phạm vi bản đầu tiên.

## 1. Công nghệ sử dụng

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS (có thể dùng Bootstrap)
- **Kiểm thử API:** Postman
- **Quản lý mã nguồn:** Git và GitHub

## 2. Quy trình nghiệp vụ chính

1. Doanh nghiệp tạo tài khoản và cập nhật hồ sơ.
2. Admin/nhân viên kiểm duyệt duyệt hồ sơ doanh nghiệp.
3. Doanh nghiệp tạo tin tuyển dụng.
4. Admin/nhân viên kiểm duyệt duyệt tin trước khi công khai.
5. Sinh viên tìm kiếm, xem chi tiết và ứng tuyển vào tin hợp lệ.
6. Doanh nghiệp xem hồ sơ ứng tuyển và cập nhật trạng thái.
7. Sinh viên theo dõi trạng thái đơn ứng tuyển của mình.

Chỉ những tin đã được duyệt thuộc doanh nghiệp đã được duyệt mới xuất hiện trong danh sách việc làm công khai.

## 3. Chức năng trong MVP

### Sinh viên
- Đăng ký, đăng nhập và đăng xuất.
- Xem/cập nhật hồ sơ cơ bản.
- Tìm kiếm và xem tin tuyển dụng đã duyệt.
- Ứng tuyển và theo dõi trạng thái đơn.

### Doanh nghiệp
- Đăng ký tài khoản và cập nhật thông tin doanh nghiệp.
- Tạo, sửa và quản lý tin tuyển dụng.
- Xem ứng viên của các tin thuộc doanh nghiệp mình.
- Cập nhật trạng thái ứng tuyển.

### Admin / Nhân viên kiểm duyệt
- Duyệt hoặc từ chối hồ sơ doanh nghiệp.
- Duyệt hoặc từ chối tin tuyển dụng.

### Tính năng mở rộng nếu còn thời gian
- Tải CV.
- Bài viết hướng nghiệp.
- Gợi ý việc làm dựa trên ngành học/kỹ năng bằng quy tắc đơn giản.

## 4. Cấu trúc thư mục

```text
career_connect/
├── run.py
├── config.py
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── auth/
│   ├── students/
│   ├── companies/
│   ├── jobs/
│   ├── applications/
│   ├── admin/
│   ├── templates/
│   └── static/
│       └── css/
├── db/
│   └── schema.sql
├── docs/
│   ├── api-spec.md
│   └── one_week_plan.md
└── tests/
```

## 5. Cài đặt và chạy trên Windows

### Bước 1: Cài Python

Cài Python 3.10 trở lên. Khi cài đặt, nên bật tùy chọn **Add Python to PATH**.

### Bước 2: Mở terminal tại thư mục dự án

Nếu tải dự án dạng ZIP, hãy giải nén trước, sau đó mở PowerShell tại thư mục có file `run.py`.

### Bước 3: Tạo môi trường ảo

```powershell
py -m venv .venv
```

Kích hoạt môi trường ảo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn việc kích hoạt, chạy lệnh sau trong terminal hiện tại rồi thử lại:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### Bước 4: Cài thư viện

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 5: Khởi tạo database

```powershell
flask --app run.py init-db
```

Lệnh này tạo các bảng theo `db/schema.sql` trong file database `db/career_connect.db`.

### Bước 6: Chạy ứng dụng

```powershell
python run.py
```

Mở trình duyệt:

- Trang chủ: http://127.0.0.1:5000/
- Kiểm tra backend: http://127.0.0.1:5000/api/health

Kết quả kiểm tra backend dự kiến:

```json
{
  "status": "ok",
  "message": "Career Connect API is running"
}
```

Dừng server bằng `Ctrl + C`.

## 6. Kiểm thử API bằng Postman

Mặc định, API sử dụng session cookie của Flask. Sau khi đăng nhập trong Postman, hãy giữ cookie để các request tiếp theo sử dụng cùng phiên đăng nhập.

### 6.1. Đăng ký sinh viên

- Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- Body → raw → JSON:

```json
{
  "email": "student@example.com",
  "password": "secret123",
  "role": "student"
}
```

### 6.2. Đăng ký doanh nghiệp

```json
{
  "email": "business@example.com",
  "password": "secret123",
  "role": "business"
}
```

Tài khoản doanh nghiệp mới cần được admin/moderator duyệt hồ sơ trước khi tin tuyển dụng được công khai.

### 6.3. Đăng nhập

- Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- Body:

```json
{
  "email": "student@example.com",
  "password": "secret123"
}
```

### 6.4. Xem thông tin tài khoản hiện tại

- Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`

### 6.5. Cập nhật hồ sơ sinh viên

- Method: `PUT`
- URL: `http://127.0.0.1:5000/api/students/me`
- Body:

```json
{
  "full_name": "Nguyen Van A",
  "major": "Information Systems",
  "skills": "Python, SQL, HTML, CSS",
  "phone": "0900000000"
}
```

### 6.6. Tìm kiếm tin tuyển dụng công khai

- Method: `GET`
- URL: `http://127.0.0.1:5000/api/jobs`
- Tìm theo từ khóa: `http://127.0.0.1:5000/api/jobs?q=python`
- Lọc theo ngành: `http://127.0.0.1:5000/api/jobs?major=Information%20Systems`

Chỉ các tin đã duyệt thuộc doanh nghiệp đã duyệt mới được trả về.

### 6.7. Ứng tuyển

- Method: `POST`
- URL: `http://127.0.0.1:5000/api/applications/jobs/1`
- Body:

```json
{
  "cover_letter": "Tôi mong muốn ứng tuyển vào vị trí này."
}
```

Thay `1` bằng ID của tin tuyển dụng đã được duyệt. Mỗi sinh viên chỉ được ứng tuyển một lần cho cùng một tin.

### 6.8. Xem các đơn đã ứng tuyển

- Method: `GET`
- URL: `http://127.0.0.1:5000/api/applications/me`

### Lưu ý về admin/moderator

Không cho phép người dùng tự đăng ký trực tiếp vai trò `admin` hoặc `moderator`. Tài khoản kiểm duyệt cần được tạo thủ công trong database hoặc qua một seed script do nhóm quản lý. Không đưa mật khẩu thật hoặc password hash nhạy cảm lên GitHub.

## 7. API hiện có và phần cần phát triển tiếp

| Nhóm | API khởi đầu |
|---|---|
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` |
| Sinh viên | `GET/PUT /api/students/me` |
| Việc làm công khai | `GET /api/jobs`, `GET /api/jobs/<job_id>` |
| Hồ sơ doanh nghiệp | `GET/PUT /api/company/profile` |
| Ứng tuyển | `POST /api/applications/jobs/<job_id>`, `GET /api/applications/me` |
| Kiểm duyệt | `GET /api/admin/pending/companies`, `POST /api/admin/companies/<id>/review`, `GET /api/admin/pending/jobs`, `POST /api/admin/jobs/<id>/review` |

**Các phần cần thành viên phát triển tiếp:** CRUD tin tuyển dụng thuộc doanh nghiệp; danh sách ứng viên thuộc tin của doanh nghiệp; cập nhật trạng thái đơn; giao diện HTML cho các module; kiểm thử quyền sở hữu dữ liệu; seed data phục vụ demo.

Xem chi tiết request/response tại [`docs/api-spec.md`](docs/api-spec.md).

## 8. Phân công nhóm

### Thành viên 1 — Sinh viên
- Hồ sơ sinh viên.
- Tìm kiếm/lọc và xem chi tiết việc làm.
- Gửi đơn ứng tuyển và theo dõi trạng thái.
- Kiểm thử các chức năng phía sinh viên.

### Thành viên 2 — Doanh nghiệp và tuyển dụng
- Hồ sơ doanh nghiệp.
- Tạo/sửa/đóng tin tuyển dụng.
- Xem ứng viên và cập nhật trạng thái đơn.
- Đảm bảo doanh nghiệp chỉ truy cập dữ liệu của mình.

### Thành viên 3 — Nền tảng và Admin
- Flask, SQLite, schema và Git.
- Đăng nhập, phân quyền.
- Kiểm duyệt doanh nghiệp/tin tuyển dụng.
- Tích hợp, kiểm thử Postman, hướng dẫn chạy và chuẩn bị demo.

Kế hoạch theo ngày nằm trong [`docs/one_week_plan.md`](docs/one_week_plan.md).

## 9. Quy ước Git đề xuất

Tạo branch riêng cho từng thành viên, ví dụ:

```text
main
feature/student
feature/recruitment
feature/core-admin
```

Quy trình đề xuất:

1. Kéo code mới nhất từ `main`.
2. Làm việc trên branch cá nhân.
3. Commit với nội dung rõ ràng.
4. Push branch lên GitHub.
5. Tạo Pull Request hoặc thống nhất với nhóm trước khi merge vào `main`.
6. Chạy lại ứng dụng và kiểm tra luồng chính sau mỗi lần tích hợp.

Không commit các file `.venv/`, `__pycache__/`, file database thật, file `.env`, mật khẩu hoặc dữ liệu cá nhân lên repository.

## 10. Quy tắc nghiệp vụ và bảo mật cơ bản

- Chỉ doanh nghiệp đã được duyệt mới được đăng tin công khai.
- Chỉ tin đã được duyệt mới xuất hiện trong tìm kiếm công khai.
- Sinh viên chỉ xem hồ sơ và đơn ứng tuyển của chính mình.
- Doanh nghiệp chỉ xem/sửa tin và đơn thuộc doanh nghiệp của mình.
- Backend phải lấy user ID và vai trò từ session, không tin dữ liệu quyền gửi từ frontend.
- Mật khẩu phải được lưu dưới dạng hash, không lưu mật khẩu thuần.
- Kiểm tra dữ liệu đầu vào và xử lý lỗi rõ ràng.
- Đây là starter phục vụ phát triển và demo tại lớp; trước khi triển khai công khai cần cấu hình secret key an toàn, CSRF protection, HTTPS, giới hạn tải file và các biện pháp bảo mật phù hợp.

## 11. Tiêu chí hoàn thành MVP

- [ ] Đăng nhập và phân quyền hoạt động.
- [ ] Doanh nghiệp được duyệt mới được đăng tin công khai.
- [ ] Tin chưa duyệt không xuất hiện với sinh viên.
- [ ] Sinh viên tìm kiếm và ứng tuyển được.
- [ ] Không cho ứng tuyển trùng một tin.
- [ ] Doanh nghiệp xem được ứng viên và cập nhật trạng thái.
- [ ] Sinh viên theo dõi được trạng thái đơn của mình.
- [ ] Các quyền truy cập dữ liệu được kiểm thử.
- [ ] Có dữ liệu mẫu, hướng dẫn cài đặt và kịch bản demo.

---

**Lưu ý:** Đây là bộ khung ban đầu để nhóm cùng phát triển, không phải sản phẩm đã hoàn thiện. Hãy chạy thử trên máy của nhóm và kiểm thử các API trước khi dùng cho buổi trình diễn.

## API Contract

Xem tài liệu mô tả các API, request/response và quy tắc phân quyền tại đây:

[📄 API Contract](Career_Connect_API_Contract.md)