# CAREER CONNECT — API CONTRACT

**Phiên bản:** 1.0  
**Mục đích:** Quy ước giao tiếp thống nhất giữa frontend và backend, đồng thời là hợp đồng làm việc giữa các thành viên.  
**Backend:** Flask + SQLite  
**Base URL khi chạy local:** `http://127.0.0.1:5000`  
**API prefix:** `/api`

> Quy tắc quan trọng: Frontend phải dùng đúng endpoint, HTTP method, tên trường và trạng thái trong tài liệu này. Không tự đổi tên field hoặc tự tạo URL khác. Nếu nhóm cần thay đổi contract, phải thống nhất trước và cập nhật tài liệu cùng code trong một commit.

## 1. Quy ước chung

### 1.1. Request và response

- Request/response dữ liệu thông thường dùng JSON với header `Content-Type: application/json`.
- Tải CV sử dụng `multipart/form-data`, tên field file bắt buộc là `file`.
- `GET` dùng để đọc; `POST` để tạo hoặc thực hiện hành động; `PUT` để cập nhật; `PATCH` để cập nhật một phần/trạng thái; `DELETE` để xóa mềm/đóng/rút theo quy tắc nghiệp vụ.
- ID trong URL là số nguyên, ví dụ `/api/jobs/12`.
- Ngày deadline dùng định dạng `YYYY-MM-DD`, ví dụ `2026-12-31`.
- Response danh sách là JSON array `[...]`; response chi tiết là JSON object `{...}`.
- Bản MVP hiện không cam kết phân trang. Không dựa vào thứ tự thuộc tính trong JSON.

### 1.2. Đăng nhập và session

API sử dụng **Flask session cookie**, không sử dụng Bearer token trong phiên bản này.

1. Gọi `POST /api/auth/login`.
2. Client phải lưu và gửi lại cookie session trong các request tiếp theo.
3. Với Postman, bật cookie jar và giữ cookie của `127.0.0.1`.
4. Không gửi `user_id` hoặc `role` từ frontend để quyết định quyền. Backend lấy danh tính/quyền từ session.

### 1.3. Vai trò

| Giá trị `role` | Ý nghĩa |
|---|---|
| `student` | Sinh viên |
| `business` | Tài khoản doanh nghiệp |
| `moderator` | Nhân viên kiểm duyệt/nội dung |
| `admin` | Quản trị viên |

Người dùng tự đăng ký chỉ được chọn `student` hoặc `business`. Tài khoản `moderator` và `admin` do admin tạo.

### 1.4. Response lỗi chuẩn

Lỗi trả về JSON có tối thiểu trường `error`; nhiều lỗi có thêm `message`.

```json
{
  "error": "invalid_input",
  "message": "Thông tin gửi lên không hợp lệ."
}
```

| HTTP status | Ý nghĩa hợp đồng |
|---|---|
| `200 OK` | Đọc/cập nhật/thao tác thành công |
| `201 Created` | Tạo tài nguyên thành công |
| `400 Bad Request` | Thiếu dữ liệu hoặc dữ liệu sai định dạng/giá trị |
| `401 Unauthorized` | Chưa đăng nhập hoặc thông tin đăng nhập sai |
| `403 Forbidden` | Không đủ quyền hoặc chưa thỏa điều kiện nghiệp vụ |
| `404 Not Found` | Không tìm thấy tài nguyên hoặc tài nguyên không thuộc quyền xem |
| `405 Method Not Allowed` | Dùng HTTP method không được hỗ trợ |
| `409 Conflict` | Trùng dữ liệu hoặc xung đột trạng thái nghiệp vụ |
| `413 Content Too Large` | Request tải lên vượt giới hạn |

Tên `error` cụ thể có thể khác nhau theo endpoint; frontend nên ưu tiên kiểm tra HTTP status, sau đó hiển thị `message` nếu có.

## 2. Sơ đồ phân quyền tổng quát

| Nhóm chức năng | Public | Student | Business | Moderator | Admin |
|---|---:|---:|---:|---:|---:|
| Health check, tin đã duyệt, bài hướng nghiệp đã xuất bản | Có | Có | Có | Có | Có |
| Tài khoản hiện tại, đổi mật khẩu, vô hiệu hóa chính mình | — | Có | Có | Có | Có |
| Hồ sơ/CV/đơn ứng tuyển của bản thân | — | Có | — | — | — |
| Hồ sơ doanh nghiệp và tin của doanh nghiệp mình | — | — | Có | — | — |
| Xem ứng viên và cập nhật trạng thái đơn thuộc tin của mình | — | — | Có | — | — |
| Duyệt hồ sơ doanh nghiệp và tin tuyển dụng | — | — | — | Có | Có |
| Xem lịch sử kiểm duyệt | — | — | — | Có | Có |
| Quản lý tài khoản và vai trò | — | — | — | — | Có |
| Quản lý danh mục việc làm | — | — | — | Đọc | CRUD |
| Quản lý bài hướng nghiệp | Chỉ đọc bài đã xuất bản | — | — | CRUD | CRUD |

