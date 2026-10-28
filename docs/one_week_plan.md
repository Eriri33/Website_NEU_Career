# Kế hoạch 1 tuần — Career Connect

## Luồng nghiệp vụ MVP
Doanh nghiệp đăng ký → admin/moderator duyệt doanh nghiệp → doanh nghiệp tạo tin → admin/moderator duyệt tin → sinh viên tìm kiếm và ứng tuyển → doanh nghiệp cập nhật trạng thái → sinh viên xem kết quả.

## Phân công
### Người 1 — Sinh viên
- CRUD phù hợp cho hồ sơ sinh viên; quản lý CV (tải lên, xem danh sách, tải xuống, xóa).
- Tìm kiếm/lọc/chi tiết tin; gợi ý việc làm theo ngành/kỹ năng (nếu kịp).
- Tạo, xem, sửa lời nhắn và rút đơn ứng tuyển; theo dõi trạng thái.
- UI, kiểm thử quyền dữ liệu của sinh viên.

### Người 2 — Doanh nghiệp và tuyển dụng
- Xem/cập nhật hồ sơ doanh nghiệp.
- CRUD tin tuyển dụng: tạo, xem, cập nhật, đóng tin; kiểm tra quyền sở hữu.
- Xem ứng viên của các tin thuộc doanh nghiệp; cập nhật trạng thái đơn.
- UI và kiểm thử dữ liệu doanh nghiệp.

### Người 3 — Nền tảng, Admin, kiểm duyệt
- Flask app, SQLite, schema, Git và API contract.
- Đăng ký/đăng nhập/đăng xuất/đổi email/đổi mật khẩu/vô hiệu hóa tài khoản; phân quyền.
- Duyệt doanh nghiệp/tin và lưu lịch sử duyệt.
- CRUD quản trị tài khoản, danh mục tin và bài viết hướng nghiệp.
- Tích hợp, Postman, dữ liệu demo và hướng dẫn chạy.

## Lịch
- Ngày 1: Chốt schema/API, tạo repo; chạy được app và init-db.
- Ngày 2: Auth/role; các thành viên bắt đầu module.
- Ngày 3: Profile, job CRUD, admin moderation/category/content CRUD.
- Ngày 4: Applications CRUD theo quy tắc; tích hợp các module.
- Ngày 5: Luồng nghiệp vụ end-to-end phải chạy.
- Ngày 6: Kiểm thử phân quyền, trường hợp sai, sửa lỗi.
- Ngày 7: Đóng băng code, demo, tài liệu và báo cáo.

## Quyết định thiết kế
- CRUD đầy đủ ở những thực thể phù hợp.
- Với tin tuyển dụng, thao tác DELETE thực chất đóng tin để lưu lịch sử.
- Với đơn ứng tuyển, DELETE thực chất rút đơn; không xóa cứng.
- Với tài khoản, DELETE là vô hiệu hóa; lịch sử đơn/duyệt vẫn được giữ.
- Lịch sử duyệt chỉ có Read, không có Update/Delete nhằm giữ tính toàn vẹn audit.
- Không làm chatbot AI, email tự động, phỏng vấn video, thanh toán hoặc giao diện phức tạp trong MVP.
