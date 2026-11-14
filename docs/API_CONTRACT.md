# CAREER CONNECT — API CONTRACT

**Phiên bản:** 2.0 (target contract cho triển khai frontend + backend)  
**Mục đích:** Quy ước giao tiếp thống nhất giữa frontend và backend, đồng thời là hợp đồng làm việc giữa các thành viên.  
**Backend:** Flask + SQLite  
**Base URL khi chạy local:** `http://127.0.0.1:5000`  
**API prefix:** `/api`

> **Đây là contract mục tiêu.** Một phần endpoint đã có trong starter, một phần là yêu cầu bổ sung chưa được code. Dùng `README.md` mục “Kiểm kê code starter” để xem trạng thái. AI/thành viên phải kiểm tra code thực tế, triển khai các mục thiếu và viết test; không được giả định ghi trong tài liệu = đã chạy.
>
> Frontend phải dùng đúng endpoint, HTTP method, tên field và trạng thái trong tài liệu này. Nếu nhóm thay đổi contract, cập nhật tài liệu + code + test trong cùng một commit.

Tài liệu bổ sung: [`SEARCH_UI_SPEC.md`](SEARCH_UI_SPEC.md) quy định hành vi UI; [`AI_IMPLEMENTATION_BRIEF.md`](AI_IMPLEMENTATION_BRIEF.md) quy định trình tự triển khai và các nguyên tắc không được vi phạm.

## 1. Quy ước chung

### 1.1. Request và response

- Request/response dữ liệu thông thường dùng JSON với header `Content-Type: application/json`.
- Tải CV sử dụng `multipart/form-data`, tên field file bắt buộc là `file`.
- `GET` dùng để đọc; `POST` để tạo hoặc thực hiện hành động; `PUT` để cập nhật; `PATCH` để cập nhật một phần/trạng thái; `DELETE` để xóa mềm/đóng/rút theo quy tắc nghiệp vụ.
- ID trong URL là số nguyên, ví dụ `/api/jobs/12`.
- Ngày deadline dùng định dạng `YYYY-MM-DD`, ví dụ `2026-12-31`.
- Response danh sách là JSON array `[...]`; response chi tiết là JSON object `{...}`.
- Bản MVP ưu tiên bộ lọc chính xác trước; phân trang có thể bổ sung sau. Các list endpoint hiện trả JSON array để tương thích starter.
- Query filters có thể kết hợp với nhau: áp dụng AND giữa các nhóm filter; nếu chọn nhiều danh mục, tin khớp ít nhất một danh mục được giữ lại (OR trong nhóm category).
- Chuỗi tìm kiếm nên trim khoảng trắng, không phân biệt hoa/thường; dùng parameterized SQL, không nối input trực tiếp vào SQL.
- Guest (chưa đăng nhập) dùng được các endpoint public. Không yêu cầu đăng nhập chỉ để tìm kiếm/xem tin.

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

Tất cả endpoint trong phần này là **Public** (guest, student và các role khác đều có thể đọc dữ liệu công khai).

| Method | Endpoint | Mục đích | Trạng thái starter |
|---|---|---|---|
| `GET` | `/api/jobs` | Danh sách/tìm kiếm/lọc tin đã duyệt | Đã có filter cơ bản; phải mở rộng các filter v2 dưới đây |
| `GET` | `/api/jobs/<job_id>` | Chi tiết tin đã duyệt | Đã có |
| `GET` | `/api/jobs/categories` | Danh mục đang hoạt động + số tin công khai trong từng danh mục | Cần bổ sung |
| `GET` | `/api/jobs/suggestions` | Từ khóa gợi ý và các tin đề xuất cho dropdown thanh tìm kiếm | Cần bổ sung |

### 6.1. Query filters của `GET /api/jobs`

| Tham số | Kiểu | Ý nghĩa |
|---|---|---|
| `q` | string | Từ khóa tìm trong tiêu đề tin, mô tả và tên doanh nghiệp |
| `location` | string | Tìm địa điểm theo chuỗi, không phân biệt hoa/thường |
| `category_id` | integer | Lọc một danh mục; giữ tương thích với starter |
| `category_ids` | string | Nhiều ID phân cách dấu phẩy, ví dụ `category_ids=1,3,4`; dùng cho checkbox nhiều danh mục |
| `job_type` | enum | `internship`, `full_time`, `part_time`, `contract` |
| `major` | string | Lọc ngành học phù hợp; tin có `major_required` rỗng vẫn có thể xuất hiện |
| `skills` | string | Lọc theo kỹ năng yêu cầu trong tin |
| `saturday_policy` | enum | `off`, `working`, `negotiable`, `unknown`; `off` nghĩa là nghỉ thứ Bảy, `working` nghĩa là làm thứ Bảy |
| `posted_within` | integer | Tin đăng trong `1`, `3`, `7` hoặc `30` ngày gần nhất |
| `sort` | enum | `latest` (mặc định), `relevance` (khi có q), `deadline_soon` |