**Quy tắc quyền sở hữu:** sinh viên chỉ thao tác CV và đơn của mình; doanh nghiệp chỉ thao tác hồ sơ/tin/đơn gắn với doanh nghiệp của mình. Nếu không tìm thấy hoặc không thuộc quyền xem, API thường trả `404` để không tiết lộ dữ liệu của người khác.

## 3. Health check

| Method | Endpoint | Quyền |
|---|---|---|
| `GET` | `/api/health` | Public |

Response `200`:

```json
{"status":"ok","message":"Career Connect API is running"}
```

## 4. Auth và tài khoản — `/api/auth`

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Đăng ký sinh viên/doanh nghiệp |
| `POST` | `/api/auth/login` | Public | Đăng nhập, tạo session |
| `POST` | `/api/auth/logout` | Public | Xóa session hiện tại |
| `GET` | `/api/auth/me` | Đã đăng nhập | Xem tài khoản hiện tại |
| `PUT` | `/api/auth/me` | Đã đăng nhập | Cập nhật email |
| `PUT` | `/api/auth/password` | Đã đăng nhập | Đổi mật khẩu |
| `DELETE` | `/api/auth/me` | Đã đăng nhập | Vô hiệu hóa tài khoản hiện tại |

### `POST /api/auth/register`

Request:

```json
{
  "email": "student@example.com",
  "password": "secret123",
  "role": "student"
}
```

`role` chỉ nhận `student` hoặc `business`; mật khẩu tối thiểu 6 ký tự.

Response `201`:

```json
{"message":"Tạo tài khoản thành công.","user_id":1,"role":"student"}
```

Khi `role=student`, backend tự tạo hồ sơ sinh viên trống. Khi `role=business`, backend tự tạo hồ sơ doanh nghiệp ở trạng thái `pending` với tên mặc định “Chưa cập nhật”. Email trùng trả `409`.

### `POST /api/auth/login`

Request:

```json
{"email":"student@example.com","password":"secret123"}
```

Response `200`:

```json
{
  "message":"Đăng nhập thành công.",
  "user":{"id":1,"email":"student@example.com","role":"student"}
}
```

Email/mật khẩu sai trả `401`; tài khoản bị vô hiệu hóa trả `403`.

### `GET /api/auth/me`

Response `200` (ví dụ):

```json
{"id":1,"email":"student@example.com","role":"student","is_active":1,"created_at":"2026-10-28 09:00:00"}
```

### `PUT /api/auth/me`

Chỉ cập nhật email, không cập nhật role qua endpoint này.

```json
{"email":"new.email@example.com"}
```

Response `200`: `{"message":"Đã cập nhật email."}`. Email trùng trả `409`.

### `PUT /api/auth/password`

```json
{"current_password":"secret123","new_password":"newsecret123"}
```

Response `200`: `{"message":"Đã đổi mật khẩu."}`. Mật khẩu cũ sai hoặc mật khẩu mới dưới 6 ký tự trả `400`.

### `DELETE /api/auth/me`

Không xóa cứng tài khoản hoặc lịch sử nghiệp vụ; đặt `is_active=0` và xóa session hiện tại. Response `200`:

```json
{"message":"Tài khoản đã được vô hiệu hóa; dữ liệu lịch sử được giữ lại."}
```

## 5. Hồ sơ sinh viên và CV — `/api/students`

