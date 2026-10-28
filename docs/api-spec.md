# Career Connect API — API contract

Base URL local: `http://127.0.0.1:5000`. JSON endpoints use `Content-Type: application/json`, except CV upload (`multipart/form-data`). Authentication uses Flask session cookies: log in first and reuse the cookie jar in Postman.

## Auth — `/api/auth`
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/register` | Create student/business account |
| POST | `/login` | Sign in and set session |
| POST | `/logout` | Sign out |
| GET | `/me` | Read current account |
| PUT | `/me` | Update current account email |
| PUT | `/password` | Change password |
| DELETE | `/me` | Deactivate own account (soft delete) |

Register body: `{"email":"student@example.com","password":"secret123","role":"student"}`. Self-registration only permits `student` and `business`; staff roles are created by an admin.

## Student — `/api/students`
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/me` | Read own profile |
| PUT | `/me` | Update own profile |
| GET | `/me/recommendations` | Rule-based job recommendations |
| GET | `/me/cvs` | List own CVs |
| POST | `/me/cvs` | Create/upload CV; `multipart/form-data`, field `file` |
| GET | `/me/cvs/<cv_id>` | Read metadata for one CV |
| GET | `/me/cvs/<cv_id>/download` | Download own CV |
| PUT | `/me/cvs/<cv_id>` | Replace an existing CV; `multipart/form-data`, field `file` |
| DELETE | `/me/cvs/<cv_id>` | Delete own CV record and file |

Profile example: `{"full_name":"Nguyen Van A","major":"Information Systems","skills":"Python, SQL","phone":"0900000000","bio":"..."}`. CV file type: PDF/DOC/DOCX; size limit: 5 MB.

## Public jobs — `/api/jobs`
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | List approved jobs; supports `q`, `major`, `location`, `job_type`, `category_id` |
| GET | `/<job_id>` | Read one approved job |

Only approved jobs belonging to approved, active companies and not past deadline are public.

## Company — `/api/company`
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/profile` | Read own company profile |
| PUT | `/profile` | Update own profile; resets review to pending |
| GET | `/jobs` | List own jobs |
| POST | `/jobs` | Create job (starts as pending) |
| GET | `/jobs/<job_id>` | Read own job |
| PUT | `/jobs/<job_id>` | Update own job; resubmits for review |
| DELETE | `/jobs/<job_id>` | Close own job instead of hard delete |
| GET | `/applications` | List applications for own jobs; optional `?job_id=1` |
| GET | `/applications/<application_id>` | Read applicant info for an owned job |
| PATCH | `/applications/<application_id>/status` | Set `reviewing`, `accepted`, or `rejected` |

Create job example: `{"title":"Python Intern","description":"...","location":"Ha Noi","job_type":"internship","major_required":"IT","skills_required":"Python, SQL","deadline":"2026-12-31","category_id":1}`. `job_type`: `internship`, `full_time`, `part_time`, `contract`.

Status update example: `{"status":"reviewing"}`. The backend checks company ownership for all company job/application operations.

## Applications — `/api/applications`
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/jobs/<job_id>` | Apply for approved job |
| GET | `/me` | List own applications |
| GET | `/<application_id>` | Read own application |
| PUT | `/<application_id>` | Edit cover letter while status is `submitted` |
| DELETE | `/<application_id>` | Withdraw application; history is retained |

An application cannot be submitted twice to the same job. `DELETE` changes status to `withdrawn`, it does not hard-delete the row.

## Admin and moderation — `/api/admin`
### Moderation
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/pending/companies` | List companies waiting for review |
| POST | `/companies/<company_id>/review` | Approve/reject a company |
| GET | `/pending/jobs` | List jobs waiting for review |
| POST | `/jobs/<job_id>/review` | Approve/reject a job |
| GET | `/review-histories` | Read-only audit history; optional `entity_type=company|job`, `entity_id=1` |

Review body: `{"decision":"approved","note":"Thông tin hợp lệ"}`. A company must be approved before its job can be approved.

### User CRUD (admin role only)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/users` | List users; optional `role`, `is_active=0|1` |
| POST | `/users` | Create user including staff roles |
| GET | `/users/<user_id>` | Read a user |
| PUT | `/users/<user_id>` | Update `role` and/or `is_active` |
| DELETE | `/users/<user_id>` | Deactivate account (soft delete) |

User creation body: `{"email":"mod@example.com","password":"secret123","role":"moderator"}`. An administrator cannot disable or downgrade their own active admin account.

### Job-category CRUD
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/categories` | List categories (admin/moderator) |
| POST | `/categories` | Create category (admin) |
| GET | `/categories/<id>` | Read category (admin/moderator) |
| PUT | `/categories/<id>` | Update category (admin) |
| DELETE | `/categories/<id>` | Delete category (admin); existing jobs remain without a category |

Category example: `{"name":"Software Development","description":"Software engineering roles"}`.

### Career-content CRUD
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/career-contents` | List all content (admin/moderator) |
| POST | `/career-contents` | Create content |
| GET | `/career-contents/<id>` | Read content |
| PUT | `/career-contents/<id>` | Update content |
| DELETE | `/career-contents/<id>` | Delete content |

Content example: `{"title":"Viết CV cho thực tập sinh","summary":"Một số lưu ý","body":"Nội dung bài viết...","category":"CV","status":"draft"}`. Public readers use `GET /api/career-contents` and only see published content.

## Database tables
`users`, `student_profiles`, `student_cvs`, `companies`, `job_categories`, `jobs`, `applications`, `career_contents`, `review_histories`.

## Common status codes
- `200`: success
- `201`: created
- `400`: invalid input
- `401`: not logged in
- `403`: wrong role or operation not allowed yet
- `404`: not found or not visible
- `409`: duplicate or invalid state transition

## Business rules
- Do not trust a user ID/role sent by frontend; read it from the authenticated session.
- Students can access only their own profile, CVs, and applications.
- A business can access only its own profile/jobs/applications.
- Only approved companies can submit jobs; jobs begin in `pending` state.
- Editing a job resubmits it for moderation.
- Application rows and review histories are retained. Withdraw/deactivate/close rather than deleting business history.
- Review history is intentionally read-only to preserve audit integrity.


## Quy ước CRUD cho tài nguyên nghiệp vụ
- **Hồ sơ sinh viên/doanh nghiệp:** được tạo tự động khi đăng ký tài khoản; chủ tài khoản xem và cập nhật hồ sơ của mình. Không xóa riêng hồ sơ vì hồ sơ gắn với tài khoản; dùng `DELETE /api/auth/me` để vô hiệu hóa tài khoản và giữ lịch sử.
- **CV:** CRUD đầy đủ; `PUT /api/students/me/cvs/<cv_id>` thay file cũ bằng file mới. Chỉ chủ CV được xem/tải/sửa/xóa.
- **Tin tuyển dụng:** doanh nghiệp tạo/xem/sửa/đóng tin của mình. `DELETE` đóng tin thay vì xóa cứng để giữ đơn ứng tuyển và lịch sử duyệt.
- **Đơn ứng tuyển:** sinh viên tạo/xem/sửa lời nhắn/rút đơn; doanh nghiệp xem đơn thuộc tin của mình và cập nhật trạng thái. Không xóa cứng.
- **Tài khoản:** admin tạo/xem/cập nhật vai trò-trạng thái/vô hiệu hóa. Người dùng tự cập nhật email/mật khẩu hoặc vô hiệu hóa tài khoản của mình.
- **Nội dung hướng nghiệp và danh mục:** staff quản lý nội dung theo quyền; lịch sử kiểm duyệt chỉ đọc để bảo toàn audit trail.