Ví dụ sử dụng kết hợp: `GET /api/jobs?q=python&location=Ha%20Noi&job_type=internship&category_ids=1,3&saturday_policy=off&posted_within=7&sort=latest`.

**Ghi chú triển khai:** starter hiện hỗ trợ `q`, `major`, `location`, `job_type`, `category_id`. `category_ids`, `skills`, `saturday_policy`, `posted_within`, `sort`, public categories và suggestions là phần cần bổ sung. `saturday_policy` phải được lưu ở `jobs`; thêm migration an toàn để database cũ có thể cập nhật mà không làm mất dữ liệu.

### 6.2. Trường cần có trên card kết quả

`id`, `title`, `description` (có thể rút gọn), `location`, `job_type`, `major_required`, `skills_required`, `deadline`, `created_at`, `category_id`, `category_name`, `company_name`, `salary_text`, `saturday_policy`.

`salary_text` có thể là “Thỏa thuận”, “Từ 30 triệu” hoặc chuỗi do doanh nghiệp nhập. Nếu chưa có dữ liệu, hiển thị “Chưa cập nhật”; không bịa mức lương. `salary_text` là field bổ sung cần thêm vào schema, form tạo/sửa tin và response.

### 6.3. Public categories — `GET /api/jobs/categories`

Chỉ trả danh mục `is_active=1`. Mỗi item gồm `id`, `name`, `description`, `job_count`, trong đó `job_count` chỉ đếm tin đang `approved`, công ty `approved` và active, deadline còn hạn. Ví dụ:

```json
[{"id":1,"name":"Marketing","description":"","job_count":15}]
```

### 6.4. Search dropdown — `GET /api/jobs/suggestions`

Query tùy chọn: `q`, `location`, `category_ids`. Response:

```json
{
  "popular_keywords": ["thực tập sinh", "Python", "Marketing", "Kế toán", "Business Analyst"],
  "suggested_jobs": [
    {"id":12,"title":"Python Intern","company_name":"ABC Technology","location":"Hà Nội","salary_text":"Thỏa thuận"}
  ]
}
```

Ở MVP, `popular_keywords` được lấy từ danh sách từ khóa seed/curated; không gọi đó là thống kê thời gian thực nếu chưa lưu search logs. `suggested_jobs` phải là tin public hợp lệ. Với Guest, ưu tiên tin mới; với Student đã đăng nhập, frontend có thể tải `/api/students/me/recommendations` để thay danh sách gợi ý bằng việc phù hợp hồ sơ.

### 6.5. Quy tắc dữ liệu public

Chỉ trả tin `approved`, thuộc doanh nghiệp `approved`, tài khoản doanh nghiệp đang hoạt động, tin chưa đóng và deadline chưa qua. Các filter bổ sung không được làm lộ tin pending/rejected/closed hoặc hồ sơ doanh nghiệp chưa duyệt. Tin không công khai trả `404` khi gọi chi tiết.

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

`GET /api/company/jobs` nhận query tùy chọn: `q` (tiêu đề/mô tả), `status=pending|approved|rejected|closed`, `category_id`, `location`, `job_type`, `sort=latest|deadline_soon`. Mặc định trả mọi trạng thái thuộc doanh nghiệp hiện tại; bộ lọc không được phép trả tin của doanh nghiệp khác.

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

Có thể lọc danh sách bằng:

- `job_id`: chỉ đơn thuộc một tin nhất định.
- `status=submitted|reviewing|accepted|rejected|withdrawn`.
- `q`: tìm tên sinh viên, email, ngành học hoặc kỹ năng.
- `sort=latest|oldest` theo ngày ứng tuyển.

Ví dụ: `GET /api/company/applications?job_id=12&status=reviewing&q=python`.

**Starter hiện chỉ lọc `job_id`;** `q`, `status` và `sort` là phần bắt buộc bổ sung. Kết quả phải giới hạn theo `c.user_id = session['user_id']` trước khi áp dụng filter.

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

Query tùy chọn của `GET /api/applications/me`:

- `q`: tìm trong tiêu đề tin hoặc tên doanh nghiệp.
- `status=submitted|reviewing|accepted|rejected|withdrawn`.
- `sort=latest|oldest`.

Starter hiện trả toàn bộ đơn của student; `q`, `status` và `sort` là phần cần bổ sung để trang lịch sử có thể tìm/lọc.

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

### 9.0. Dữ liệu tổng quan Dashboard