### 5.1. Hồ sơ sinh viên

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/students/me` | Student | Đọc hồ sơ của mình |
| `PUT` | `/api/students/me` | Student | Cập nhật hồ sơ của mình |
| `GET` | `/api/students/me/recommendations` | Student | Gợi ý tối đa 20 việc làm theo ngành/kỹ năng |

Hồ sơ được tạo cùng tài khoản nên không có endpoint tạo/xóa hồ sơ riêng. Tắt tài khoản không xóa hồ sơ và lịch sử.

Request cập nhật:

```json
{
  "full_name":"Nguyen Van A",
  "major":"Information Systems",
  "skills":"Python, SQL, HTML, CSS",
  "phone":"0900000000",
  "bio":"Sinh viên năm 3, đang tìm vị trí thực tập."
}
```

Response `200`:

```json
{"message":"Đã cập nhật hồ sơ sinh viên."}
```

Các field chưa gửi hoặc rỗng được lưu thành chuỗi rỗng ở phiên bản hiện tại; frontend nên gửi đủ 5 field khi lưu form.

### 5.2. CV — CRUD

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/students/me/cvs` | Student | Liệt kê CV của mình |
| `POST` | `/api/students/me/cvs` | Student | Tải CV lên |
| `GET` | `/api/students/me/cvs/<cv_id>` | Student | Xem metadata CV |
| `GET` | `/api/students/me/cvs/<cv_id>/download` | Student | Tải file CV xuống |
| `PUT` | `/api/students/me/cvs/<cv_id>` | Student | Thay file CV hiện tại |
| `DELETE` | `/api/students/me/cvs/<cv_id>` | Student | Xóa CV và file tương ứng |

`POST`/`PUT` sử dụng `multipart/form-data` với field `file`. File cho phép `.pdf`, `.doc`, `.docx`; tổng request hiện giới hạn 5 MB. Không gửi JSON cho upload CV.

Response tạo `201`:

```json
{"message":"Đã tải CV lên.","cv_id":3,"filename":"resume.pdf"}
```

Response metadata `200`:

```json
{"id":3,"original_filename":"resume.pdf","created_at":"2026-10-28 09:00:00"}
```

Response thay file `200`:

```json
{"message":"Đã thay thế CV.","cv_id":3,"filename":"resume-new.docx"}
```

Response xóa `200`: `{"message":"Đã xóa CV."}`. ID CV chỉ được sử dụng bởi chủ sở hữu.

## 6. Việc làm công khai — `/api/jobs`

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/jobs` | Public | Danh sách/tìm kiếm/lọc tin đã duyệt |
| `GET` | `/api/jobs/<job_id>` | Public | Chi tiết tin đã duyệt |

Query parameters của `GET /api/jobs`:

| Tham số | Kiểu | Ý nghĩa |
|---|---|---|
| `q` | string | Từ khóa trong tiêu đề, mô tả hoặc tên doanh nghiệp |
| `major` | string | Lọc theo ngành yêu cầu; tin không giới hạn ngành vẫn có thể hiển thị |
| `location` | string | Lọc địa điểm theo chuỗi |
| `job_type` | enum | `internship`, `full_time`, `part_time`, `contract` |
| `category_id` | integer | Lọc danh mục |

Ví dụ: `GET /api/jobs?q=python&location=Ha%20Noi&job_type=internship`.

Response là mảng JSON. Mỗi tin có các trường chính `id`, `title`, `description`, `location`, `job_type`, `major_required`, `skills_required`, `deadline`, `created_at`, `category_id`, `category_name`, `company_name`.

Chỉ trả tin `approved`, thuộc doanh nghiệp `approved`, tài khoản doanh nghiệp đang hoạt động và deadline chưa qua. Tin không thỏa điều kiện trả `404` khi gọi chi tiết.

## 7. Doanh nghiệp, tin tuyển dụng và ứng viên — `/api/company`

### 7.1. Hồ sơ doanh nghiệp

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/company/profile` | Business | Xem hồ sơ doanh nghiệp của mình |
| `PUT` | `/api/company/profile` | Business | Cập nhật hồ sơ doanh nghiệp của mình |

Request `PUT`:

```json
{
  "company_name":"ABC Technology",
  "description":"Công ty phần mềm.",
  "website":"https://example.com"
}
```

`company_name` là bắt buộc. Cập nhật thông tin sẽ đặt `approval_status` về `pending`; doanh nghiệp cần được duyệt lại. Response `200`:

```json
{"message":"Đã cập nhật hồ sơ; doanh nghiệp cần được duyệt lại."}
```

