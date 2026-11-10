# Module Business (TV2) — Bàn giao

Phạm vi: hồ sơ doanh nghiệp, quản lý tin tuyển dụng, tìm/lọc ứng viên, cập nhật trạng thái đơn.

## Chạy thử

Khởi động ứng dụng bằng `run.cmd` tại thư mục gốc. Script tự chuẩn bị môi trường
Python, khởi tạo database và chạy web server.

Để nạp dữ liệu địa giới và tài khoản demo (tùy chọn), chạy tại thư mục gốc:

```cmd
.venv\Scripts\python.exe scripts\import_administrative_units.py
.venv\Scripts\python.exe scripts\seed_business_demo.py
```

Hoặc khởi tạo và chạy thủ công:

```powershell
flask --app run.py init-db
python scripts/import_administrative_units.py
python scripts/seed_business_demo.py        # dữ liệu demo, chạy lại nhiều lần vẫn an toàn
python run.py
```

Mở `http://127.0.0.1:5000/business/login` — `business@demo.neu.vn` / `demo1234`.
`business2@demo.neu.vn` dùng để thử quyền sở hữu; `admin@demo.neu.vn` / `admin123` để duyệt (qua API cho tới khi TV3 làm UI duyệt).
Chạy test: `python -m unittest tests.test_business tests.test_api -v`

## Trang giao diện (`/business/*`)

| URL | Nội dung | API dùng |
|---|---|---|
| `/business/login` | Đăng nhập/đăng ký doanh nghiệp | `/api/auth/*` |
| `/business/dashboard` | Số liệu, phễu trạng thái hồ sơ, việc cần chú ý | `/api/company/jobs`, `applications`, `applications/stats` |
| `/business/jobs` | Danh sách + tìm/lọc tin, đóng tin | `GET /api/company/jobs`, `DELETE /api/company/jobs/<id>` |
| `/business/jobs/new`, `/<id>/edit` | Form tạo/sửa tin (tỉnh → phường/xã từ DB) | `POST/PUT /api/company/jobs`, `/api/company/categories`, `/api/locations/*` |
| `/business/jobs/<id>` | Chi tiết tin, trạng thái duyệt, hồ sơ của tin | `/api/company/jobs/<id>`, `applications*` |
| `/business/applicants` | Tìm/lọc ứng viên, ngăn chi tiết, đổi trạng thái | `/api/company/applications*` |
| `/business/profile` | Hồ sơ công ty, trạng thái duyệt | `GET/PUT /api/company/profile` |

Mọi trang có trạng thái đang tải, rỗng, lỗi (có nút Thử lại). Không có dữ liệu giả trong JavaScript.

## File thêm/sửa

- Sửa (backend): `backend/app/__init__.py`, `backend/app/database.py`, `backend/app/companies/routes.py`, `db/schema.sql`
- Mới (backend): `backend/app/textutil.py`, `backend/app/locations/`, `backend/app/business_ui/`, `scripts/seed_business_demo.py`
- Mới/sửa (frontend): `frontend/templates/business/*`, `frontend/static/css/{neu-tokens,business}.css`, `frontend/static/js/business/*`, `frontend/static/images/*`
- Test: `tests/test_business.py` (24 ca)

## Thay đổi body `POST/PUT /api/company/jobs` (so với contract mục 7.2)

Thêm hai field tùy chọn (khớp contract mục 14):

```json
{
  "salary_text": "5 - 7 triệu",
  "saturday_policy": "off"
}
```

`salary_text` tối đa 100 ký tự, rỗng thì lưu "Thỏa thuận". `saturday_policy` nhận `off`, `working`, `negotiable`, `unknown` (mặc định `unknown`).

## Đề xuất bổ sung contract cho `/api/company/*` (chờ nhóm duyệt rồi mới đưa vào `API_CONTRACT.md`)

Các mục dưới đây đã có code + test trong `tests/test_business.py`.

**Bộ lọc `GET /api/company/jobs`:** `q` (tiêu đề/mô tả), `status`, `category_id`, `location`, `job_type`, `sort=latest|deadline_soon` (tin không có hạn xếp cuối). Tất cả kết hợp AND. Giá trị không hợp lệ trả `400` (`invalid_status`, `invalid_sort`, `invalid_input`). Mỗi tin trả thêm: `application_count`, `new_application_count` (đơn `submitted`), `needs_re_review` (đang `pending` sau khi từng được duyệt/từ chối), `is_expired` (deadline đã qua).

**Bộ lọc `GET /api/company/applications`:** `job_id`, `status`, `q` (tên/email/ngành/kỹ năng), `sort=latest|oldest`. Ràng buộc sở hữu (`c.user_id = session`) luôn áp dụng trước bộ lọc. Chi tiết đơn trả thêm `bio`, `job_status`.