`GET /api/admin/dashboard/summary` cho cả `admin` và `moderator` sử dụng. Endpoint trả số liệu tổng hợp lấy trực tiếp từ SQLite, không trả danh sách tài khoản/đơn cá nhân.

Response `200` có cấu trúc:

```json
{
  "role": "admin",
  "stats": {
    "active_users": 12,
    "active_students": 8,
    "active_business_accounts": 3,
    "companies_total": 3,
    "companies_approved": 2,
    "companies_pending": 1,
    "jobs_total": 7,
    "jobs_approved": 4,
    "jobs_pending": 1,
    "applications_total": 9,
    "applications_pending": 5,
    "categories_total": 6,
    "categories_active": 5,
    "contents_total": 4,
    "contents_published": 3,
    "contents_draft": 1,
    "reviews_today": 2
  },
  "recent_reviews": [
    {
      "id": 8,
      "entity_type": "job",
      "entity_id": 12,
      "action": "approved",
      "note": "Nội dung hợp lệ.",
      "created_at": "2026-10-31 09:30:00",
      "reviewer_email": "moderator@example.com",
      "entity_name": "Python Intern"
    }
  ]
}
```

Các số liệu JSON trên chỉ minh họa cấu trúc, không phải dữ liệu cố định. `jobs_approved` chỉ đếm tin đang được công khai: tin đã duyệt, doanh nghiệp đã duyệt, tài khoản doanh nghiệp đang hoạt động và tin chưa hết hạn. `recent_reviews` trả tối đa 8 quyết định kiểm duyệt mới nhất. Các vai trò không phải Admin vẫn được xem số liệu tổng hợp, nhưng giao diện Moderator không hiển thị mục quản lý tài khoản.

### 9.1. Kiểm duyệt doanh nghiệp và việc làm

Các endpoint này cho `admin` và `moderator` sử dụng.

Để staff không phải duyệt một danh sách dài không thể tìm kiếm, bổ sung các query filters và list endpoints dưới đây:

- `GET /api/admin/pending/companies?q=&sort=oldest|newest`: `q` tìm tên doanh nghiệp/email.
- `GET /api/admin/pending/jobs?q=&category_id=&location=&job_type=&sort=oldest|newest`: tìm tiêu đề/mô tả/tên doanh nghiệp và lọc danh mục, địa điểm, loại việc.
- `GET /api/admin/companies?q=&approval_status=pending|approved|rejected`: danh sách quản trị doanh nghiệp theo trạng thái (admin/moderator).
- `GET /api/admin/jobs?q=&status=pending|approved|rejected|closed&category_id=&location=&job_type=&company_id=`: tìm/lọc tin ở mọi trạng thái (admin/moderator).

Hai endpoint danh sách tất cả `/companies` và `/jobs` là **yêu cầu bổ sung**; các endpoint `pending/*` hiện có cần được thêm query filters. Bộ lọc không được thay thế kiểm tra role.

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

Query list tùy chọn: `q`, `role=student|business|moderator|admin`, `is_active=0|1`. `q` tìm email, tên sinh viên hoặc tên doanh nghiệp liên quan. Starter hiện có `role` và `is_active`; `q` là phần cần bổ sung.

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

`GET /api/admin/categories` nhận query tùy chọn `q` (tên danh mục), `is_active=0|1`; staff cần tìm nhanh danh mục trên màn quản lý. Starter hiện trả toàn bộ danh mục, chưa có query filters.

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

`GET /api/admin/career-contents` nhận query `q` (title/summary/body), `category`, `status=draft|published`; starter hiện trả mọi nội dung chưa lọc, cần bổ sung filters.

## 10. Bài viết hướng nghiệp công khai — `/api/career-contents`

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| `GET` | `/api/career-contents` | Public | Liệt kê bài đã xuất bản |
| `GET` | `/api/career-contents/<content_id>` | Public | Xem bài đã xuất bản |

Public API **chỉ** trả nội dung `published`; draft không được trả ra public endpoint. `GET /api/career-contents` nhận query tùy chọn `q` (title/summary/body) và `category` để trang hướng nghiệp tìm/lọc bài. Nội dung quản trị được thao tác ở `/api/admin/career-contents` như mục 9.4. Public search tuyệt đối không được lộ draft.

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
| **TV1 — Public Discovery + Student** | Guest/student search UI, danh mục/keyword suggestions, hồ sơ/CV, tìm và xem tin, apply/tracking, public career content | `/api/jobs*`, `/api/students/*`, `/api/applications/*`, `GET /api/career-contents*` |
| **TV2 — Business Recruitment** | Hồ sơ doanh nghiệp, CRUD tin của mình, tìm/lọc tin, tìm/lọc ứng viên, cập nhật trạng thái đơn | `/api/company/*` |
| **TV3 — Platform + Staff/Admin** | Auth/session, phân quyền, schema/migration/seed, search/filter kiểm duyệt, user/category/content admin, tích hợp | `/api/auth/*`, `/api/admin/*`, schema và cấu hình app |
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
11. Test search public: kết hợp keyword + location + category + job type; thử không có kết quả, clear filters và danh mục có `job_count` đúng.
12. Test gợi ý: keyword chọn từ dropdown đưa đúng từ khóa vào ô search; suggested jobs đều là tin public hợp lệ.
13. Test business: lọc tin theo status và ứng viên theo query/status nhưng không thấy dữ liệu business khác.
14. Test admin/moderator: lọc hàng chờ theo keyword; admin tìm user theo q/role/active; lọc bài theo category/status.

