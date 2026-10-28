# AI IMPLEMENTATION BRIEF — READ BEFORE CODING

Bạn đang làm tiếp dự án nhóm Career Connect, Flask + SQLite + Jinja/HTML/CSS/Bootstrap + JavaScript fetch(). Đây là dự án có code starter, không phải tạo lại từ đầu.

## Tài liệu cần đọc
1. `README.md` — mục tiêu, module, vai trò, thứ tự ưu tiên và audit hiện trạng.
2. `docs/API_CONTRACT.md` — contract mục tiêu: endpoints, parameters, fields, permission, statuses.
3. `docs/SEARCH_UI_SPEC.md` — hành vi giao diện tìm kiếm/lọc theo ảnh mẫu.
4. `db/schema.sql`, `app/__init__.py`, `app/*/routes.py`, `app/auth/guards.py`, `tests/test_api.py` — code thực tế trước khi sửa.

## Thứ tự thực hiện
1. Kiểm tra code thực tế và liệt kê file/endpoint hiện có; không đoán.
2. Thực hiện P0 trước: public search + real filters + job details; company job CRUD and applicant management; student apply/tracking; moderation workflow; search/filter trên từng list view.
3. Bổ sung public categories, suggestions, Saturday policy, posting date filters, salary display, search/filter query params theo contract.
4. Xây frontend thật gọi API, có loading/empty/error states. Không fake results, không render hardcoded job cards thay cho API.
5. Cập nhật schema + migration an toàn + routes + UI + contract + tests đồng bộ.
6. Chạy test trên môi trường hiện có. Báo lại test nào thực sự chạy được, không tuyên bố đã chạy nếu chưa chạy.

## Nguyên tắc không được vi phạm
- Giữ Flask Blueprint và session cookie trừ khi được yêu cầu đổi kiến trúc.
- Không cho tự đăng ký admin/moderator.
- Backend là nơi quyết định role và ownership; không tin user_id/role/company_id do frontend gửi.
- Business chỉ thấy tin/đơn của mình; student chỉ thấy hồ sơ/CV/đơn của mình.
- Public job search chỉ trả job đã approved, công ty approved + active, chưa đóng và chưa quá deadline.
- Khi sửa tin đã duyệt, status trở về pending.
- Xóa tin = close; xóa đơn = withdraw; xóa tài khoản = deactivate để giữ lịch sử.
- Dùng parameterized SQL; không nối query string trực tiếp vào SQL.
- Nếu thêm cột, migration phải idempotent và không xóa dữ liệu database sẵn có.
- Các filter phải thật sự truyền từ UI đến query parameters rồi được BE áp dụng.
- Chỉ dùng Bootstrap/plain JS như stack mặc định; không thêm React/Next.js/package lớn nếu không cần.

## Bàn giao khi hoàn thành
- Liệt kê endpoint mới/đã sửa.
- Nêu file đã sửa.
- Đưa lệnh cài đặt/run/test chính xác.
- Đưa bộ test search/filter và quyền sở hữu.
- Ghi rõ các hạng mục chưa làm; không dùng “đã hoàn tất” nếu mới có UI hoặc mới có API một phía.