**Tìm kiếm không phân biệt hoa/thường và dấu tiếng Việt:** `q` và `location` được so khớp qua hàm SQL `fold()` (đăng ký trong `get_db()`), nên `ke toan` khớp `Kế toán`, `ha noi` khớp `Thành phố Hà Nội`. Ký tự `%` và `_` trong từ khóa được escape.

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/company/applications/stats?job_id=&q=` | Business | Số đơn theo trạng thái trong phạm vi lọc, dùng cho tab đếm: `{"submitted":1,"reviewing":0,"accepted":0,"rejected":0,"withdrawn":0,"total":1}` |
| `GET` | `/api/company/categories` | Business | Danh mục đang hoạt động `[{"id","name"}]` để chọn khi đăng tin |
| `GET` | `/api/locations/provinces?q=` | Public | Tỉnh/thành từ bảng `provinces` |
| `GET` | `/api/locations/provinces/<code>/wards?q=` | Public | Phường/xã của một tỉnh (`404` nếu mã tỉnh sai) |

**Validation bổ sung:** hồ sơ `website` chỉ nhận `http://` hoặc `https://` (chặn `javascript:`); giới hạn độ dài `title` 150, `description` 10000, `location`/`major_required` 255, `skills_required` 500, `salary_text` 100, `company_name` 150; `deadline` mới không được ở quá khứ (giữ nguyên hạn cũ khi sửa tin thì được); `category_id` phải là danh mục đang hoạt động; trường văn bản phải là chuỗi.

**Quy ước `jobs.location`:** vẫn là một chuỗi. Giao diện doanh nghiệp ghép `"<địa chỉ cụ thể>, <phường/xã>, <tỉnh/thành>"` theo tên trong `wards`/`provinces`; lọc công khai theo tỉnh vẫn dùng `location LIKE`.

## Hồ sơ công ty mở rộng

Thêm 3 trường tùy chọn vào bảng `companies` (có migration, DB cũ vẫn dùng được):

| Cột | Ý nghĩa | Ràng buộc |
|---|---|---|
| `company_size` | Quy mô nhân sự | rỗng hoặc `1-9`, `10-24`, `25-99`, `100-499`, `500-999`, `1000+` |
| `industry` / `primary_industry` | Ngành nghề kinh doanh chính; hai field được đồng bộ để tương thích client cũ | tối đa 150 ký tự cho `industry`, 255 ký tự cho `primary_industry` |
| `business_industries` | Các lĩnh vực kinh doanh, phân cách bằng dấu phẩy | tối đa 1000 ký tự |
| `address` | Địa điểm công ty, dạng `"<chi tiết>, <phường/xã>, <tỉnh/thành>"` | tối đa 255 ký tự |

`GET /api/company/profile` trả các trường trên. `PUT /api/company/profile` nhận chúng; **không gửi trường nào thì giữ nguyên giá trị đã lưu** (client cũ chỉ gửi 3 trường cơ bản vẫn chạy đúng). `industry` và `primary_industry` đồng bộ khi chỉ một trong hai được gửi. Gửi chuỗi rỗng để xóa. Lưu hồ sơ vẫn đưa trạng thái về `pending`.

Giao diện `/business/profile` có ô chọn quy mô, ngành nghề (gợi ý + nhập tự do), lĩnh vực kinh doanh, địa chỉ chọn tỉnh/phường từ bảng dùng chung, bản đồ và liên kết chia sẻ hồ sơ công khai. Bản đồ dùng Google Maps, không cần API key.

Chưa làm: logo công ty và bộ chọn nhiều ngành nghề phụ có cấu trúc riêng. Trang công khai chỉ hiện hồ sơ đã được duyệt và tài khoản còn hoạt động.

## Thay đổi chạm vào phần của TV3/TV1

1. `db/schema.sql` + `migrate_db()` trong `backend/app/database.py`: thêm `jobs.saturday_policy`, `jobs.salary_text` (theo contract mục 14) và các trường hồ sơ công ty. Migration idempotent, chạy trong `init-db` và khi khởi động nếu DB đã tồn tại.
2. `get_db()` đăng ký hàm SQL `fold()` để tìm kiếm không dấu. TV1/TV3 có thể dùng lại (`backend/app/textutil.py`).
3. Blueprint mới `/api/locations/*` đọc bảng `provinces`/`wards` chung (không đổi cấu trúc bảng).
4. TV1 cần thêm `salary_text`, `saturday_policy` vào SELECT của `/api/jobs` để hiển thị/lọc; TV3 thêm vào danh sách admin.
5. Trang `/business/login` là bản tối thiểu để module chạy độc lập; TV3 có thể thay bằng trang đăng nhập chung và đổi redirect trong `backend/app/business_ui/routes.py`.

## Chưa làm / giới hạn

- **Doanh nghiệp chưa xem được CV của ứng viên.** Contract hiện chỉ cho sinh viên tải CV của mình và bảng `applications` không gắn CV. Muốn có cần thêm `applications.cv_id` và endpoint tải cho business — cần nhóm thống nhất contract.
- Hồ sơ công ty chưa có logo và chưa có nhiều ngành nghề phụ.
- Hàng chờ duyệt và UI admin thuộc TV3; hiện duyệt doanh nghiệp/tin phải gọi API (Postman) hoặc dùng seed.
- Lưu hồ sơ công ty luôn đưa trạng thái về `pending` theo contract, kể cả khi nội dung không đổi (UI chặn lưu khi không có thay đổi và cảnh báo trước khi gửi duyệt lại).
- Phân trang chưa có (list trả mảng JSON theo contract).
- Google Fonts tải từ CDN; offline sẽ dùng font hệ thống.
- Chưa có test tự động cho JavaScript; đã kiểm thử tay bằng trình duyệt (đăng nhập sai, lọc, tạo tin, đổi trạng thái, đăng ký mới, truy cập chéo).