## 14. Các field/schema bổ sung để đáp ứng bộ lọc v2

`db/schema.sql` hiện **chưa có** dữ liệu lịch làm việc thứ Bảy và trường lương hiển thị. Cần bổ sung tối thiểu:

- `jobs.saturday_policy TEXT NOT NULL DEFAULT 'unknown' CHECK (saturday_policy IN ('off','working','negotiable','unknown'))`.
- `jobs.salary_text TEXT NOT NULL DEFAULT 'Thỏa thuận'`.

Cập nhật đồng bộ form tạo/sửa tin, insert/update SQL và response của public/business/admin job list. Khi có database cũ, thêm migration idempotent kiểm tra cột tồn tại trước khi `ALTER TABLE`; không xóa database hoặc mất dữ liệu thành viên để thêm cột. Có thể thêm dữ liệu sample cho các chính sách thứ Bảy khác nhau để kiểm thử filter.

MVP không bắt buộc lọc lương số học; `salary_text` dùng để hiển thị. Nếu sau này muốn lọc theo mức lương, cần thêm numeric salary range có đơn vị rõ ràng và cập nhật contract trước.

## 15. Phân định trạng thái triển khai

Các phần dưới đây là **yêu cầu cần code**, không phải khẳng định starter đã có:

1. `GET /api/jobs/categories` và `GET /api/jobs/suggestions`.
2. Search v2: `category_ids`, `skills`, `saturday_policy`, `posted_within`, `sort`.
3. Search/filter cho company jobs, company applications và student applications.
4. Search/filter cho pending companies/jobs; endpoint quản trị danh sách tất cả companies/jobs.
5. Query `q` cho admin users/categories/career contents và public career content.
6. Giao diện search theo `docs/SEARCH_UI_SPEC.md` và màn CRUD theo từng role.
7. Unit/API tests cho từng filter, kết hợp filters và giới hạn quyền sở hữu.

Các filter cơ bản `q`, `major`, `location`, `job_type`, `category_id` của `GET /api/jobs` đã có trong starter hiện tại; cần kiểm tra code sau merge trước khi kết luận trạng thái trên branch chung.

## 16. Quy tắc khi dùng AI để triển khai

- Đọc `README.md`, `docs/API_CONTRACT.md`, `docs/SEARCH_UI_SPEC.md`, schema và toàn bộ route liên quan trước khi sửa.
- Giữ Flask Blueprint/session hiện tại; không tự chuyển sang React, JWT hoặc framework mới nếu nhóm chưa yêu cầu.
- Không tạo fake search result trong JavaScript để giả vờ filter hoạt động. UI phải gửi query param đến API thật.
- Không tự đổi tên endpoint/JSON fields; nếu cần đổi, hãy chỉ rõ tất cả nơi phải cập nhật.
- Mỗi tính năng mới phải cập nhật schema/migration (nếu cần), backend, frontend, contract và tests.
- Chạy test thực tế trước khi báo hoàn thành; báo rõ lệnh nào đã/chưa chạy.
- Không dùng `git push --force`, không xóa database có dữ liệu nhóm và không đưa credentials/upload CV lên GitHub.

## 17. Phạm vi bảo mật

- Đây là contract cho MVP/demo, không phải production guarantee.
- Trước khi deploy thực tế cần đặt `SECRET_KEY` ổn định, ngẫu nhiên và dùng chung giữa các worker, bật HTTPS, CSRF protection và bảo vệ file upload. Nếu không đặt biến này, ứng dụng tạo khóa tạm thời theo tiến trình; phiên đăng nhập sẽ hết hiệu lực khi khởi động lại ứng dụng.
- Backend phải lấy user ID/role từ session, không tin role gửi từ frontend.
- Các thao tác đóng tin/rút đơn/vô hiệu hóa tài khoản giữ lịch sử; không diễn giải `DELETE` là luôn xóa vật lý.
- Các search endpoint quản trị phải áp dụng role guard **trước** khi truy vấn; business search phải giới hạn ownership **trước** khi filter.
