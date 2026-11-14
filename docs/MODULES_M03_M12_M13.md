# Bản đồ module M03, M12, M13

Backend dùng Flask Blueprint và SQLite. Các package nghiệp vụ được nhóm theo mã
module tại `backend/app/modules/`; các endpoint hiện có được giữ nguyên để không
làm hỏng client Career Connect đang sử dụng.

## M03 — Sinh viên và quá trình theo học

| Chức năng | File |
|---|---|
| Hồ sơ tài khoản sinh viên, CV, gợi ý việc làm | `backend/app/students/routes.py` |
| Hồ sơ ứng tuyển, lịch sử và trạng thái đơn | `backend/app/applications/routes.py` |
| Tiếp nhận bàn giao, ghi mã định danh, chương trình/khóa và lần theo học | `backend/app/modules/m03_students/routes.py` |
| Thay đổi trạng thái lần theo học và lưu lịch sử/căn cứ | `backend/app/modules/m03_students/routes.py` |
| Liên kết mã tham chiếu tới điểm, tài chính, hỗ trợ, hồ sơ tốt nghiệp | `backend/app/modules/m03_students/routes.py` |
| Bảng định danh, lần theo học, lịch sử và liên kết hệ thống | `db/module_tables.sql` |

API mới:

- `POST /api/students/intakes` — moderator/admin ghi nhận bàn giao đã kiểm tra
  cho một tài khoản sinh viên đã tồn tại; body gồm `student_user_id`,
  `student_code`, `program_code`, `program_name`, `cohort`, `source_system`,
  `reason` và tùy chọn `effective_from` (`YYYY-MM-DD`).
- `GET /api/students/records/<user_id>` — xem tổng hợp hồ sơ và các liên kết
  (moderator/admin).
- `PATCH /api/students/enrollments/<id>/status` — đổi trạng thái với căn cứ và
  ngày hiệu lực tùy chọn (`effective_at`, `YYYY-MM-DD`); thay đổi được lưu trong
  lịch sử.
- `POST /api/students/records/<user_id>/system-links` — lưu mã tham chiếu từ hệ
  thống điểm, tài chính, hỗ trợ hoặc tốt nghiệp, không sao chép dữ liệu nguồn.

`student_code` là mã do hệ thống có thẩm quyền cấp; ứng dụng không tự tạo quy tắc
hay dãy mã. Mô hình cho phép một người có nhiều lần theo học và nhiều định danh,
nhưng quyết định mã toàn trường hay mã theo chương trình vẫn cần chủ nghiệp vụ
phê duyệt. Hiện intake chỉ nhận tài khoản sinh viên đã được tạo; chưa kết nối hệ
thống tuyển sinh để tự nhận bàn giao. Chưa tích hợp hệ thống điểm/tài chính/tốt
nghiệp: chỉ lưu external ID và tên hệ thống đầu mối.

## M12 — Hỗ trợ người học

| Chức năng | File |
|---|---|
| Tạo, liệt kê yêu cầu; trao đổi; xem lịch sử; phân công, chuyển đơn vị, ưu tiên và trạng thái | `backend/app/modules/m12_support/routes.py` |
| Bảng yêu cầu, trao đổi và nhật ký chuyển trạng thái | `db/module_tables.sql` |
| Xác thực session và giới hạn vai trò staff | `backend/app/auth/guards.py` |

API mới:

- `GET/POST /api/support/tickets` — người đăng nhập xem yêu cầu của mình hoặc
  (staff) danh sách toàn hệ thống; tạo yêu cầu mới.
- `GET /api/support/tickets/<id>` — xem chi tiết, trao đổi và nhật ký; chỉ người
  gửi và moderator/admin được xem.
- `POST /api/support/tickets/<id>/messages` — thêm trao đổi trong phạm vi được
  phép.
- `PATCH /api/support/tickets/<id>` — staff cập nhật trạng thái, mức ưu tiên,
  đơn vị/người xử lý; người gửi chỉ được mở lại yêu cầu đã giải quyết/đóng.

Ticket mặc định không công khai; danh sách của người gửi không lộ ticket của
người khác. Chưa có SLA/thời hạn xử lý vì chưa được thống nhất. Tệp đính kèm và
đồng bộ nhân sự/HR chưa được triển khai. Moderator/admin hiện là nhóm staff mà
ứng dụng có sẵn; chưa có role riêng cho giảng viên/nhân viên.

## M13 — Đối tác doanh nghiệp và thực tập

| Chức năng | File |
|---|---|
| Danh bạ doanh nghiệp đối tác, tìm kiếm, cập nhật, rà trùng, xác minh | `backend/app/modules/m13_partners/routes.py` |
| Đầu mối liên hệ tách khỏi doanh nghiệp, cập nhật và xác minh riêng | `backend/app/modules/m13_partners/routes.py` |
| Bảng đối tác và đầu mối liên hệ | `db/module_tables.sql` |
| Tài khoản doanh nghiệp tuyển dụng, hồ sơ/doanh nghiệp đăng tuyển và tin | `backend/app/companies/routes.py` |
| Quy trình đơn ứng tuyển hiện có | `backend/app/applications/routes.py` |

API đối tác tại `/api/partners` chỉ dành cho moderator/admin:

- `GET/POST /api/partners` — tìm kiếm danh bạ hoặc tạo doanh nghiệp; dữ liệu trùng
  tên/website trả `409` để người nhập kiểm tra.
- `GET/PATCH /api/partners/<id>` — xem/cập nhật doanh nghiệp.
- `POST /api/partners/<id>/contacts` và `PATCH /api/partners/contacts/<id>` —
  quản lý từng người liên hệ riêng.
- `POST /api/partners/<id>/verify` và
  `POST /api/partners/contacts/<id>/verify` — ghi thời điểm xác minh.

Hồ sơ đối tác độc lập với tài khoản doanh nghiệp dùng đăng tuyển. Chưa triển khai
quy trình/hồ sơ thực tập hoặc đánh giá thực tập vì đặc tả chưa được cung cấp.
Con số khoảng 5.000 đối tác mới/năm chưa được dùng làm KPI cho đến khi cách đếm
được thống nhất.

## Các lưu ý triển khai khác

- Đồng bộ thông tin cá nhân giảng viên từ HR: chưa có hệ thống nguồn, giao thức,
  trường dữ liệu hay quy tắc xung đột; chưa tự tạo tích hợp giả.
- Thông báo lịch học/học phí và nhắc hạn: chưa có module lịch học/học phí, kênh
  gửi hay quy tắc nhận thông báo.
- Khảo sát/đánh giá: chưa có đặc tả biểu mẫu, phân quyền, ẩn danh và thời điểm
  mở/đóng khảo sát. Chưa tạo cơ chế đánh giá giảng viên để tránh phát sinh dữ
  liệu nhạy cảm sai quy trình.
- Kiểm thử API module mới: `python -m unittest tests.test_new_modules -v`.