### 7.2. Tin tuyển dụng — CRUD nghiệp vụ

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/company/jobs` | Business | Liệt kê tin của doanh nghiệp mình |
| `POST` | `/api/company/jobs` | Business đã được duyệt | Tạo tin mới |
| `GET` | `/api/company/jobs/<job_id>` | Business sở hữu tin | Xem chi tiết tin của mình |
| `PUT` | `/api/company/jobs/<job_id>` | Business sở hữu tin | Cập nhật tin và gửi duyệt lại |
| `DELETE` | `/api/company/jobs/<job_id>` | Business sở hữu tin | Đóng tin, không xóa cứng |

Request `POST` (những field bắt buộc được đánh dấu):

```json
{
  "title":"Python Intern",
  "description":"Tham gia phát triển ứng dụng web.",
  "location":"Ha Noi",
  "job_type":"internship",
  "major_required":"Information Systems",
  "skills_required":"Python, SQL",
  "deadline":"2026-12-31",
  "category_id":1
}
```

Bắt buộc: `title`, `description`. `job_type` mặc định `internship`; giá trị hợp lệ: `internship`, `full_time`, `part_time`, `contract`. `deadline` có thể `null`/rỗng hoặc theo `YYYY-MM-DD`. `category_id` có thể bỏ qua hoặc `null`.

Response tạo `201`:

```json
{"message":"Đã tạo tin; tin đang chờ kiểm duyệt.","job_id":12,"status":"pending"}
```

Khi cập nhật `PUT`, các field không gửi sẽ giữ giá trị cũ; tin quay lại `pending` và phải được duyệt lại. `DELETE` đặt status thành `closed`, giữ nguyên đơn ứng tuyển và lịch sử. Không có thao tác xóa cứng tin trong API này.

### 7.3. Ứng viên của doanh nghiệp

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/company/applications` | Business | Liệt kê đơn thuộc tin của mình |
| `GET` | `/api/company/applications/<application_id>` | Business sở hữu tin liên quan | Xem chi tiết đơn và thông tin ứng viên |
| `PATCH` | `/api/company/applications/<application_id>/status` | Business sở hữu tin liên quan | Cập nhật trạng thái tuyển dụng |

Có thể lọc danh sách bằng `GET /api/company/applications?job_id=12`.

Request cập nhật trạng thái:

```json
{"status":"reviewing"}
```

`status` chỉ nhận `reviewing`, `accepted`, hoặc `rejected`. Không thể cập nhật đơn đã `withdrawn`; lỗi trạng thái trả `409`. Response `200`:

```json
{"message":"Đã cập nhật trạng thái đơn ứng tuyển.","status":"reviewing"}
```

## 8. Đơn ứng tuyển của sinh viên — `/api/applications`

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `POST` | `/api/applications/jobs/<job_id>` | Student | Ứng tuyển vào tin hợp lệ |
| `GET` | `/api/applications/me` | Student | Liệt kê đơn của mình |
| `GET` | `/api/applications/<application_id>` | Student sở hữu đơn | Xem một đơn |
| `PUT` | `/api/applications/<application_id>` | Student sở hữu đơn | Sửa lời nhắn khi đơn đang `submitted` |
| `DELETE` | `/api/applications/<application_id>` | Student sở hữu đơn | Rút đơn, không xóa cứng |

Request ứng tuyển:

```json
{"cover_letter":"Tôi mong muốn ứng tuyển vào vị trí này."}
```

Response `201`:

```json
{"message":"Ứng tuyển thành công.","application_id":21}
```

Một sinh viên chỉ được ứng tuyển một lần cho mỗi tin; trùng đơn trả `409`. Tin chưa duyệt, hết hạn hoặc không khả dụng trả `404`.

Request cập nhật đơn:

```json
{"cover_letter":"Đây là lời nhắn đã cập nhật."}
```

Chỉ được sửa khi đơn ở trạng thái `submitted`. `DELETE` chỉ rút đơn khi status là `submitted` hoặc `reviewing`; response `200`:

```json
{"message":"Đã rút đơn ứng tuyển; lịch sử được giữ lại."}
```

## 9. Admin và kiểm duyệt — `/api/admin`

### 9.1. Kiểm duyệt doanh nghiệp và việc làm

Các endpoint này cho `admin` và `moderator` sử dụng.

| Method | Endpoint | Mục đích |
|---|---|---|
| `GET` | `/api/admin/pending/companies` | Danh sách doanh nghiệp chờ duyệt |
| `POST` | `/api/admin/companies/<company_id>/review` | Duyệt/từ chối doanh nghiệp |
| `GET` | `/api/admin/pending/jobs` | Danh sách tin chờ duyệt, thuộc doanh nghiệp đã duyệt |
| `POST` | `/api/admin/jobs/<job_id>/review` | Duyệt/từ chối tin |
| `GET` | `/api/admin/review-histories` | Xem lịch sử kiểm duyệt |

Body duyệt doanh nghiệp:

```json
{"decision":"approved","note":"Thông tin doanh nghiệp hợp lệ."}
```

