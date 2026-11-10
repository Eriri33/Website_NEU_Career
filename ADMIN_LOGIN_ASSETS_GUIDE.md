# NEU Career - cập nhật giao diện Admin

## Cập nhật trên project hiện tại (patch)
1. Sao lưu thư mục project.
2. Giải nén `NEU_Career_login_assets_patch.zip`.
3. Copy thư mục `frontend` và file `ADMIN_LOGIN_ASSETS_GUIDE.md` vào thư mục gốc `Website_NEU_Career`.
4. Chọn ghi đè khi Windows hỏi. Patch chỉ thay `frontend/templates/admin/login.html`, thêm CSS/JS đăng nhập và ảnh NEU; không thay API/backend.

## Chạy
Chạy file `run.cmd` tại thư mục gốc hoặc nhấp đúp vào file để khởi động ứng dụng.
Mở `http://127.0.0.1:5000/admin/login`.

## Ghi chú
- Form gọi `POST /api/auth/login` cùng-origin.
- Chỉ role `admin` và `moderator` được vào `/admin/`.
- Ảnh nằm trong `frontend/static/images/neu/`.
- Đây là trang đăng nhập staff; không thay đổi các luồng đăng nhập khác.