Body duyệt tin có cùng cấu trúc. `decision` chỉ nhận `approved` hoặc `rejected`; `note` là tùy chọn. Không thể duyệt tin khi hồ sơ doanh nghiệp chưa được duyệt; API trả `409`.

Response thành công `200`:

```json
{"message":"Đã cập nhật kết quả duyệt doanh nghiệp.","status":"approved"}
```

Query lịch sử: `entity_type=company|job`, `entity_id=<id>`. Lịch sử là read-only.

### 9.2. CRUD tài khoản — chỉ Admin

| Method | Endpoint | Mục đích |
|---|---|---|
| `GET` | `/api/admin/users` | Liệt kê tài khoản |
| `POST` | `/api/admin/users` | Tạo tài khoản bất kỳ vai trò |
| `GET` | `/api/admin/users/<user_id>` | Xem chi tiết tài khoản |
| `PUT` | `/api/admin/users/<user_id>` | Sửa role/trạng thái hoạt động |
| `DELETE` | `/api/admin/users/<user_id>` | Vô hiệu hóa tài khoản |

Query list tùy chọn: `role=student|business|moderator|admin`, `is_active=0|1`.

Request tạo:

```json
{"email":"mod@example.com","password":"secret123","role":"moderator"}
```

Với tài khoản business, có thể gửi thêm `company_name`. Request `PUT`:

```json
{"role":"business","is_active":1}
```

`DELETE` là vô hiệu hóa mềm. Admin không được tự hạ quyền hoặc tự khóa tài khoản đang đăng nhập; xung đột trả `409`.

### 9.3. CRUD danh mục việc làm

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/admin/categories` | Admin/Moderator | Liệt kê danh mục |
| `POST` | `/api/admin/categories` | Admin | Tạo danh mục |
| `GET` | `/api/admin/categories/<category_id>` | Admin/Moderator | Xem danh mục |
| `PUT` | `/api/admin/categories/<category_id>` | Admin | Cập nhật danh mục |
| `DELETE` | `/api/admin/categories/<category_id>` | Admin | Xóa danh mục |

Request tạo:

```json
{"name":"Software Development","description":"Các vị trí phát triển phần mềm."}
```

`PUT` hỗ trợ `name`, `description`, `is_active`. Tên danh mục phải có giá trị và duy nhất. Xóa danh mục không xóa tin cũ; tin sẽ không còn liên kết danh mục.

### 9.4. CRUD nội dung hướng nghiệp

Các endpoint quản trị nội dung nằm dưới `/api/admin/career-contents` và cho admin/moderator.

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/admin/career-contents` | Admin/Moderator | Liệt kê mọi nội dung, gồm draft |
| `POST` | `/api/admin/career-contents` | Admin/Moderator | Tạo nội dung |
| `GET` | `/api/admin/career-contents/<content_id>` | Admin/Moderator | Xem một nội dung |
| `PUT` | `/api/admin/career-contents/<content_id>` | Admin/Moderator | Sửa nội dung |
| `DELETE` | `/api/admin/career-contents/<content_id>` | Admin/Moderator | Xóa nội dung |

Request tạo:

```json
{
  "title":"Viết CV cho sinh viên thực tập",
  "summary":"Một số lưu ý khi chuẩn bị CV.",
  "body":"Nội dung bài viết...",
  "category":"CV",
  "status":"draft"
}
```

Bắt buộc: `title`, `body`. `status` là `draft` hoặc `published`, mặc định `draft`.

## 10. Bài viết hướng nghiệp công khai — `/api/career-contents`

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/career-contents` | Public | Liệt kê bài đã xuất bản |
| `GET` | `/api/career-contents/<content_id>` | Public | Xem bài đã xuất bản |

Public API **chỉ** trả nội dung `published`; draft không được trả ra public endpoint. Nội dung quản trị được thao tác ở `/api/admin/career-contents` như mục 9.4.

## 11. Trạng thái và quy tắc chuyển trạng thái

### 11.1. Hồ sơ doanh nghiệp

`pending` → `approved` hoặc `rejected` qua kiểm duyệt. Khi doanh nghiệp sửa hồ sơ, trạng thái trở về `pending`.

### 11.2. Tin tuyển dụng

`pending` → `approved` hoặc `rejected` qua kiểm duyệt. Khi doanh nghiệp sửa tin, tin trở về `pending`. Doanh nghiệp đóng tin bằng `DELETE` → `closed`. Tin phải thuộc doanh nghiệp đã duyệt mới được đưa vào kiểm duyệt/hiển thị công khai.

### 11.3. Đơn ứng tuyển

Trạng thái: `submitted`, `reviewing`, `accepted`, `rejected`, `withdrawn`.

- Sinh viên tạo đơn: `submitted`.
- Doanh nghiệp chuyển trạng thái: `reviewing`, `accepted`, hoặc `rejected`.
- Sinh viên chỉ sửa lời nhắn khi `submitted`.
- Sinh viên chỉ rút đơn khi `submitted` hoặc `reviewing`; rút đơn chuyển sang `withdrawn`.
- Đơn `withdrawn` không được doanh nghiệp cập nhật lại.
- Mỗi cặp `(job_id, student_id)` chỉ có một đơn; không tạo lại đơn trùng kể cả đơn đã rút trong bản MVP hiện tại.

### 11.4. Nội dung hướng nghiệp

`draft` chưa công khai; `published` được trả ra public endpoint. Moderator/admin có thể sửa hoặc xóa nội dung theo quyền của API.

## 12. Contract theo thành viên phụ trách

Bảng này giúp chia việc mà không làm trùng hoặc lệch API.

| Thành viên/module | Phạm vi | Endpoint chính |
|---|---|---|
| **TV1 — Sinh viên** | Hồ sơ, CV, tìm/lọc tin, xem tin, ứng tuyển, theo dõi/rút/sửa đơn | `/api/students/*`, `GET /api/jobs*`, `/api/applications/*`, `GET /api/career-contents*` |
| **TV2 — Doanh nghiệp** | Hồ sơ doanh nghiệp, CRUD tin của mình, danh sách ứng viên, cập nhật trạng thái đơn | `/api/company/*` |
| **TV3 — Core/Admin** | Auth/session, phân quyền, database, kiểm duyệt, user/category/content admin, tích hợp | `/api/auth/*`, `/api/admin/*`, schema và cấu hình app |
| **Chung** | Frontend gọi đúng contract, không truy cập database trực tiếp | Tất cả endpoint liên quan UI của từng module |

### Quy tắc bàn giao giữa thành viên

1. Không đổi endpoint hoặc tên JSON field khi chưa báo nhóm.
2. Mỗi endpoint phải có ít nhất một ca thành công và một ca lỗi được thử bằng Postman.
3. Thành viên phụ trách endpoint cung cấp: file/Blueprint, quyền cần có, body mẫu, response mẫu và kết quả test.
4. Người gọi endpoint không tự xử lý nghiệp vụ thay backend; ví dụ không tự quyết định quyền admin bằng một biến phía trình duyệt.
5. Nếu bổ sung field mới, cập nhật cả schema/database (nếu cần), code backend, contract, frontend và test.

## 13. Smoke-test tối thiểu cho luồng demo

1. Tạo tài khoản business và student.
2. Đăng nhập business, cập nhật hồ sơ; xác nhận trạng thái doanh nghiệp chuyển về `pending`.
3. Admin/moderator duyệt doanh nghiệp `approved`.
4. Business tạo tin; tin ở `pending` và chưa xuất hiện ở `GET /api/jobs`.
5. Admin/moderator duyệt tin `approved`.
6. Student tìm thấy tin và gửi đơn; thử gửi lại lần hai phải nhận `409`.
7. Business xem danh sách ứng viên và chuyển đơn sang `reviewing`, sau đó `accepted` hoặc `rejected`.
8. Student xem `/api/applications/me` và thấy trạng thái đã đổi.
9. Kiểm tra sinh viên A không đọc/xóa CV hoặc đơn của sinh viên B; business A không thao tác tin/đơn của business B.
10. Kiểm tra bài `draft` không xuất hiện ở `GET /api/career-contents`, còn bài `published` có thể đọc công khai.

## 14. Phạm vi và lưu ý

- Đây là contract cho code base hiện tại của nhóm, không phải cam kết một dịch vụ production.
- Cấu hình session cookie phù hợp cho demo local; trước khi deploy thực tế cần cấu hình `SECRET_KEY` an toàn, HTTPS, CSRF protection và biện pháp bảo vệ upload phù hợp.
- Một vài thao tác dùng soft delete/đóng/rút để giữ lịch sử nghiệp vụ; không hiểu `DELETE` là luôn xóa vật lý dữ liệu.
- Nếu code thực tế khác contract sau khi merge, nhóm cần xác định thay đổi nào là chủ đích, cập nhật tài liệu và test trước khi tiếp tục phát triển frontend.
